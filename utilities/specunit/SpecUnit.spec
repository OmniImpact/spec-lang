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
		:name: suiteName;
	}
}

Class is WorkItem{
	namespace: ['specunit'];

	String is path;
	String is kind;
	Array of String is expect: [];

	replace Function is init(String is itemPath, String is itemKind, Array of String is itemExpect){
		:path: itemPath;
		:kind: itemKind;
		:expect: itemExpect;
	}
}

Class is SpecTestUi{
	namespace: ['specunit'];

	replace Array of Array of String is using: [
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Cleo is ui;
	CleoSection is wSec;
	Int is wBarSlot: 0;
	CleoSection is sSec;
	CleoSection is rSec;
	CleoSection is pSec;
	Int is pSlot: 0;
	Int is total: 0;
	Int is maxSuiteRows: 16;

	Array of Int is workerActive: [];
	Map of String to Int is suiteNameToSlotId: Map:init();
	Int is startedCount: 0;
	Int is completedCount: 0;
	Int is passedCount: 0;
	Int is failedCount: 0;
	Int is totalCpuUs: 0;
	Int is totalRssKb: 0;
	Int is peakRssKb: 0;
	Int is metricSamples: 0;

	replace Function is init(Cleo is ui, CleoSection is wSec, Int is wBarSlot, CleoSection is sSec, CleoSection is rSec, CleoSection is pSec, Int is pSlot, Int is total, Int is threads, Map of String to Int is nameToSlot){
		:ui: ui;
		:wSec: wSec;
		:wBarSlot: wBarSlot;
		:sSec: sSec;
		:rSec: rSec;
		:pSec: pSec;
		:pSlot: pSlot;
		:total: total;
		:suiteNameToSlotId: nameToSlot;
		:workerActive: [];
		local Int is i: 0;
		while({ i < threads }, {
			:workerActive:add(item: 0);
			i: i + 1;
		});
		:renderWorkersBar();
	}

	Function is renderWorkersBar(){
		local Int is n: :workerActive:length();
		local Int is activeCount: 0;
		local String is boxes: '';
		local Int is i: 0;
		while({ i < n }, {
			local Int is st: :workerActive:get(index: i, default: 0);
			if({ i > 0 }, { boxes: boxes . ' '; });
			if(check: { st != 0 }, then: {
				boxes: boxes . '■';
				activeCount: activeCount + 1;
			}, else: {
				boxes: boxes . '□';
			});
			i: i + 1;
		});
		local String is rt: (activeCount as String) . '/' . (n as String) . ' active';
		:wSec:updateText(index: :wBarSlot, text: boxes, rightText: rt);
	}

	Function is syncProgress(){
		local Float is s1: if({ :total > 0 }, { (:completedCount as Float) / (:total as Float) }, { 1.0 });
		local Float is s2: if({ :total > 0 }, { (:startedCount as Float) / (:total as Float) }, { 1.0 });
		local String is msg: (:completedCount as String) . '/' . (:total as String) . ' completed (' . (:startedCount as String) . ' queued/active, ' . (:failedCount as String) . ' failed)';
		:pSec:updateProgress(index: :pSlot, text: msg, stage1: s1, stage2: s2);
	}

	Function is onStarted(Int is threadIndex, String is itemPath){
		:startedCount: :startedCount + 1;
		if({ threadIndex >= 0 && threadIndex < :workerActive:length() }, {
			:workerActive:set(index: threadIndex, value: 1);
		});
		:renderWorkersBar();

		local Int is slotId: :sSec:addShapeThrobber(
			shape: ThrobberShape:CIRCLE_DOT,
			effect: ThrobberEffect:BLINK,
			color: CleoColor:ansi(code: 254),
			text: itemPath,
			rightText: 'compiling'
		);
		:suiteNameToSlotId:set(key: itemPath, value: slotId);
		:syncProgress();
		:ui:markDirty();
		:ui:flushUnlocked();
	}

	Function is onRunning(String is itemPath){
		if({ :suiteNameToSlotId:has(key: itemPath) }, {
			local Int is slotId: :suiteNameToSlotId:get(key: itemPath);
			:sSec:updateText(index: slotId, text: itemPath, rightText: 'running');
			:ui:markDirty();
			:ui:flushUnlocked();
		});
	}

	Function is onWorkerIdle(Int is threadIndex){
		if({ threadIndex >= 0 && threadIndex < :workerActive:length() }, {
			:workerActive:set(index: threadIndex, value: 0);
		});
		:renderWorkersBar();
	}

	Function is onResult(String is name, Boolean is passed, String is note){
		:completedCount: :completedCount + 1;
		if({ passed }, { :passedCount: :passedCount + 1; });
		if({ !passed }, { :failedCount: :failedCount + 1; });

		if({ :suiteNameToSlotId:has(key: name) }, {
			local Int is slotId: :suiteNameToSlotId:get(key: name);
			local String is rt: if({ passed }, { 'passed' }, { 'failed' });
			local CleoColor is c: if({ passed }, { CleoColor:ansi(code: 255) }, { CleoColor:ansi(code: 242) });
			:sSec:resolveSlot(index: slotId, badge: '●', text: name, color: c, rightText: rt);
			:ui:commitSlotUnlocked(section: :sSec, slotId: slotId);
			:sSec:removeSlot(index: slotId);
		});

		:syncProgress();
		:ui:markDirty();
		:ui:flushUnlocked();
	}

	Function is onMetrics(Int is cpuUs, Int is rssKb){
		:totalCpuUs: :totalCpuUs + cpuUs;
		if({ rssKb > 0 }, {
			:totalRssKb: :totalRssKb + rssKb;
			:metricSamples: :metricSamples + 1;
			if({ rssKb > :peakRssKb }, { :peakRssKb: rssKb; });
		});
	}

	Function of String is fmtSec(Int is ms){
		local Int is whole: ms / 1000;
		local Int is frac: (ms % 1000) / 10;
		local String is fStr: if({ frac < 10 }, { '0' . (frac as String) }, { (frac as String) });
		return (whole as String) . '.' . fStr . 's';
	}

	Function of String is fmtMb(Int is kb){
		local Int is mb10: (kb * 10) / 1024;
		local Int is whole: mb10 / 10;
		local Int is frac: mb10 % 10;
		return (whole as String) . '.' . (frac as String) . ' MB';
	}

	Function is showResults(Int is wallMs){
		local String is badge: if({ :failedCount == 0 }, { '✔ ALL PASSED' }, { '✘ ' . (:failedCount as String) . ' FAILED' });
		local CleoColor is c: if({ :failedCount == 0 }, { CleoColor:ansi(code: 254) }, { CleoColor:ansi(code: 255) });
		:rSec:addLine(
			text: (:passedCount as String) . ' passed, ' . (:failedCount as String) . ' failed  (' . (:completedCount as String) . ' suites)',
			color: c,
			rightText: badge,
			bold: true
		);
		local Int is cpuMs: :totalCpuUs / 1000;
		:rSec:addLine(
			text: 'Wall time: ' . :fmtSec(ms: wallMs),
			color: CleoColor:ansi(code: 250),
			rightText: 'CPU time: ' . :fmtSec(ms: cpuMs)
		);
		local Int is avgKb: if({ :metricSamples > 0 }, { :totalRssKb / :metricSamples }, { 0 });
		:rSec:addLine(
			text: 'Memory avg: ' . :fmtMb(kb: avgKb),
			color: CleoColor:ansi(code: 250),
			rightText: 'Peak: ' . :fmtMb(kb: :peakRssKb)
		);
	}
}

## The held registry: the work queue and the results. Held arrays and
## maps are mutex-protected — the Parallel wave reads the queue and
## records results from every worker thread safely.
Class is SpecTestRegistry{
	namespace: ['specunit'];

	replace Array of Array of String is using: [
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'sys', Conditional],
		['base', 'sys', as Parallel()]
	];

	held Array of WorkItem is queue: [];
	held Array of SuiteResult is results: [];
	held Map of String to SuiteResult is byName: Map:init();
	held Array of Int is nextIdxRef: [0];
	held Array of SpecTestUi is uiHolder: [];

	held Function is setupUi(Cleo is ui, CleoSection is wSec, Int is wBarSlot, CleoSection is sSec, CleoSection is rSec, CleoSection is pSec, Int is pSlot, Int is total, Int is threads, Map of String to Int is nameToSlot){
		local SpecTestUi is helper: SpecTestUi:init(ui: ui, wSec: wSec, wBarSlot: wBarSlot, sSec: sSec, rSec: rSec, pSec: pSec, pSlot: pSlot, total: total, threads: threads, nameToSlot: nameToSlot);
		SpecTestRegistry:uiHolder:add(item: helper);
	}

	held Function is recordMetrics(String is cpuStr, String is rssStr){
		Parallel:syncWith(lock: 77, action: {
			local Conditional is cond: Conditional:init();
			cond:if(check: { return SpecTestRegistry:uiHolder:length() > 0; }, then: {
				local SpecTestUi is h: SpecTestRegistry:uiHolder:get(index: 0);
				h:onMetrics(cpuUs: cpuStr:parseInt(default: 0), rssKb: rssStr:parseInt(default: 0));
			});
		});
	}

	held Function is showResults(String is wallMsStr){
		Parallel:syncWith(lock: 77, action: {
			local Conditional is cond: Conditional:init();
			cond:if(check: { return SpecTestRegistry:uiHolder:length() > 0; }, then: {
				local SpecTestUi is h: SpecTestRegistry:uiHolder:get(index: 0);
				h:showResults(wallMs: wallMsStr:parseInt(default: 0));
			});
		});
	}

	held Function of Int is nextWorkIndex(){
		local Int is res: -1;
		Parallel:syncWith(lock: 17, action: {
			local Int is idx: SpecTestRegistry:nextIdxRef:get(index: 0, default: 0);
			local Int is tot: SpecTestRegistry:queue:length();
			local Conditional is cond: Conditional:init();
			cond:if(check: { return idx < tot; }, then: {
				SpecTestRegistry:nextIdxRef:set(index: 0, value: idx + 1);
				res: idx;
			});
		});
		return res;
	}

	held Function is markStarted(String is tiStr, String is itemPath){
		Parallel:syncWith(lock: 77, action: {
			local Conditional is cond: Conditional:init();
			cond:if(check: { return SpecTestRegistry:uiHolder:length() > 0; }, then: {
				local SpecTestUi is h: SpecTestRegistry:uiHolder:get(index: 0);
				h:onStarted(threadIndex: tiStr:parseInt(default: 0), itemPath: itemPath);
			});
		});
	}

	held Function is markRunning(String is itemPath){
		Parallel:syncWith(lock: 77, action: {
			local Conditional is cond: Conditional:init();
			cond:if(check: { return SpecTestRegistry:uiHolder:length() > 0; }, then: {
				local SpecTestUi is h: SpecTestRegistry:uiHolder:get(index: 0);
				h:onRunning(itemPath: itemPath);
			});
		});
	}

	held Function is markWorkerIdle(String is tiStr){
		Parallel:syncWith(lock: 77, action: {
			local Conditional is cond: Conditional:init();
			cond:if(check: { return SpecTestRegistry:uiHolder:length() > 0; }, then: {
				local SpecTestUi is h: SpecTestRegistry:uiHolder:get(index: 0);
				h:onWorkerIdle(threadIndex: tiStr:parseInt(default: 0));
			});
		});
	}

	held Function is addResult(String is name, Boolean is passed, String is note, String is report){
		Parallel:syncWith(lock: 17, action: {
			local SuiteResult is r: SuiteResult:init(suiteName: name);
			r:passed: passed;
			r:note: note;
			r:report: report;
			SpecTestRegistry:results:add(item: r);
			SpecTestRegistry:byName:set(key: name, value: r);
		});
		Parallel:syncWith(lock: 77, action: {
			local Conditional is cond: Conditional:init();
			cond:if(check: { return SpecTestRegistry:uiHolder:length() > 0; }, then: {
				local SpecTestUi is h: SpecTestRegistry:uiHolder:get(index: 0);
				h:onResult(name: name, passed: passed, note: note);
			});
		});
	}
}

Class is SpecUnit{
	namespace: ['specunit'];

	replace Array of Array of String is using: [
		# The plain form grants construction (the report's locals), the
		# as-form grants the bare call surface (the overloads pattern).
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'cleo', CleoWidth],
		['base', 'cleo', as CleoWidth()],
		['base', 'cleo', BorderStyle],
		['base', 'cleo', ThrobberShape],
		['base', 'cleo', ThrobberEffect],
		['base', 'cleo', TitlePlacement],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Process()],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Parallel()],
		['base', 'sys', as Dir()],
		['base', 'sys', as File()],
		['base', 'sys', as Uri()],
		['base', 'sys', as Time()],
		['base', 'core', SpecError],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task]
	];

	replace Function of Boolean is SpecErrorHandler(SpecError is error){
		line(color256(code: 203, text: 'specunit: unhandled error: ' . error:toString()));
		exit(status: 1);
		return true;
	}

	replace Function is init(Map of String to String is args){
		local String is specBin: args:getString(key: 's', default: args:getString(key: 'spec', default: '.'));
		if(check: { specBin == '.' }, then: {
			specBin: 'bin/spec';
		});
		local String is root: args:getString(key: 'root', default: '.');
		local String is dirsRaw: args:getString(key: 't', default: args:getString(key: 'tests', default: ''));
		if(check: { dirsRaw == '' }, then: {
			line(color256(code: 203, text: 'specunit: missing required -t <dir> (or --tests <dir>)'));
			exit(status: 1);
		});
		local String is srcDirsRaw: args:getString(key: 'S', default: args:getString(key: 'source-dirs', default: ''));
		local Boolean is useLlvm: args:has(key: 'llvm');
		local String is srcDirFlags: :buildSourceDirFlags(raw: srcDirsRaw);
		if(check: { useLlvm }, then: {
			srcDirFlags: ' --llvm' . srcDirFlags;
		});
		local Int is cores: Process:threadCount();
		local String is jArg: args:getString(key: 'j', default: args:getString(key: 'threads', default: ''));
		local Int is threads: 0;
		if(check: { jArg != '' }, then: {
			threads: jArg as Int;
		}, else: {
			threads: cores - 2;
		});
		if(check: { threads < 1 }, then: {
			threads: 1;
		});
		:enqueueDirs(dirsRaw: dirsRaw, root: root);
		local Int is total: SpecTestRegistry:queue:length();
		if(check: { total == 0 }, then: {
			line(color256(code: 203, text: 'specunit: no test suites found in: ' . dirsRaw));
			exit(status: 1);
		});
		if(check: { threads > total }, then: {
			threads: total;
		});

		# Grayscale Cleo UI at 100% terminal width
		local Cleo is ui: Cleo:init(
			title: ' specunit ',
			titleColor: CleoColor:ansi(code: 255),
			titleBgColor: CleoColor:ansi(code: 236),
			width: CleoWidth:percent(pct: 100),
			outerBorder: BorderStyle:ROUNDED,
			dividerBorder: BorderStyle:THIN,
			borderColor: CleoColor:ansi(code: 240),
			dividerColor: CleoColor:ansi(code: 237)
		);
		local CleoSection is sSec: ui:addSection(
			title: ' Test Suites ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);
		sSec:groupResolvedFirst: true;
		local Map of String to Int is nameToSlot: Map:init();

		local CleoSection is wSec: ui:addSection(
			title: ' Workers (' . (threads as String) . '/' . (cores as String) . ' cores) ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);
		local Int is wBarSlot: wSec:addLine(text: '', color: CleoColor:ansi(code: 252), rightText: '0/' . (threads as String) . ' active');

		local CleoSection is rSec: ui:addSection(
			title: ' Results ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);

		local CleoSection is pSec: ui:addSection(
			title: ' Suite Progress ',
			titleColor: CleoColor:ansi(code: 254),
			titleBgColor: CleoColor:ansi(code: 237),
			titlePlacement: TitlePlacement:INLINE_BORDER,
			fgColor: CleoColor:ansi(code: 250)
		);
		local Int is pSlot: pSec:addProgressArea(
			text: '0/' . (total as String) . ' completed (' . specBin . ')',
			stage1Color: CleoColor:ansi(code: 252),
			stage2Color: CleoColor:ansi(code: 243),
			trackColor: CleoColor:ansi(code: 236),
			showTwoStagePercent: true
		);

		SpecTestRegistry:setupUi(ui: ui, wSec: wSec, wBarSlot: wBarSlot, sSec: sSec, rSec: rSec, pSec: pSec, pSlot: pSlot, total: total, threads: threads, nameToSlot: nameToSlot);
		local Int is startMs: Time:monotonicMs();
		ThreadScope:open(body: local Function(ThreadScope is scope){
			ui:start(scope: scope);

			local Array of Task is workers: [];
			local Int is wIdx: 0;
			while({ wIdx < threads }, {
				local Int is ti: wIdx;
				local Task is wt: scope:spawn(task: local Function(){
					local Boolean is keepGoing: true;
					while({ keepGoing }, {
						local Int is idx: SpecTestRegistry:nextWorkIndex();
						if(check: { idx < 0 }, then: {
							keepGoing: false;
						}, else: {
							local WorkItem is item: SpecTestRegistry:queue:get(index: idx);
							SpecTestRegistry:markStarted(tiStr: (ti as String), itemPath: item:path);
							if(check: { item:kind == 'negative' }, then: {
								:runNegative(item: item, idx: idx, specBin: specBin, root: root, srcDirFlags: srcDirFlags);
							}, else: {
								if(check: { item:kind == 'run-fail' }, then: {
									:runRunFail(item: item, idx: idx, specBin: specBin, root: root, srcDirFlags: srcDirFlags);
								}, else: {
									:runSuite(item: item, idx: idx, specBin: specBin, root: root, srcDirFlags: srcDirFlags);
								});
							});
							SpecTestRegistry:markWorkerIdle(tiStr: (ti as String));
						});
					});
				});
				workers:add(item: wt);
				wIdx: wIdx + 1;
			});
			scope:awaitAll(group: workers);

			local Int is wallMs: Time:monotonicMs() - startMs;
			SpecTestRegistry:showResults(wallMsStr: (wallMs as String));
			ui:finish();
		});
		:report();
	}

	Function of String is buildSourceDirFlags(String is raw){
		local String is out: '';
		if(check: { raw != '' }, then: {
			raw:split(delimiter: ','):each(action: local Function(String is seg){
				local String is sd: seg:trim();
				if(check: { sd != '' }, then: {
					out: out . ' -s "' . sd . '"';
				});
			});
		});
		local String is exeDir: Dir:exeDir();
		if(check: { exeDir != '' }, then: {
			local String is bundledUnit: exeDir . '/../utilities/specunit';
			if(check: { fileExists(path: bundledUnit) }, then: {
				out: out . ' -s "' . bundledUnit . '"';
			});
			local String is bundledSpec: exeDir . '/../spec';
			if(check: { fileExists(path: bundledSpec) }, then: {
				out: out . ' -s "' . bundledSpec . '"';
			});
		});
		return out;
	}

	Function of String is resolveItemPath(String is root, String is relOrAbs){
		if(check: { relOrAbs:startsWith(prefix: '/') || (relOrAbs:length() >= 2 && relOrAbs:substring(start: 1, end: 2) == ':') }, then: {
			return relOrAbs;
		});
		return root . '/' . relOrAbs;
	}

	## Enqueues every candidate under each comma/newline-separated
	## [dirsRaw] entry (relative to [root]), via a recursive walk.
	Function is enqueueDirs(String is dirsRaw, String is root){
		dirsRaw:split(delimiter: "\n"):each(action: local Function(String is segRaw){
			local String is seg: if(check: { segRaw:endsWith(suffix: "\r") }, then: { segRaw:substring(start: 0, end: segRaw:length() - 1); }, else: { segRaw; });
			seg:split(delimiter: ','):each(action: local Function(String is dirRaw){
				local String is dir: if(check: { dirRaw:endsWith(suffix: "\r") }, then: { dirRaw:substring(start: 0, end: dirRaw:length() - 1); }, else: { dirRaw; });
				if(check: { dir != '' }, then: {
					local String is absDir: :resolveItemPath(root: root, relOrAbs: dir);
					if(check: { !fileExists(path: absDir) }, then: {
						line(color256(code: 203, text: 'specunit: test directory not found: ' . dir));
						exit(status: 1);
					});
					:enqueueTree(absDir: absDir, relDir: dir . '/');
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
			if(check: { name:startsWith(prefix: '.') }, then: {
				return;
			});
			local String is childAbs: absDir . '/' . name;
			local String is childRel: relDir . name;
			local Array of String is children: Dir:dirList(path: childAbs);
			if(check: { children:length() > 0 }, then: {
				:enqueueTree(absDir: childAbs, relDir: childRel . '/');
			}, else: {
				if(check: { name:endsWith(suffix: '.spec') && fileRead(path: childAbs, default: '') != '' }, then: {
					:enqueueFile(relPath: childRel);
				});
			});
		});
	}

	## Classifies one candidate: every suite MUST extend the SpecUnitTest
	## base class and produce a SpecUnit report table. Candidates that do not
	## extend the base test class are not runnable as suites.
	Function is enqueueFile(String is relPath){
		local String is content: fileRead(path: relPath, default: '');
		local String is kind: '';
		local Array of String is expect: [];
		content:split(delimiter: "\n"):each(action: local Function(String is segRaw){
			local String is seg: if(check: { segRaw:endsWith(suffix: "\r") }, then: { segRaw:substring(start: 0, end: segRaw:length() - 1); }, else: { segRaw; });
			if(check: { seg:startsWith(prefix: '#! specunit: ') }, then: {
				kind: seg:substring(start: 13, end: seg:length());
			}, else: {
				if(check: { seg:startsWith(prefix: '#! expect: ') }, then: {
					expect:add(item: seg:substring(start: 11, end: seg:length()));
				});
			});
		});
		if(check: { (kind == '' || kind == 'suite') && content:contains(needle: 'SpecUnitTest') }, then: {
			kind: 'suite';
		}, else: {
			if(check: { kind == 'suite' }, then: {
				kind: '';
			});
		});
		if(check: { kind == '' || kind == 'helper' }, then: {
			return;
		});
		SpecTestRegistry:queue:add(item: WorkItem:init(itemPath: relPath, itemKind: kind, itemExpect: expect));
	}

	## Compiles one suite (one compiler thread), executes the produced
	## binary, records the verdict, and deletes the compiled test.
	##
	## @return: 1 when anything failed, 0 when green.
	Function of Int is runSuite(WorkItem is item, Int is idx, String is specBin, String is root, String is srcDirFlags){
		local String is src: :resolveItemPath(root: root, relOrAbs: item:path);
		local String is exeSuffix: if(check: { Process:osName() == 'windows' }, then: { '.exe' }, else: { '.bin' });
		local String is bin: :workPath(suffix: exeSuffix, idx: idx, stem: :fileStem(path: item:path));
		local String is compileOut: bin . '.compile';
		local Array of String is cArgs: ['-c', 'cd "' . root . '" && "' . specBin . '" --quiet --threads 1' . srcDirFlags . ' -i "' . src . '" -o "' . bin . '" > "' . compileOut . '" 2>&1'];
		local Map of String to String is cRes: Process:measure(command: 'sh', args: cArgs);
		local Int is cStatus: cRes:getInt(key: 'exit', default: -1);
		local Int is cCpu: cRes:getInt(key: 'cpu_us', default: 0);
		local Int is cRss: cRes:getInt(key: 'rss_kb', default: 0);
		if(check: { cStatus != 0 }, then: {
			SpecTestRegistry:recordMetrics(cpuStr: (cCpu as String), rssStr: (cRss as String));
			local String is diag: fileRead(path: compileOut, default: '');
			SpecTestRegistry:addResult(name: item:path, passed: false, note: 'compilation failed: ' . :firstLine(text: diag), report: diag);
			fileRemove(path: compileOut);
			return 1;
		});
		fileRemove(path: compileOut);
		SpecTestRegistry:markRunning(itemPath: item:path);

		local String is runOut: bin . '.out';
		local Array of String is rArgs: ['-c', 'cd "' . root . '" && export SPEC_BIN="' . specBin . '" && "' . bin . '" < /dev/null > "' . runOut . '" 2>&1'];
		local Map of String to String is rRes: Process:measure(command: 'sh', args: rArgs);
		local Int is rStatus: rRes:getInt(key: 'exit', default: -1);
		local Int is totalCpu: cCpu + rRes:getInt(key: 'cpu_us', default: 0);
		local Int is rRss: rRes:getInt(key: 'rss_kb', default: 0);
		local Int is maxRss: if(check: { rRss > cRss }, then: { rRss; }, else: { cRss; });
		SpecTestRegistry:recordMetrics(cpuStr: (totalCpu as String), rssStr: (maxRss as String));
		local String is out: fileRead(path: runOut, default: '');
		local Boolean is passed: rStatus == 0;
		local String is note: '';
		if(check: { passed && !out:contains(needle: '== SpecUnit ==') }, then: {
			passed: false;
			note: 'exited 0 but produced no SpecUnit report table';
		});
		if(check: { !passed && note == '' }, then: {
			note: 'exit ' . (rStatus as String) . ' — ' . :firstLine(text: out);
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
	Function of Int is runNegative(WorkItem is item, Int is idx, String is specBin, String is root, String is srcDirFlags){
		local String is src: :resolveItemPath(root: root, relOrAbs: item:path);
		local String is compileOut: :workPath(suffix: '.compile', idx: idx, stem: :fileStem(path: item:path));
		local Array of String is cArgs: ['-c', 'cd "' . root . '" && "' . specBin . '" --quiet --threads 1' . srcDirFlags . ' -i "' . src . '" -o "/dev/null" > "' . compileOut . '" 2>&1'];
		local Map of String to String is cRes: Process:measure(command: 'sh', args: cArgs);
		local Int is cStatus: cRes:getInt(key: 'exit', default: -1);
		SpecTestRegistry:recordMetrics(cpuStr: (cRes:getInt(key: 'cpu_us', default: 0) as String), rssStr: (cRes:getInt(key: 'rss_kb', default: 0) as String));
		local String is cText: fileRead(path: compileOut, default: '');
		local Boolean is passed: true;
		local String is note: '';
		if(check: { cStatus == 0 }, then: {
			passed: false;
			note: 'compilation succeeded but must fail';
		}, else: {
			if(check: { !:allPresent(text: cText, expect: item:expect) }, then: {
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
	Function of Int is runRunFail(WorkItem is item, Int is idx, String is specBin, String is root, String is srcDirFlags){
		local String is src: :resolveItemPath(root: root, relOrAbs: item:path);
		local String is exeSuffix: if(check: { Process:osName() == 'windows' }, then: { '.exe' }, else: { '.bin' });
		local String is bin: :workPath(suffix: exeSuffix, idx: idx, stem: :fileStem(path: item:path));
		local String is compileOut: bin . '.compile';
		local Array of String is cArgs: ['-c', 'cd "' . root . '" && "' . specBin . '" --quiet --threads 1' . srcDirFlags . ' -i "' . src . '" -o "' . bin . '" > "' . compileOut . '" 2>&1'];
		local Map of String to String is cRes: Process:measure(command: 'sh', args: cArgs);
		local Int is cStatus: cRes:getInt(key: 'exit', default: -1);
		local Int is cCpu: cRes:getInt(key: 'cpu_us', default: 0);
		local Int is cRss: cRes:getInt(key: 'rss_kb', default: 0);
		local Boolean is passed: true;
		local String is note: '';
		local String is evidence: '';
		if(check: { cStatus != 0 }, then: {
			SpecTestRegistry:recordMetrics(cpuStr: (cCpu as String), rssStr: (cRss as String));
			passed: false;
			evidence: fileRead(path: compileOut, default: '');
			note: 'compilation failed: ' . :firstLine(text: evidence);
		}, else: {
			fileRemove(path: compileOut);
			SpecTestRegistry:markRunning(itemPath: item:path);
			local String is runOut: bin . '.out';
			local Array of String is rArgs: ['-c', 'cd "' . root . '" && "' . bin . '" < /dev/null > "' . runOut . '" 2>&1'];
			local Map of String to String is rRes: Process:measure(command: 'sh', args: rArgs);
			local Int is rStatus: rRes:getInt(key: 'exit', default: -1);
			local Int is totalCpu: cCpu + rRes:getInt(key: 'cpu_us', default: 0);
			local Int is rRss: rRes:getInt(key: 'rss_kb', default: 0);
			local Int is maxRss: if(check: { rRss > cRss }, then: { rRss; }, else: { cRss; });
			SpecTestRegistry:recordMetrics(cpuStr: (totalCpu as String), rssStr: (maxRss as String));
			evidence: fileRead(path: runOut, default: '');
			if(check: { rStatus == 0 }, then: {
				passed: false;
				note: 'exited 0 but must fail';
			}, else: {
				if(check: { !:allPresent(text: evidence, expect: item:expect) }, then: {
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

	## The flat work path for one item's artifacts: pid + queue
	## index + stem keeps concurrent compiles collision-free.
	Function of String is workPath(String is suffix, Int is idx, String is stem){
		return Uri:systemTempDir() . '/specrun_' . (Process:getPid() as String) . '_' . (idx as String) . '_' . stem . suffix;
	}

	## The report: failed items' evidence printed (if any), then the CI exit.
	Function is report(){
		local Int is passed: 0;
		local Int is failed: 0;
		SpecTestRegistry:results:each(action: local Function(SuiteResult is r){
			if(check: { r:passed }, then: {
				passed: passed + 1;
			}, else: {
				failed: failed + 1;
			});
		});
		if(check: { failed > 0 }, then: {
			line('');
			line(bold() . color256(code: 203, text: '== Failures =='));
			SpecTestRegistry:results:each(action: local Function(SuiteResult is r){
				if(check: { !r:passed }, then: {
					line(color256(code: 203, text: '[FAIL] ' . r:name . '  ' . r:note));
					if(check: { r:report != '' }, then: {
						line(color256(code: 203, text: r:report));
					});
				});
			});
		});
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
