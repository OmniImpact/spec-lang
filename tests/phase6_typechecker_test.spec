##
# Phase 6 Semantic Type Checker Test Suite
##

Class is Phase6TypeCheckerTest{

	replace local Array of String is using: [
		base:io:*,
		base:struct:Array,
		base:iterator:*,
		compiler:Token,
		compiler:Lexer,
		compiler:Parser,
		compiler:TypeChecker
	];

	replace local Function is init(Map of String to String is args){
		output:line("======================================");
		output:line("     Phase 6 Semantic Type Checker    ");
		output:line("======================================\n");

		self:testCleanProgram();
		self:testTypeMismatches();

		output:line("\nPhase 6 Type Checker test completed successfully!");
	}

	testCleanProgram(){
		output:line("--- 1. Testing Well-Typed Program ---");
		local String is source: "class ValidProgram{\n\tlocal Int is count: 42;\n\tlocal String is name: \"Spec\";\n\tlocal Boolean is active: true;\n\treplace local Function of Int is add(Int is a, Int is b){\n\t\treturn a + b;\n\t}\n}";

		local Lexer is lexer: Lexer:init(source: source);
		local Array of Token is tokens: lexer:tokenize();
		local Parser is parser: Parser:init(tokens: tokens);
		local ProgramNode is prog: parser:parseProgram();

		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is errors: tc:checkProgram(program: prog);

		output:line("Type errors detected: " . errors:length());
		if (errors:length() == 0) {
			output:line("[PASS] Zero type errors on clean program");
		}
	}

	testTypeMismatches(){
		output:line("\n--- 2. Testing Type Mismatch Detection ---");

		# A. Variable type mismatch: assigning String to Int
		local String is badVarSource: "class BadVar{\n\tlocal Int is x: \"hello\";\n}";
		local Lexer is l1: Lexer:init(source: badVarSource);
		local Parser is p1: Parser:init(tokens: l1:tokenize());
		local TypeChecker is tc1: TypeChecker:init();
		local Array of TypeError is e1: tc1:checkProgram(program: p1:parseProgram());

		output:line("Variable mismatch errors: " . e1:length());
		if (e1:length() > 0) {
			local TypeError is err: e1:get(index: 0);
			output:line("[PASS] Detected: " . err:toString());
		}

		# B. Return type mismatch: returning String from Function of Int
		local String is badRetSource: "class BadReturn{\n\treplace local Function of Int is calc(){\n\t\treturn \"wrong\";\n\t}\n}";
		local Lexer is l2: Lexer:init(source: badRetSource);
		local Parser is p2: Parser:init(tokens: l2:tokenize());
		local TypeChecker is tc2: TypeChecker:init();
		local Array of TypeError is e2: tc2:checkProgram(program: p2:parseProgram());

		output:line("Return mismatch errors: " . e2:length());
		if (e2:length() > 0) {
			local TypeError is err: e2:get(index: 0);
			output:line("[PASS] Detected: " . err:toString());
		}

		# C. If condition mismatch: using Int in if condition
		local String is badIfSource: "class BadIf{\n\treplace local Function is test(){\n\t\tif (42) {\n\t\t\tlocal Int is y: 1;\n\t\t}\n\t}\n}";
		local Lexer is l3: Lexer:init(source: badIfSource);
		local Parser is p3: Parser:init(tokens: l3:tokenize());
		local TypeChecker is tc3: TypeChecker:init();
		local Array of TypeError is e3: tc3:checkProgram(program: p3:parseProgram());

		output:line("If condition errors: " . e3:length());
		if (e3:length() > 0) {
			local TypeError is err: e3:get(index: 0);
			output:line("[PASS] Detected: " . err:toString());
		}
	}

}
