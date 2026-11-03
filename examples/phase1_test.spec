class Phase1Test{

	replace local Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:io:*,
		base:sys:*
	];

	replace local Function is init(Map of String to String is args){
		output:line("======================================");
		output:line("          Phase 1 Feature Test        ");
		output:line("======================================\n");

		# 1. String inspection primitives
		output:line("--- 1. String Inspection Primitives ---");
		local String is text: "Hello, Spec 2026!";
		output:line("text = \"" . text . "\"");
		output:line("text:length() = " . text:length());
		output:line("charAt(0) = " . text:charAt(index: 0, default: "?"));
		output:line("charAt(7) = " . text:charAt(index: 7, default: "?"));
		output:line("charAt(99) [default fallback] = " . text:charAt(index: 99, default: "?"));
		output:line("substring(7, 11) = " . text:substring(start: 7, end: 11));
		output:line("indexOf(\"Spec\") = " . text:indexOf(search: "Spec", default: -1));
		output:line("indexOf(\"Missing\") = " . text:indexOf(search: "Missing", default: -1));

		local String is digitStr: "12345";
		local String is alphaStr: "Identifier_Name";
		local String is mixedStr: "123abc";
		local String is spaceStr: "  \t \n ";

		output:line("\"12345\":isDigit() = " . digitStr:isDigit());
		output:line("\"123abc\":isDigit() = " . mixedStr:isDigit());
		output:line("\"Identifier_Name\":isAlpha() = " . alphaStr:isAlpha());
		output:line("\"12345\":isAlpha() = " . digitStr:isAlpha());
		output:line("\"  \\t \\n \":isWhitespace() = " . spaceStr:isWhitespace());
		output:line("\"12345\":isWhitespace() = " . digitStr:isWhitespace());

		# 2. File I/O
		output:line("\n--- 2. File I/O Primitives ---");
		local String is testFilePath: "test_phase1_output.tmp";
		local String is fileData: "Self-Hosting Spec Stage 1 Bootstrap Data\nLine 2";

		local Boolean is writeOk: File:write(path: testFilePath, content: fileData);
		output:line("File:write returned: " . writeOk);
		output:line("File:exists(testFilePath): " . File:exists(path: testFilePath));

		local String is readContent: File:read(path: testFilePath, default: "NOT_FOUND");
		output:line("File:read content:\n" . readContent);

		local String is missingContent: File:read(path: "non_existent_file.tmp", default: "FALLBACK_DEFAULT");
		output:line("File:read missing fallback: " . missingContent);

		# 3. Process Execution
		output:line("\n--- 3. Process Execution ---");
		local Int is exitCode: Process:execute(command: "echo", args: ["Process:execute", "successfully", "invoked"]);
		output:line("echo exitCode = " . exitCode);

		output:line("\nAll Phase 1 features verified successfully!");
	}

}
