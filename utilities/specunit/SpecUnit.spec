#! Package specunit
#! The SpecUnit test runner — a Spec program that tests Spec programs.
#! It is NOT the compiler and has no compiler test mode: it invokes the
#! spec compiler as a command (one compile thread per test), executes
#! each produced binary under a timeout, records the verdict, and
#! deletes the compiled test (see KNOWLEDGE-SPECDEV.md §4a).
#!
#! CLI:
#!   specunit -s ./bin/spec -t tests/
#!   -s  the spec compiler executable (default: <root>/bin/spec)
#!   -t  a test directory, relative to the root; repeat the flag or
#!       separate entries with commas. Scanned recursively (dot
#!       directories skipped).
#!
#! Classification — every candidate .spec file declares itself by its
#! `#!` banner; unmarked files that mention the specunit package are
#! suites, everything else is a helper or a standalone program and is
#! skipped:
#!   #! specunit: suite      compile, run, exit 0 and no [FAIL] required
#!   #! specunit: negative   compilation MUST fail; every
#!                           `#! expect: <text>` must appear in the
#!                           diagnostics
#!   #! specunit: run-fail   compile must succeed, the run MUST exit
#!                           non-zero, every expect must appear in the
#!                           run output
#!   #! specunit: helper     skip (multi-file fixture partners)
#!
#! Architecture:
#! - SpecTestRegistry: the held state — the work queue and the results.
#!   Held arrays and maps are mutex-protected, so the Parallel wave
#!   reads the queue and records results from every worker thread
#!   safely.
#! - SpecUnit: the entry program. Scans the -t trees, dispatches the
#!   compile+execute wave across Parallel:run workers (threads =
#!   cores - 2), and prints the summary when all tests are done.
#!
#! Report ordering: results appear in queue order. dirList order is the
#! filesystem's; a Spec-level ordering primitive (String:compare over
#! the Buf floor) is a tracked follow-up.

Class is SuiteResult{
	namespace: ['specunit'];

	String is name;
	Boolean is passed: true;
	String is note: '';
	String is report: '';

	replace Function is init(String is suiteName){
		self:name: suiteName;
	}
}

Class is WorkItem{
	namespace: ['specunit'];

	String is path;
	String is kind;
	Array of String is expect: [];
	Boolean is requireReport: false;

	replace Function is init(String is itemPath, String is itemKind, Array of String is itemExpect, Boolean is itemRequireReport){
		self:path: itemPath;
		self:kind: itemKind;
		self:expect: itemExpect;
		self:requireReport: itemRequireReport;
	}
}

## The held registry: the work queue and the results. Held arrays and
## maps are mutex-protected — the Parallel wave reads the queue and
## records results from every worker thread safely.
Class is SpecTestRegistry{
	namespace: ['specunit'];

	held Array of WorkItem is queue: [];
	held Array of SuiteResult is results: [];
	held Map of String to SuiteResult is byName: Map:init();

	held Function is addResult(String is name, Boolean is passed, String is note, String is report){
		local SuiteResult is r: SuiteResult:init(suiteName: name);
		r:passed: passed;
		r:note: note;
		r:report: report;
		SpecTestRegistry:results:add(item: r);
		SpecTestRegistry:byName:set(key: name, value: r);
	}
}

Class is SpecUnit{
	namespace: ['specunit'];

	replace Array of Array of String is using: [
		# The plain form grants construction (the report's locals), the
		# as-form grants the bare call surface (the overloads pattern).
		['base', 'sys', Output],
		['base', 'sys', as Output()],
		['base', 'sys', Conditional],
		['base', 'sys', as Conditional()],
		['base', 'sys', Loops],
		['base', 'sys', as Loops()],
		['base', 'sys', Process],
		['base', 'sys', as Process()],
		['base', 'sys', Ansi],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Parallel()],
		['base', 'sys', as Dir()],
		['base', 'sys', as File()]
	];

	replace Function is init(Map of String to String is args){
		local String is specBin: args:getString(key: 's', default: args:getString(key: 'spec', default: '.'));
		Conditional:if(check: { specBin == '.' }, then: {
			specBin: 'bin/spec';
		});
		local String is root: args:getString(key: 'root', default: '.');
		local String is dirsRaw: args:getString(key: 't', default: args:getString(key: 'tests', default: 'tests'));
		local Int is cores: Process:threadCount();
		local Int is threads: cores - 2;
		if(check: { threads < 1 }, then: {
			threads: 1;
		});
		line(bold() . color256(code: 51, text: '== specunit =='));
		line('compiler: ' . specBin);
		line('workers: ' . (threads as String) . ' (of ' . (cores as String) . ' cores)');

		self:enqueueDirs(dirsRaw: dirsRaw, root: root);
		local Int is total: SpecTestRegistry:queue:length();
		line('work items: ' . (total as String));

		Parallel:run(threads: threads, iterations: total, worker: local Function of Int(Int is threadIndex, Int is count){
			local Int is k: 0;
			local Int is idx: threadIndex;
			local Int is failures: 0;
			while({ k < count && idx < total }, {
				local WorkItem is item: SpecTestRegistry:queue:get(index: idx);
				Conditional:if(check: { item:kind == 'negative' }, then: {
					failures: failures + self:runNegative(item: item, idx: idx, specBin: specBin, root: root);
				}, else: {
					Conditional:if(check: { item:kind == 'run-fail' }, then: {
						failures: failures + self:runRunFail(item: item, idx: idx, specBin: specBin, root: root);
					}, else: {
						failures: failures + self:runSuite(item: item, idx: idx, specBin: specBin, root: root);
					});
				});
				k: k + 1;
				idx: idx + threads;
			});
			return failures;
		});

		self:report();
	}

	## Enqueues every candidate under each comma/newline-separated
	## [dirsRaw] entry (relative to [root]), via a recursive walk.
	Function is enqueueDirs(String is dirsRaw, String is root){
		dirsRaw:split(delimiter: "\n"):each(action: local Function(String is seg){
			seg:split(delimiter: ','):each(action: local Function(String is dir){
				Conditional:if(check: { dir != '' }, then: {
					self:enqueueTree(absDir: root . '/' . dir, relDir: dir . '/');
				});
			});
		});
	}

	## Walks [absDir] recursively (dot directories skipped). A directory
	## is any entry whose dirList is non-empty (spec_dir_list on a file
	## returns empty); a candidate file is a non-empty .spec file, whose
	## `#!` banner classifies it.
	Function is enqueueTree(String is absDir, String is relDir){
		Dir:dirList(path: absDir):each(action: local Function(String is name){
			Conditional:if(check: { name:startsWith(prefix: '.') }, then: {
				return;
			});
			local String is childAbs: absDir . '/' . name;
			local String is childRel: relDir . name;
			local Array of String is children: Dir:dirList(path: childAbs);
			Conditional:if(check: { children:length() > 0 }, then: {
				self:enqueueTree(absDir: childAbs, relDir: childRel . '/');
			}, else: {
				Conditional:if(check: { name:endsWith(suffix: '.spec') && fileRead(path: childAbs, default: '') != '' }, then: {
					self:enqueueFile(relPath: childRel);
				});
			});
		});
	}

	## Classifies one candidate by its `#!` banner: an explicit
	## `#! specunit: <kind>` marker wins; an unmarked file that mentions
	## the specunit package is a suite; everything else is skipped. A
	## suite whose file IMPORTS the framework (the `['specunit'` using
	## spelling) must produce a SpecUnit report table — the gate that
	## keeps entry-init machinery failures loud instead of silently
	## empty green binaries.
	Function is enqueueFile(String is relPath){
		local String is content: fileRead(path: relPath, default: '');
		local String is kind: '';
		local Boolean is requireReport: false;
		local Array of String is expect: [];
		content:split(delimiter: "\n"):each(action: local Function(String is seg){
			Conditional:if(check: { seg:startsWith(prefix: '#! specunit: ') }, then: {
				kind: seg:substring(start: 13, end: seg:length());
			}, else: {
				Conditional:if(check: { seg:startsWith(prefix: '#! expect: ') }, then: {
					expect:add(item: seg:substring(start: 11, end: seg:length()));
				});
			});
		});
		Conditional:if(check: { kind == '' && content:contains(needle: 'specunit') }, then: {
			kind: 'suite';
			requireReport: content:contains(needle: "['specunit'");
		});
		Conditional:if(check: { kind == '' || kind == 'helper' }, then: {
			return;
		});
		SpecTestRegistry:queue:add(item: WorkItem:init(itemPath: relPath, itemKind: kind, itemExpect: expect, itemRequireReport: requireReport));
	}

	## Compiles one suite (one compiler thread), executes the produced
	## binary, records the verdict, and deletes the compiled test.
	##
	## @return: 1 when anything failed, 0 when green.
	Function of Int is runSuite(WorkItem is item, Int is idx, String is specBin, String is root){
		local String is src: root . '/' . item:path;
		local String is bin: self:workPath(suffix: '.bin', idx: idx, stem: self:fileStem(path: item:path));
		local String is compileOut: bin . '.compile';
		local Array of String is cArgs: ['-c', 'cd "' . root . '" && "' . specBin . '" --quiet --threads 1 -i "' . src . '" -o "' . bin . '" > "' . compileOut . '" 2>&1'];
		local Int is cStatus: Process:execute(command: 'sh', args: cArgs);
		if(check: { cStatus != 0 }, then: {
			local String is diag: fileRead(path: compileOut, default: '');
			SpecTestRegistry:addResult(name: item:path, passed: false, note: 'compilation failed: ' . self:firstLine(text: diag), report: diag);
			fileRemove(path: compileOut);
			return 1;
		});
		fileRemove(path: compileOut);

		local String is runOut: bin . '.out';
		local Array of String is rArgs: ['-c', 'cd "' . root . '" && timeout 10 "' . bin . '" > "' . runOut . '" 2>&1'];
		local Int is rStatus: Process:execute(command: 'sh', args: rArgs);
		local String is out: fileRead(path: runOut, default: '');
		local Boolean is passed: rStatus == 0;
		if(check: { passed && out:contains(needle: '[FAIL]') }, then: {
			passed: false;
		});
		# A framework-importing suite must print the SpecUnit report
		# table: a binary that exits 0 silently (entry-init machinery
		# failing to run the runner) is a failure, never a pass.
		local String is note: '';
		if(check: { passed && item:requireReport && !out:contains(needle: '== SpecUnit ==') }, then: {
			passed: false;
			note: 'exited 0 but produced no SpecUnit report table';
		});
		if(check: { !passed && note == '' }, then: {
			note: 'exit ' . (rStatus as String) . ' — ' . self:firstLine(text: out);
		});
		SpecTestRegistry:addResult(name: item:path, passed: passed, note: note, report: out);
		fileRemove(path: bin);
		fileRemove(path: runOut);
		if(check: { passed }, then: {
			return 0;
		});
		return 1;
	}

	## Compile-must-fail: the produced diagnostics must contain every
	## `#! expect:` string from the file's banner.
	##
	## @return: 1 when the compile succeeds or an expect is missing, 0
	##          when green.
	Function of Int is runNegative(WorkItem is item, Int is idx, String is specBin, String is root){
		local String is src: root . '/' . item:path;
		local String is compileOut: self:workPath(suffix: '.compile', idx: idx, stem: self:fileStem(path: item:path));
		local Array of String is cArgs: ['-c', 'cd "' . root . '" && "' . specBin . '" --quiet --threads 1 -i "' . src . '" -o "/dev/null" > "' . compileOut . '" 2>&1'];
		local Int is cStatus: Process:execute(command: 'sh', args: cArgs);
		local String is cText: fileRead(path: compileOut, default: '');
		local Boolean is passed: true;
		local String is note: '';
		if(check: { cStatus == 0 }, then: {
			passed: false;
			note: 'compilation succeeded but must fail';
		}, else: {
			if(check: { !self:allPresent(text: cText, expect: item:expect) }, then: {
				passed: false;
				note: 'missing expected diagnostic';
			});
		});
		SpecTestRegistry:addResult(name: item:path, passed: passed, note: note, report: cText);
		fileRemove(path: compileOut);
		if(check: { passed }, then: {
			return 0;
		});
		return 1;
	}

	## Compile-then-run-must-fail: the binary must exit non-zero and its
	## output must contain every expected string — the framework's
	## graceful failures (an empty suite) and the reflection floor's
	## panics (a non-void or parametered test method, an
	## unconstructible test class).
	##
	## @return: 1 when anything failed, 0 when green.
	Function of Int is runRunFail(WorkItem is item, Int is idx, String is specBin, String is root){
		local String is src: root . '/' . item:path;
		local String is bin: self:workPath(suffix: '.bin', idx: idx, stem: self:fileStem(path: item:path));
		local String is compileOut: bin . '.compile';
		local Array of String is cArgs: ['-c', 'cd "' . root . '" && "' . specBin . '" --quiet --threads 1 -i "' . src . '" -o "' . bin . '" > "' . compileOut . '" 2>&1'];
		local Int is cStatus: Process:execute(command: 'sh', args: cArgs);
		local Boolean is passed: true;
		local String is note: '';
		local String is evidence: '';
		if(check: { cStatus != 0 }, then: {
			passed: false;
			evidence: fileRead(path: compileOut, default: '');
			note: 'compilation failed: ' . self:firstLine(text: evidence);
		}, else: {
			fileRemove(path: compileOut);
			local String is runOut: bin . '.out';
			local Array of String is rArgs: ['-c', 'cd "' . root . '" && timeout 10 "' . bin . '" > "' . runOut . '" 2>&1'];
			local Int is rStatus: Process:execute(command: 'sh', args: rArgs);
			evidence: fileRead(path: runOut, default: '');
			if(check: { rStatus == 0 }, then: {
				passed: false;
				note: 'exited 0 but must fail';
			}, else: {
				if(check: { !self:allPresent(text: evidence, expect: item:expect) }, then: {
					passed: false;
					note: 'missing expected run diagnostic';
				});
			});
			fileRemove(path: runOut);
		});
		SpecTestRegistry:addResult(name: item:path, passed: passed, note: note, report: evidence);
		fileRemove(path: compileOut);
		fileRemove(path: bin);
		if(check: { passed }, then: {
			return 0;
		});
		return 1;
	}

	## The flat /tmp work path for one item's artifacts: pid + queue
	## index + stem keeps concurrent compiles collision-free.
	Function of String is workPath(String is suffix, Int is idx, String is stem){
		return '/tmp/specrun_' . (Process:getPid() as String) . '_' . (idx as String) . '_' . stem . suffix;
	}

	## The report: the per-item table in queue order, failed items'
	## evidence printed, then the CI exit. Bare calls throughout — the
	## runner is an instance class, so the as-imported surfaces dispatch
	## through self (builtin if included: it yields in local-init
	## position, and binds to a local before any call-argument use).
	Function is report(){
		local Int is passed: 0;
		local Int is failed: 0;
		local Int is nameLen: 14;
		SpecTestRegistry:results:each(action: local Function(SuiteResult is r){
			if(check: { r:name:length() > nameLen }, then: {
				nameLen: r:name:length();
			});
			if(check: { r:passed }, then: {
				passed: passed + 1;
			}, else: {
				failed: failed + 1;
			});
		});
		line('');
		line(bold() . color256(code: 51, text: '== Results =='));
		SpecTestRegistry:results:each(action: local Function(SuiteResult is r){
			local String is status: if(check: { r:passed }, then: { color256(code: 114, text: '[PASS]'); }, else: { color256(code: 203, text: '[FAIL]'); });
			local String is pad: '';
			repeat(count: nameLen - r:name:length(), worker: {
				pad: pad . ' ';
			});
			line(status . ' ' . r:name . pad . '  ' . r:note);
			if(check: { !r:passed && r:report != '' }, then: {
				line(color256(code: 203, text: r:report));
			});
		});
		local String is verdict: if(check: { failed == 0 }, then: { color256(code: 114, text: 'ALL GREEN'); }, else: { color256(code: 203, text: 'FAILED'); });
		line(bold() . color256(code: 51, text: '== ' . (passed as String) . ' passed, ' . (failed as String) . ' failed — ' . verdict . ' =='));
		local Int is exitCode: if(check: { failed > 0 }, then: { 1 }, else: { 0 });
		exit(status: exitCode);
	}

	## Whether [text] contains every expected message.
	Function of Boolean is allPresent(String is text, Array of String is expect){
		local Boolean is all: true;
		expect:each(action: local Function(String is msg){
			if(check: { !text:contains(needle: msg) }, then: {
				all: false;
			});
		});
		return all;
	}

	## The first line of [text] — the compile/run diagnostic headline.
	Function of String is firstLine(String is text){
		if(check: { text == '' }, then: {
			return '';
		});
		local Int is nl: text:indexOf(search: "\n", default: text:length());
		return text:substring(start: 0, end: nl);
	}

	## The file's basename without the .spec extension.
	Function of String is fileStem(String is path){
		local Array of String is segs: path:split(delimiter: '/');
		local String is base: segs:get(index: segs:length() - 1);
		local Array of String is parts: base:split(delimiter: '.');
		return parts:get(index: 0);
	}
}
