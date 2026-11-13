#! Package specunit
#! The assertion surface: held functions appending CheckRecords into the
#! SpecUnitState registry — UNCONDITIONALLY (the ok flag carries the
#! outcome; the runner interprets records in endTest). Held bodies cannot
#! branch, so the records are data by design. Held functions do not
#! overload, so the equality asserts are typed by name — the invoke
#! ladder's future Any-marshal rung is what unifies them.
#! See KNOWLEDGE-SPECDEV.md §4a.

Class is Assert{
	namespace: ['specunit'];

	replace Array of Array of String is using: [
		['specunit', SpecUnitState],
		['specunit', CheckRecord],
		['base', 'sys', File],
		['base', 'sys', Process],
		['base', 'struct', Array]
	];

	## Asserts that compiling [source] fails with a diagnostic containing [expect].
	##
	## @param source: The Spec code snippet to compile.
	## @param expect: The expected diagnostic substring.
	held Function is compilerRejects(String is source, String is expect){
		local Process is proc: Process:init();
		local File is files: File:init();
		local String is baseTemp: files:fileTemp(template: '/tmp/spec_assert_XXXXXX');
		files:fileRemove(path: baseTemp);
		local String is tmp: baseTemp . '.spec';
		local String is outPath: tmp . '.out';
		files:fileWrite(path: tmp, content: source, onSuccess: local Function(Int is n){}, onError: local Function(String is s){});
		local Array of String is args: ['-c', './bin/spec --quiet -i "' . tmp . '" -o /dev/null > "' . outPath . '" 2>&1'];
		local Int is status: proc:execute(command: 'sh', args: args);
		local String is output: files:fileRead(path: outPath, onSuccess: local Function(String is s){}, onError: local Function(String is s){}, default: '');
		files:fileRemove(path: tmp);
		files:fileRemove(path: outPath);

		local Boolean is ok: status != 0 && output:contains(needle: expect);
		local String is msg: 'expected compile error containing \'' . expect . '\', exit ' . (status as String) . ', got: ' . output;
		SpecUnitState:checks:add(item: CheckRecord:init(ok: ok, msg: msg));
	}

	## Asserts that compiling [filePath] fails with a diagnostic containing [expect].
	##
	## @param filePath: The Spec file to compile.
	## @param expect: The expected diagnostic substring.
	held Function is compilerRejectsFile(String is filePath, String is expect){
		local Process is proc: Process:init();
		local File is files: File:init();
		local String is outPath: files:fileTemp(template: '/tmp/spec_assert_out_XXXXXX');
		local Array of String is args: ['-c', './bin/spec --quiet -i "' . filePath . '" -o /dev/null > "' . outPath . '" 2>&1'];
		local Int is status: proc:execute(command: 'sh', args: args);
		local String is output: files:fileRead(path: outPath, onSuccess: local Function(String is s){}, onError: local Function(String is s){}, default: '');
		files:fileRemove(path: outPath);

		local Boolean is ok: status != 0 && output:contains(needle: expect);
		local String is msg: 'expected compile error for ' . filePath . ' containing \'' . expect . '\', exit ' . (status as String) . ', got: ' . output;
		SpecUnitState:checks:add(item: CheckRecord:init(ok: ok, msg: msg));
	}

	## Asserts that compiling and running [source] aborts with [expect].
	##
	## @param source: The Spec code snippet to run.
	## @param expect: The expected runtime error substring.
	held Function is runFails(String is source, String is expect){
		local Process is proc: Process:init();
		local File is files: File:init();
		local String is baseTemp: files:fileTemp(template: '/tmp/spec_assert_XXXXXX');
		files:fileRemove(path: baseTemp);
		local String is tmp: baseTemp . '.spec';
		local String is bin: tmp . '.bin';
		local String is outPath: tmp . '.out';
		files:fileWrite(path: tmp, content: source, onSuccess: local Function(Int is n){}, onError: local Function(String is s){});
		local Array of String is cArgs: ['-c', './bin/spec --quiet -i "' . tmp . '" -o "' . bin . '" > "' . outPath . '" 2>&1'];
		local Int is cStatus: proc:execute(command: 'sh', args: cArgs);
		local Array of String is rArgs: ['-c', '"' . bin . '" < /dev/null > "' . outPath . '" 2>&1'];
		local Int is rStatus: proc:execute(command: 'sh', args: rArgs);
		local String is rOut: files:fileRead(path: outPath, onSuccess: local Function(String is s){}, onError: local Function(String is s){}, default: '');
		files:fileRemove(path: tmp);
		files:fileRemove(path: bin);
		files:fileRemove(path: outPath);

		local Boolean is ok: cStatus == 0 && rStatus != 0 && rOut:contains(needle: expect);
		local String is msg: 'expected run error containing \'' . expect . '\', compile ' . (cStatus as String) . ', exit ' . (rStatus as String) . ', got: ' . rOut;
		SpecUnitState:checks:add(item: CheckRecord:init(ok: ok, msg: msg));
	}

	## Records an unconditional failure.
	##
	## @param message: The failure message.
	held Function is fail(String is message){
		SpecUnitState:checks:add(item: CheckRecord:init(ok: false, msg: message));
	}

	## Integer equality: [expected] must equal [actual].
	##
	## @param expected: The expected value.
	## @param actual: The actual value.
	held Function is areEqualInt(Int is expected, Int is actual){
		SpecUnitState:checks:add(item: CheckRecord:init(ok: expected == actual, msg: 'expected ' . (expected as String) . ', got ' . (actual as String) . ' (areEqualInt)'));
	}

	## Integer inequality: [notExpected] must differ from [actual].
	##
	## @param notExpected: The forbidden value.
	## @param actual: The actual value.
	held Function is areNotEqualInt(Int is notExpected, Int is actual){
		SpecUnitState:checks:add(item: CheckRecord:init(ok: notExpected != actual, msg: 'expected anything but ' . (actual as String) . ' (areNotEqualInt)'));
	}

	## String equality: [expected] must equal [actual].
	##
	## @param expected: The expected value.
	## @param actual: The actual value.
	held Function is areEqualString(String is expected, String is actual){
		SpecUnitState:checks:add(item: CheckRecord:init(ok: expected == actual, msg: 'expected \'' . expected . '\', got \'' . actual . '\' (areEqualString)'));
	}

	## Float closeness within [delta] — never raw == on doubles.
	##
	## @param expected: The expected value.
	## @param actual: The actual value.
	## @param delta: The inclusive tolerance.
	held Function is areClose(Float is expected, Float is actual, Float is delta){
		SpecUnitState:checks:add(item: CheckRecord:init(ok: !((expected - actual) > delta || (actual - expected) > delta), msg: 'expected ' . (expected as String) . ' +/- ' . (delta as String) . ', got ' . (actual as String) . ' (areClose)'));
	}

	## Boolean truth.
	##
	## @param condition: The condition that must hold.
	held Function is isTrue(Boolean is condition){
		SpecUnitState:checks:add(item: CheckRecord:init(ok: condition, msg: 'isTrue failed'));
	}

	## Boolean falsity.
	##
	## @param condition: The condition that must not hold.
	held Function is isFalse(Boolean is condition){
		SpecUnitState:checks:add(item: CheckRecord:init(ok: !condition, msg: 'isFalse failed'));
	}
}
