#! Package specunit
#! The SpecUnit runner: reflection-driven discovery over the Introspection
#! class registry, per-test fresh instances (the xUnit rule), lifecycle
#! hooks by convention, and the report table. An INSTANCE class — the
#! suite entry (SpecUnitTest's argv-Map init) constructs it and calls
#! runAll; the mutable state lives on the SpecUnitState registry
#! singleton (see KNOWLEDGE-SPECDEV.md §4a).

Class is SpecUnitRunner{
	replace [String] is namespace: ['specunit'];

	replace [[String]] is using: [
		['specunit', SpecUnitState],
		['specunit', TestResult],
		['specunit', CheckRecord],
		['base', 'core', SpecError],
		['base', 'cleo', Cleo],
		['base', 'cleo', CleoSection],
		['base', 'cleo', CleoColor],
		['base', 'cleo', as CleoColor()],
		['base', 'cleo', CleoWidth],
		['base', 'cleo', as CleoWidth()],
		['base', 'cleo', BorderStyle],
		['base', 'cleo', TitlePlacement],
		['base', 'sys', as Mem()],
		['base', 'sys', as Introspection()],
		['base', 'sys', as Ansi()],
		['base', 'sys', as Output()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Process()]
	];

	## Discovers and runs every runnable test class whose source basename
	## starts with [sourcePrefix] — the root file's basename, so a suite
	## file's binary runs exactly that file's classes — then reports and
	## exits (1 when any test failed). A class extending the base with no
	## `test*` methods contributes nothing and is skipped; a suite with
	## no runnable test classes at all is diagnosed and fails the CI
	## contract instead of reporting a silent all-green.
	##
	## @param sourcePrefix: The root source basename prefix.
	## @param timeoutMs: Maximum allowed duration per test in milliseconds (default: 30000ms).
	Function is runAll(String is sourcePrefix, Int is timeoutMs: 30000){
		local Int is found: 0;
		classNames():each(action: local Function(String is cn){
			if(check: { :isTestClass(className: cn, sourcePrefix: sourcePrefix) }, then: {
				found: found + 1;
				:runClass(className: cn, timeoutMs: timeoutMs);
			});
		});
		if(check: { found == 0 }, then: {
			line('No test classes found in ' . sourcePrefix);
			exit(status: 1);
		});
		:report();
	}

	## Whether [className] is a runnable test class: it extends the
	## SpecUnitTest base, its source matches [sourcePrefix], and it
	## declares at least one `test*` method (own or inherited).
	##
	## @param className: The candidate class name.
	## @param sourcePrefix: The root source basename prefix.
	## @return: True when the class contributes at least one test.
	Function of Boolean is isTestClass(String is className, String is sourcePrefix){
		if(check: { !extendsClass(className: className, baseName: 'SpecUnitTest') }, then: {
			return false;
		});
		if(check: { !classSourceFile(className: className):startsWith(prefix: sourcePrefix) }, then: {
			return false;
		});
		local Boolean is has: false;
		functions(className: className):each(action: local Function(Array of String is path){
			if(check: { path:get(index: 1):startsWith(prefix: 'test') }, then: {
				has: true;
			});
		});
		return has;
	}

	local Function is recordUnhandledError(Int is errAddr, String is phase){
		if(check: { errAddr == 0 }, then: { return; });
		local SpecError is err: Mem:addrToObj(addr: errAddr) as SpecError;
		local Array of TestResult is cell: SpecUnitState:currentCell;
		if(check: { cell:length() > 0 }, then: {
			local TestResult is r: cell:get(index: 0);
			r:passed: false;
			r:failures:push(item: 'Unhandled SpecError in ' . phase . ': ' . err:toString());
		});
		Mem:releaseAddr(objAddr: errAddr);
	}

	## Runs one test class: every `test*` method on a fresh instance,
	## bracketed by `beforeEach`/`afterEach` when the class declares
	## them (lifecycle by convention — hasMethod, no annotations).
	## Unhandled [SpecError]s are caught at each phase boundary so
	## `afterEach` cleanup and `:endTest` always execute.
	##
	## @param className: The test class name.
	## @param timeoutMs: Maximum allowed duration per test in milliseconds (default: 30000ms).
	Function is runClass(String is className, Int is timeoutMs: 30000){
		local Boolean is hasBefore: hasMethod(className: className, methodName: 'beforeEach');
		local Boolean is hasAfter: hasMethod(className: className, methodName: 'afterEach');
		functions(className: className):each(action: local Function(Array of String is path){
			local String is m: path:get(index: 1);
			if(check: { m:startsWith(prefix: 'test') }, then: {
				:beginTest(name: className . '.' . m);
				local Any is instance: instantiate(className: className);
				local Int is beforeErrAddr: 0;
				if(check: { hasBefore }, then: {
					beforeErrAddr: Mem:callCatching(action: local Function(){
						invokeVoid(instance: instance, methodName: 'beforeEach');
					});
				});
				if(check: { beforeErrAddr != 0 }, then: {
					:recordUnhandledError(errAddr: beforeErrAddr, phase: 'beforeEach');
				}, else: {
					local Int is testErrAddr: Mem:callCatching(action: local Function(){
						invokeVoid(instance: instance, methodName: m);
					});
					if(check: { testErrAddr != 0 }, then: {
						:recordUnhandledError(errAddr: testErrAddr, phase: m);
					});
				});
				if(check: { hasAfter }, then: {
					local Int is afterErrAddr: Mem:callCatching(action: local Function(){
						invokeVoid(instance: instance, methodName: 'afterEach');
					});
					if(check: { afterErrAddr != 0 }, then: {
						:recordUnhandledError(errAddr: afterErrAddr, phase: 'afterEach');
					});
				});
				:endTest(timeoutMs: timeoutMs);
			});
		});
	}

	## Opens a result for the named test and makes it current.
	##
	## @param name: The "ClassName.methodName" identity.
	Function is beginTest(String is name){
		local TestResult is r: TestResult:init(testName: name);
		r:startedAtMs: clockMs();
		r:checksBefore: SpecUnitState:checks:length();
		SpecUnitState:results:add(item: r);
		SpecUnitState:currentCell:clear();
		SpecUnitState:currentCell:add(item: r);
	}

	## Closes the current result: stamps the duration.
	## Interprets this test's assertion span (the CheckRecords since
	## checksBefore): a failing record flips the result and joins its
	## failure list. Runs in the runner, where branching is available —
	## the held-side Assert appended records unconditionally.
	Function is endTest(Int is timeoutMs: 30000){
		local Array of TestResult is cell: SpecUnitState:currentCell;
		if(check: { cell:length() > 0 }, then: {
			local TestResult is r: cell:get(index: 0);
			r:durationMs: clockMs() - r:startedAtMs;
			if(check: { timeoutMs > 0 && r:durationMs > timeoutMs }, then: {
				r:passed: false;
				r:failures:push(item: 'test exceeded timeout of ' . (timeoutMs as String) . 'ms (' . (r:durationMs as String) . 'ms)');
			});
			range(start: r:checksBefore, end: SpecUnitState:checks:length(), worker: local Function(Int is idx){
				local CheckRecord is rec: SpecUnitState:checks:get(index: idx);
				if(check: { !rec:ok }, then: {
					r:passed: false;
					r:failures:push(item: rec:msg);
				});
			});
		});
	}

	## Prints the report table and exits: 1 when any test failed, 0
	## otherwise — the CI contract.
	Function is report(){
		local Int is passed: 0;
		local Int is failed: 0;
		local Int is totalMs: 0;
		local Int is nameLen: 12;
		SpecUnitState:results:each(action: local Function(TestResult is r){
			if(check: { r:name:length() > nameLen }, then: {
				nameLen: r:name:length();
			});
			if(check: { r:passed }, then: {
				passed: passed + 1;
			}, else: {
				failed: failed + 1;
			});
			totalMs: totalMs + r:durationMs;
		});
		local Cleo is ui: Cleo:toolUi(title: ' SpecUnit ');
		local CleoSection is rSec: ui:addToolSection(title: ' Results ');
		SpecUnitState:results:each(action: local Function(TestResult is r){
			local String is status: if(check: { r:passed }, then: { '[PASS]' }, else: { '[FAIL]' });
			local CleoColor is c: if(check: { r:passed }, then: { CleoColor:ansi(code: 114) }, else: { CleoColor:ansi(code: 203) });
			rSec:addLine(text: status . ' ' . r:name, color: c, rightText: (r:durationMs as String) . 'ms');
			if(check: { !r:passed }, then: {
				each(list: r:failures, action: local Function(String is f){
					rSec:addLine(text: '       - ' . f, color: CleoColor:ansi(code: 203), wrap: true);
				});
			});
		});
		local String is verdict: if(check: { failed == 0 }, then: { 'ALL PASSED' }, else: { 'FAILED' });
		local CleoColor is vColor: if(check: { failed == 0 }, then: { CleoColor:ansi(code: 114) }, else: { CleoColor:ansi(code: 203) });
		# A test GROUP is a class (the "Class" prefix of each
		# "Class.method" result); a TEST is one method's execution. A
		# class's tests run consecutively, so the group count is the
		# number of prefix transitions. Both numbers report separately.
		local Int is groups: 0;
		local String is lastGroup: '';
		SpecUnitState:results:each(action: local Function(TestResult is r){
			local Int is dot: r:name:indexOf(search: '.', default: -1);
			if(check: { dot > 0 }, then: {
				local String is g: r:name:substring(start: 0, end: dot);
				if(check: { g != lastGroup }, then: {
					groups: groups + 1;
					lastGroup: g;
				});
			});
		});
		local CleoSection is sumSec: ui:addToolSection(title: ' Summary ');
		sumSec:addLine(text: (groups as String) . ' test groups · ' . (passed as String) . ' passed · ' . (failed as String) . ' failed · ' . (totalMs as String) . 'ms', color: vColor, rightText: verdict);
		ui:render();
		# the branch-yield works in local-init position; nested as a call
		# argument the builtin if emits statement-form, so bind first.
		local Int is exitCode: if(check: { failed > 0 }, then: { 1 }, else: { 0 });
		exit(status: exitCode);
	}
}
