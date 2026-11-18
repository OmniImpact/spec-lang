#! LLVM backend baseline smoke tests (SpecUnit).
#!
#! Verifies the cross-platform prerequisites for the experimental LLVM backend:
#!   1. `clang` is available on PATH (Linux, macOS, Windows UCRT64).
#!   2. `clang` can compile a minimal `.ll` IR module into a native executable.
#!   3. The Spec compiler frontend (Lexer, Parser, TypeChecker) parses and
#!      type-checks a sample program cleanly.

Class of SpecUnitTest is TestLlvmSmoke{
	namespace: ['testllvm'];

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'lexer', Token],
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'checker', TypeChecker],
		['base', 'compiler', 'checker', TypeError],
		['base', 'sys', as Conditional()],
		['base', 'sys', as File()],
		['base', 'sys', as Process()],
		['base', 'sys', as Uri()]
	];

	Function is testClangToolchainAvailable(){
		local Int is rc: Process:execute(command: 'clang', args: ['--version']);
		Assert:areEqualInt(0, rc);
	}

	Function is testClangCompilesMinimalLlvmIr(){
		local String is tmp: Uri:systemTempDir();
		local String is pid: Process:getPid() as String;
		local String is llPath: tmp . '/spec_llvm_smoke_' . pid . '.ll';
		local String is binPath: tmp . '/spec_llvm_smoke_' . pid;
		if({ Process:osName() == 'windows' }, {
			binPath: binPath . '.exe';
		});

		local String is ir: "define i32 @main() {\nentry:\n  ret i32 42\n}\n";
		local Boolean is wrote: File:fileWrite(path: llPath, content: ir, onSuccess: local Function(){}, onError: local Function(String is e){});
		Assert:isTrue(wrote);

		local Int is ccRc: Process:execute(command: 'clang', args: [llPath, '-o', binPath]);
		Assert:areEqualInt(0, ccRc);

		local Int is runRc: Process:execute(command: binPath, args: []);
		Assert:areEqualInt(42, runRc);

		File:fileRemove(path: llPath);
		File:fileRemove(path: binPath);
	}

	Function is testFrontendParsesAndTypeChecks(){
		local String is src: "Class is Sample{\n\tFunction of Int is add(Int is a, Int is b){\n\t\treturn a + b;\n\t}\n}\n";
		local Lexer is lex: Lexer:init(source: src);
		local Array of Token is tokens: lex:tokenize();
		local Parser is parser: Parser:init(tokens: tokens);
		local ProgramNode is prog: parser:parseProgram();
		Assert:areEqualInt(0, parser:errors:length());

		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is errs: tc:checkProgram(program: prog);
		Assert:areEqualInt(0, errs:length());
	}
}
