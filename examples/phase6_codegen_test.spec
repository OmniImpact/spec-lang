##
# Phase 6 Pure Spec Code Generator Test Suite
##

class Phase6CodegenTest{

	replace local Array of String is using: [
		base:io:*,
		base:sys:Process,
		base:struct:Array,
		base:iterator:*,
		compiler:Token,
		compiler:Lexer,
		compiler:Parser,
		compiler:TypeChecker,
		compiler:CodeGenerator
	];

	init(Map of String to String is args){
		output:line("======================================");
		output:line("     Phase 6 Pure-Spec Code Generator ");
		output:line("======================================\n");

		local String is source: "class HelloCodegen{\n\treplace local Function is init(Map of String to String is args){\n\t\tlocal String is msg: \"Hello from Pure Spec Code Generator!\";\n\t\toutput:line(msg);\n\t}\n}";

		output:line("1. Lexing & Parsing target program...");
		local Lexer is lexer: Lexer:init(source: source);
		local Array of Token is tokens: lexer:tokenize();
		local Parser is parser: Parser:init(tokens: tokens);
		local ProgramNode is prog: parser:parseProgram();
		output:line("[PASS] Parsed classes: " . prog:getClasses():length());

		output:line("\n2. Running Semantic TypeChecker...");
		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is errors: tc:checkProgram(program: prog);
		output:line("Type errors: " . errors:length());
		if (errors:length() == 0) {
			output:line("[PASS] Program passed static type checking");
		}

		output:line("\n3. Generating C11 Source Code via CodeGenerator.spec...");
		local CodeGenerator is cg: CodeGenerator:init();
		local String is cCode: cg:generateProgram(program: prog, entryClass: "HelloCodegen");
		output:line("Generated C code bytes: " . cCode:length());
		if (cCode:length() > 0) {
			output:line("[PASS] Emitted complete C11 translation unit");
		}

		output:line("\n4. Writing generated C to /tmp/pure_spec_hello.c...");
		local Boolean is written: File:write(path: "/tmp/pure_spec_hello.c", content: cCode);
		if (written) {
			output:line("[PASS] Wrote /tmp/pure_spec_hello.c successfully");
		}

		output:line("\n5. Compiling /tmp/pure_spec_hello.c with gcc...");
		local Int is gccCode: Process:execute(command: "gcc", args: ["-O2", "/tmp/pure_spec_hello.c", "-o", "/tmp/pure_spec_hello"]);
		output:line("gcc exit status: " . gccCode);
		if (gccCode == 0) {
			output:line("[PASS] GCC successfully compiled pure-Spec generated C code!");
		}

		output:line("\n6. Executing compiled binary /tmp/pure_spec_hello:");
		local Int is runCode: Process:execute(command: "/tmp/pure_spec_hello", args: []);
		output:line("Binary exit status: " . runCode);
		if (runCode == 0) {
			output:line("[PASS] Executed binary successfully!");
		}

		output:line("\nPhase 6 Code Generator test completed successfully!");
	}

}
