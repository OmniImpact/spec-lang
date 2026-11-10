Class is Phase1Test{

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys'],
		['base', 'sys', as File()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('======================================');
		Output:line('          Phase 1 Feature Test        ');
		Output:line("======================================\n");

		# 1. String inspection primitives
		Output:line('--- 1. String Inspection Primitives ---');
		local String is text: 'Hello, Spec 2026!';
		Output:line('text = "' . text . '"');
		Output:line('text:length() = ' . text:length());
		Output:line('charAt(0) = ' . text:charAt(index: 0, default: '?'));
		Output:line('charAt(7) = ' . text:charAt(index: 7, default: '?'));
		Output:line('charAt(99) [default fallback] = ' . text:charAt(index: 99, default: '?'));
		Output:line('substring(7, 11) = ' . text:substring(start: 7, end: 11));
		Output:line('indexOf("Spec") = ' . text:indexOf(search: 'Spec', default: -1));
		Output:line('indexOf("Missing") = ' . text:indexOf(search: 'Missing', default: -1));

		local String is digitStr: '12345';
		local String is alphaStr: 'Identifier_Name';
		local String is mixedStr: '123abc';
		local String is spaceStr: "  \t \n ";

		Output:line('"12345":isDigit() = ' . digitStr:isDigit());
		Output:line('"123abc":isDigit() = ' . mixedStr:isDigit());
		Output:line('"Identifier_Name":isAlpha() = ' . alphaStr:isAlpha());
		Output:line('"12345":isAlpha() = ' . digitStr:isAlpha());
		Output:line("\"  \\t \\n \":isWhitespace() = " . spaceStr:isWhitespace());
		Output:line('"12345":isWhitespace() = ' . digitStr:isWhitespace());

		# 2. File I/O
		Output:line("\n--- 2. File I/O Primitives ---");
		local String is testFilePath: '/tmp/spec_phase1_output.tmp';
		local String is fileData: "Self-Hosting Spec Stage 1 Bootstrap Data\nLine 2";

		local Boolean is writeOk: fileWrite(path: testFilePath, content: fileData);
		Output:line('File:write returned: ' . writeOk);
		Output:line('fileExists(testFilePath): ' . fileExists(path: testFilePath));

		local String is readContent: fileRead(path: testFilePath, default: 'NOT_FOUND');
		Output:line("File:read content:\n" . readContent);

		local String is missingContent: fileRead(path: 'non_existent_file.tmp', default: 'FALLBACK_DEFAULT');
		Output:line('File:read missing fallback: ' . missingContent);

		# 3. Process Execution
		Output:line("\n--- 3. Process Execution ---");
		local Int is exitCode: Process:execute(command: 'echo', args: ['Process:execute', 'successfully', 'invoked']);
		Output:line('echo exitCode = ' . exitCode);

		Output:line("\nAll Phase 1 features verified successfully!");
	}

}
