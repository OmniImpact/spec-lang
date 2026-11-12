#! SpecUnit sweep (from phase1_test.spec): phase 1 feature surface —
#! string inspection primitives, character classification, the file
#! write/read round-trip with fallback, and process execution status.

Class of SpecUnitTest is TestPhase1{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys'],
		['base', 'sys', as File()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()]
	];

	# 1. String inspection primitives
	Function is testStringInspection(){
		local String is text: 'Hello, Spec 2026!';
		Assert:areEqualString('Hello, Spec 2026!', text);
		Assert:areEqualInt(17, text:length());
		Assert:areEqualString('H', text:charAt(index: 0, default: '?'));
		Assert:areEqualString('S', text:charAt(index: 7, default: '?'));
		Assert:areEqualString('?', text:charAt(index: 99, default: '?'));
		Assert:areEqualString('Spec', text:substring(start: 7, end: 11));
		Assert:areEqualInt(7, text:indexOf(search: 'Spec', default: -1));
		Assert:areEqualInt(-1, text:indexOf(search: 'Missing', default: -1));
	}

	Function is testCharClassification(){
		local String is digitStr: '12345';
		local String is alphaStr: 'Identifier_Name';
		local String is mixedStr: '123abc';
		local String is spaceStr: "  \t \n ";
		Assert:isTrue(digitStr:isDigit());
		Assert:isFalse(mixedStr:isDigit());
		Assert:isFalse(alphaStr:isAlpha());
		Assert:isFalse(digitStr:isAlpha());
		Assert:isTrue(spaceStr:isWhitespace());
		Assert:isFalse(digitStr:isWhitespace());
	}

	# 2. File I/O primitives
	Function is testFileWriteReadRoundTrip(){
		local String is testFilePath: '/tmp/spec_phase1_output.tmp';
		local String is fileData: "Self-Hosting Spec Stage 1 Bootstrap Data\nLine 2";
		local Boolean is writeOk: fileWrite(path: testFilePath, content: fileData);
		Assert:isTrue(writeOk);
		Assert:isTrue(fileExists(path: testFilePath));
		local String is readContent: fileRead(path: testFilePath, default: 'NOT_FOUND');
		Assert:areEqualString(fileData, readContent);
		local String is missingContent: fileRead(path: 'non_existent_file.tmp', default: 'FALLBACK_DEFAULT');
		Assert:areEqualString('FALLBACK_DEFAULT', missingContent);
	}

	# 3. Process execution
	Function is testProcessExecute(){
		local Int is exitCode: Process:execute(command: 'echo', args: ['Process:execute', 'successfully', 'invoked']);
		Assert:areEqualInt(0, exitCode);
	}
}
