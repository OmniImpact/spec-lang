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
		['specunit', AssertHelper],
		['base', 'sys', File],
		['base', 'sys', Process],
		['base', 'struct', Array]
	];

	## Returns the directory for temporary test files.
	## On Windows, uses 'bin' to stay within the repo root and avoid MSYS2 /tmp
	## path translation mismatches; on POSIX systems, uses '/tmp'.
	##
	## @return: The directory path ('bin' or '/tmp').
	held Function of String is tempDir(){
		local AssertHelper is helper: AssertHelper:init();
		return helper:resolveTempDir();
	}

	## Normalizes path separators to forward slashes for cross-platform
	## command execution under shells.
	##
	## @param path: The path to normalize.
	## @return: The normalized path with '/' separators.
	held Function of String is normalizePath(String is path){
		return path:replaceAll(search: '\\', replacement: '/');
	}

	## Returns the path to the Spec compiler binary to invoke for test assertions.
	##
	## @return: The binary path (e.g. 'bin/spec' or 'bin/spec.exe').
	held Function of String is specBin(){
		local AssertHelper is helper: AssertHelper:init();
		return helper:resolveSpecBin();
	}

	## Asserts that compiling [source] fails with a diagnostic containing [expect].
	##
	## @param source: The Spec code snippet to compile.
	## @param expect: The expected diagnostic substring.
	held Function is compilerRejects(String is source, String is expect){
		local Process is proc: Process:init();
		local File is files: File:init();
		local AssertHelper is helper: AssertHelper:init();
		local String is stem: helper:nextStem();
		local String is tmp: helper:workPath(suffix: '.spec', stem: stem);
		local String is outPath: helper:workPath(suffix: '.out', stem: stem);
		files:fileWrite(path: tmp, content: source, onSuccess: local Function(Int is n){}, onError: local Function(String is s){});
		local String is bin: helper:resolveSpecBin();
		local Array of String is args: ['-c', 'cd "." && "' . bin . '" --quiet --threads 1 -i "' . tmp . '" -o /dev/null > "' . outPath . '" 2>&1'];
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
		local AssertHelper is helper: AssertHelper:init();
		local String is stem: helper:nextStem();
		local String is outPath: helper:workPath(suffix: '.out', stem: stem);
		local String is bin: helper:resolveSpecBin();
		local String is inPath: filePath:replaceAll(search: '\\', replacement: '/');
		local Array of String is args: ['-c', 'cd "." && "' . bin . '" --quiet --threads 1 -i "' . inPath . '" -o /dev/null > "' . outPath . '" 2>&1'];
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
		local AssertHelper is helper: AssertHelper:init();
		local String is stem: helper:nextStem();
		local String is tmp: helper:workPath(suffix: '.spec', stem: stem);
		local String is targetBin: helper:workPath(suffix: helper:resolveExeSuffix(), stem: stem);
		local String is outPath: helper:workPath(suffix: '.out', stem: stem);
		files:fileWrite(path: tmp, content: source, onSuccess: local Function(Int is n){}, onError: local Function(String is s){});
		local String is bin: helper:resolveSpecBin();
		local Array of String is cArgs: ['-c', 'cd "." && "' . bin . '" --quiet --threads 1 -i "' . tmp . '" -o "' . targetBin . '" > "' . outPath . '" 2>&1'];
		local Int is cStatus: proc:execute(command: 'sh', args: cArgs);
		local Array of String is rArgs: ['-c', 'cd "." && "' . targetBin . '" < /dev/null > "' . outPath . '" 2>&1'];
		local Int is rStatus: proc:execute(command: 'sh', args: rArgs);
		local String is rOut: files:fileRead(path: outPath, onSuccess: local Function(String is s){}, onError: local Function(String is s){}, default: '');
		files:fileRemove(path: tmp);
		files:fileRemove(path: targetBin);
		files:fileRemove(path: outPath);

		local Boolean is ok: cStatus == 0 && rStatus != 0 && rOut:contains(needle: expect);
		local String is msg: 'expected run error containing \'' . expect . '\', compile ' . (cStatus as String) . ', exit ' . (rStatus as String) . ', got: ' . rOut;
		SpecUnitState:checks:add(item: CheckRecord:init(ok: ok, msg: msg));
	}

	## Asserts that compiling and running [source] succeeds with [expect] in output.
	##
	## @param source: The Spec code snippet to run.
	## @param expect: The expected runtime output substring.
	held Function is runSucceeds(String is source, String is expect){
		local Process is proc: Process:init();
		local File is files: File:init();
		local AssertHelper is helper: AssertHelper:init();
		local String is stem: helper:nextStem();
		local String is tmp: helper:workPath(suffix: '.spec', stem: stem);
		local String is targetBin: helper:workPath(suffix: helper:resolveExeSuffix(), stem: stem);
		local String is outPath: helper:workPath(suffix: '.out', stem: stem);
		files:fileWrite(path: tmp, content: source, onSuccess: local Function(Int is n){}, onError: local Function(String is s){});
		local String is bin: helper:resolveSpecBin();
		local Array of String is cArgs: ['-c', 'cd "." && "' . bin . '" --quiet --threads 1 -i "' . tmp . '" -o "' . targetBin . '" > "' . outPath . '" 2>&1'];
		local Int is cStatus: proc:execute(command: 'sh', args: cArgs);
		local Array of String is rArgs: ['-c', 'cd "." && "' . targetBin . '" < /dev/null > "' . outPath . '" 2>&1'];
		local Int is rStatus: proc:execute(command: 'sh', args: rArgs);
		local String is rOut: files:fileRead(path: outPath, onSuccess: local Function(String is s){}, onError: local Function(String is s){}, default: '');
		files:fileRemove(path: tmp);
		files:fileRemove(path: targetBin);
		files:fileRemove(path: outPath);

		local Boolean is ok: cStatus == 0 && rStatus == 0 && rOut:contains(needle: expect);
		local String is msg: 'expected run success containing \'' . expect . '\', compile ' . (cStatus as String) . ', exit ' . (rStatus as String) . ', got: ' . rOut;
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
