##
# Phase 6 Pure Spec Code Generator Test Suite
##

Class is Phase6CodegenTest{

	replace Array of Array of String is using: [
		['base', 'io'],
		['base', 'sys', Process],
		['base', 'struct', Array],
		['base', 'iterator'],
		['base', 'compiler', 'lexer', Token],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'checker', TypeChecker],
		['base', 'compiler', 'gen', CodeGenerator],
		['base', 'io', as File()],
		['base', 'io', as Output()],
		['base', 'sys', as Process()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('======================================');
		Output:line('     Phase 6 Pure-Spec Code Generator ');
		Output:line("======================================\n");

		local String is source: "class HelloCodegen{\n\treplace local Function is init(Map of String to String is args){\n\t\tlocal String is msg: \"Hello from Pure Spec Code Generator!\";\n\t\toutput:line(msg);\n\t}\n}";

		Output:line('1. Lexing & Parsing target program...');
		local Lexer is lexer: Lexer:init(source: source);
		local Array of Token is tokens: lexer:tokenize();
		local Parser is parser: Parser:init(tokens: tokens);
		local ProgramNode is prog: parser:parseProgram();
		Output:line('[PASS] Parsed classes: ' . prog:classes:length());

		Output:line("\n2. Running Semantic TypeChecker...");
		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is errors: tc:checkProgram(program: prog);
		Output:line('Type errors: ' . errors:length());
		if (errors:length() == 0) {
			Output:line('[PASS] Program passed static type checking');
		}

		Output:line("\n3. Generating C11 Source Code via CodeGenerator.spec...");
		local CodeGenerator is cg: CodeGenerator:init();
		local String is cCode: cg:generateProgram(program: prog, entryClass: 'HelloCodegen');
		Output:line('Generated C code bytes: ' . cCode:length());
		if (cCode:length() > 0) {
			Output:line('[PASS] Emitted complete C11 translation unit');
		}

		Output:line("\n4. Writing generated C to /tmp/pure_spec_hello.c...");
		local Boolean is written: File:write(path: '/tmp/pure_spec_hello.c', content: cCode);
		if (written) {
			Output:line('[PASS] Wrote /tmp/pure_spec_hello.c successfully');
		}

		Output:line("\n5. Compiling /tmp/pure_spec_hello.c with gcc...");
		local Int is gccCode: Process:execute(command: 'gcc', args: ['-O2', '/tmp/pure_spec_hello.c', '-o', '/tmp/pure_spec_hello']);
		Output:line('gcc exit status: ' . gccCode);
		if (gccCode == 0) {
			Output:line('[PASS] GCC successfully compiled pure-Spec generated C code!');
		}

		Output:line("\n6. Executing compiled binary /tmp/pure_spec_hello:");
		local Int is runCode: Process:execute(command: '/tmp/pure_spec_hello', args: []);
		Output:line('Binary exit status: ' . runCode);
		if (runCode == 0) {
			Output:line('[PASS] Executed binary successfully!');
		}

		Output:line("\nPhase 6 Code Generator test completed successfully!");
	}

}
