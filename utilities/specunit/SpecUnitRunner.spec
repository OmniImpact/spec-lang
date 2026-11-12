#! Package specunit
#! The SpecUnit runner: reflection-driven discovery over the Introspection
#! class registry, per-test fresh instances (the xUnit rule), lifecycle
#! hooks by convention, and the report table. An INSTANCE class — the
#! suite entry (SpecUnitTest's argv-Map init) constructs it and calls
#! runAll; the mutable state lives on the SpecUnitState registry
#! singleton (see KNOWLEDGE-SPECDEV.md §4a).

Class is SpecUnitRunner{
	namespace: ['specunit'];

	replace Array of Array of String is using: [
		['specunit', SpecUnitState],
		['specunit', TestResult],
		['specunit', CheckRecord],
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
	Function is runAll(String is sourcePrefix){
		local Int is found: 0;
		classNames():each(action: local Function(String is cn){
			Conditional:if(check: { self:isTestClass(className: cn, sourcePrefix: sourcePrefix) }, then: {
				found: found + 1;
				self:runClass(className: cn);
			});
		});
		Conditional:if(check: { found == 0 }, then: {
			line('No test classes found in ' . sourcePrefix);
			exit(status: 1);
		});
		self:report();
	}

	## Whether [className] is a runnable test class: it extends the
	## SpecUnitTest base, its source matches [sourcePrefix], and it
	## declares at least one `test*` method (own or inherited).
	##
	## @param className: The candidate class name.
	## @param sourcePrefix: The root source basename prefix.
	## @return: True when the class contributes at least one test.
	Function of Boolean is isTestClass(String is className, String is sourcePrefix){
		Conditional:if(check: { !extendsClass(className: className, baseName: 'SpecUnitTest') }, then: {
			return false;
		});
		Conditional:if(check: { !classSourceFile(className: className):startsWith(prefix: sourcePrefix) }, then: {
			return false;
		});
		local Boolean is has: false;
		functions(className: className):each(action: local Function(Array of String is path){
			Conditional:if(check: { path:get(index: 1):startsWith(prefix: 'test') }, then: {
				has: true;
			});
		});
		return has;
	}

	## Runs one test class: every `test*` method on a fresh instance,
	## bracketed by `beforeEach`/`afterEach` when the class declares
	## them (lifecycle by convention — hasMethod, no annotations).
	##
	## @param className: The test class name.
	Function is runClass(String is className){
		local Boolean is hasBefore: hasMethod(className: className, methodName: 'beforeEach');
		local Boolean is hasAfter: hasMethod(className: className, methodName: 'afterEach');
		functions(className: className):each(action: local Function(Array of String is path){
			local String is m: path:get(index: 1);
			if(check: { m:startsWith(prefix: 'test') }, then: {
				self:beginTest(name: className . '.' . m);
				local Any is instance: instantiate(className: className);
				if(check: { hasBefore }, then: {
					invokeVoid(instance: instance, methodName: 'beforeEach');
				});
				invokeVoid(instance: instance, methodName: m);
				if(check: { hasAfter }, then: {
					invokeVoid(instance: instance, methodName: 'afterEach');
				});
				self:endTest();
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
	Function is endTest(){
		local Array of TestResult is cell: SpecUnitState:currentCell;
		Conditional:if(check: { cell:length() > 0 }, then: {
			local TestResult is r: cell:get(index: 0);
			r:durationMs: clockMs() - r:startedAtMs;
			local Int is idx: r:checksBefore;
			while({ idx < SpecUnitState:checks:length() }, {
				local CheckRecord is rec: SpecUnitState:checks:get(index: idx);
				idx++;
				Conditional:if(check: { !rec:ok }, then: {
					r:passed: false;
					r:failures:add(item: rec:msg);
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
		line(bold() . color256(code: 51, text: '== SpecUnit =='));
		SpecUnitState:results:each(action: local Function(TestResult is r){
			local String is status: if(check: { r:passed }, then: { color256(code: 114, text: '[PASS]'); }, else: { color256(code: 203, text: '[FAIL]'); });
			local String is pad: '';
			repeat(count: nameLen - r:name:length(), worker: {
				pad: pad . ' ';
			});
			line(status . ' ' . r:name . pad . '  ' . (r:durationMs as String) . 'ms');
			if(check: { !r:passed }, then: {
				r:failures:each(action: local Function(String is f){
					line(color256(code: 203, text: '       - ' . f));
				});
			});
		});
		local String is verdict: if(check: { failed == 0 }, then: { color256(code: 114, text: 'ALL GREEN'); }, else: { color256(code: 203, text: 'FAILED'); });
		line(bold() . color256(code: 51, text: '== ' . (passed as String) . ' passed, ' . (failed as String) . ' failed in ' . (totalMs as String) . 'ms — ' . verdict . ' =='));
		# the branch-yield works in local-init position; nested as a call
		# argument the builtin if emits statement-form, so bind first.
		local Int is exitCode: if(check: { failed > 0 }, then: { 1 }, else: { 0 });
		exit(status: exitCode);
	}
}
