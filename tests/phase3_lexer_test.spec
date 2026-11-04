Class is Phase3LexerTest{

	replace Array of String is using: [
		base:io:*,
		base:struct:Array,
		base:iterator:*,
		compiler:Token,
		compiler:Lexer
	];

	replace Function is init(Map of String to String is args){
		output:line("======================================");
		output:line("        Phase 3 Pure-Spec Lexer       ");
		output:line("======================================\n");

		local String is snippet: "class MyClass{\n\tlocal Int is count: 42;\n\tlocal Float is pi: 3.14;\n\tlocal String is msg: \"Hello\";\n\tif (count >= 10 && true) {\n\t\toutput:line(msg);\n\t}\n}";

		output:line("Source to tokenize:\n" . snippet . "\n");

		local Lexer is lexer: Lexer:init(source: snippet);
		local Array of Token is tokens: lexer:tokenize();

		output:line("Total tokens emitted: " . tokens:length());

		Class is PrintTokensLoop extends Loop{
			local Array of Token is tokens;
			local Int is idx: 0;

			replace Function is init(Array of Token is tokens){
				self:tokens: tokens;
				self:idx: 0;
			}

			replace Function of Boolean is evaluate(){
				return idx < tokens:length();
			}

			replace Function of Boolean is iteration(LoopControl is control){
				local Token is tok: tokens:get(index: idx);
				output:line("Token[" . idx . "]: " . tok:getKind() . " -> '" . tok:getValue() . "' (line " . tok:getLine() . ", col " . tok:getCol() . ")");
				self:idx: idx + 1;
				return true;
			}
		}
		While:run(loop: PrintTokensLoop:init(tokens: tokens));

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
