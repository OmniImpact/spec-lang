class Phase3LexerTest{

	replace local Array of String is using: [
		base:io:*,
		base:struct:Array,
		compiler:Token,
		compiler:Lexer
	];

	replace local Function is init(Map of String to String is args){
		output:line("======================================");
		output:line("        Phase 3 Pure-Spec Lexer       ");
		output:line("======================================\n");

		local String is snippet: "class MyClass{\n\tlocal Int is count: 42;\n\tlocal Float is pi: 3.14;\n\tlocal String is msg: \"Hello\";\n\tif (count >= 10 && true) {\n\t\toutput:line(msg);\n\t}\n}";

		output:line("Source to tokenize:\n" . snippet . "\n");

		local Lexer is lexer: Lexer:init(source: snippet);
		local Array of Token is tokens: lexer:tokenize();

		output:line("Total tokens emitted: " . tokens:length());

		local Int is idx: 0;
		while (idx < tokens:length()) {
			local Token is tok: tokens:get(index: idx);
			output:line("Token[" . idx . "]: " . tok:getKind() . " -> '" . tok:getValue() . "' (line " . tok:getLine() . ", col " . tok:getCol() . ")");
			idx: idx + 1;
		}

		# Assertions
		local Token is firstTok: tokens:get(index: 0);
		if (firstTok:getKind() == "KEYWORD" && firstTok:getValue() == "class") {
			output:line("\n[PASS] First token is KEYWORD 'class'");
		}

		local Token is secondTok: tokens:get(index: 1);
		if (secondTok:getKind() == "IDENTIFIER" && secondTok:getValue() == "MyClass") {
			output:line("[PASS] Second token is IDENTIFIER 'MyClass'");
		}

		local Token is lastTok: tokens:get(index: tokens:length() - 1);
		if (lastTok:getKind() == "EOF") {
			output:line("[PASS] Final token is EOF");
		}

		output:line("\nPhase 3 Lexer test completed successfully!");
	}

}
