#! SpecUnit sweep (from phase6_codegen_test.spec): the pure-Spec code
#! generator pipeline — parse the target program, load it through the
#! resolver cascade, typecheck, emit a complete C11 translation unit,
#! compile it with gcc, and execute the produced binary.
#!
#! Pipeline note: the old suite's gcc/run steps never printed their
#! [PASS] lines — the driver contract gained registerProgram plus the
#! entry-init fields and its embedded fixture still used the retired
#! `output:line` / `replace local Function` spellings, so the emitted C
#! could not compile (silently, the checks had no else branch). The
#! fixture is updated to current spellings and the pipeline follows the
#! driver's contract (Loader -> TypeChecker -> registerProgram ->
#! entry-init fields -> generateProgram) so every original check holds
#! for real.

Class of SpecUnitTest is TestPhase6Codegen{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', Process],
		['base', 'struct', Array],
		['base', 'iterator'],
		['base', 'compiler', 'lexer', Token],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'loader', Loader],
		['base', 'compiler', 'checker', TypeChecker],
		['base', 'compiler', 'gen', CodeGenerator],
		['base', 'sys', as File()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'checker', TypeError],
		['base', 'sys', as Conditional()]
	];

	## The target program: one HelloCodegen class printing a message,
	## spelled in the current language (as-Output import, replace
	## Function init, class-prefixed Output:line call).
	Function of String is fixtureSource(){
		return "class HelloCodegen{\n\treplace Array of Array of String is using: [\n\t\t['base', 'sys', as Output()]\n\t];\n\treplace Function is init(Map of String to String is args){\n\t\tlocal String is msg: \"Hello from Pure Spec Code Generator!\";\n\t\tOutput:line(msg);\n\t}\n}";
	}

	# Step 1: lexing & parsing the target program.
	Function is testParseFixtureProgram(){
		local Lexer is lexer: Lexer:init(source: self:fixtureSource());
		local Array of Token is tokens: lexer:tokenize();
		local Parser is parser: Parser:init(tokens: tokens);
		local ProgramNode is prog: parser:parseProgram();
		Assert:areEqualInt(1, prog:classes:length());
	}

	# Step 2: the loaded program passes static type checking.
	Function is testLoadedProgramTypechecks(){
		fileWrite(path: '/tmp/pure_spec_fixture.spec', content: self:fixtureSource());
		local Loader is loader: Loader:init();
		local ProgramNode is prog: loader:loadProgram(rootPath: '/tmp/pure_spec_fixture.spec');
		Assert:isTrue(prog:classes:length() >= 1);
		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is errors: tc:checkProgram(program: prog);
		Assert:areEqualInt(0, errors:length());
	}

	# Steps 3-4: generate the C11 translation unit and write it out
	# (streamed, as the driver does — and checked first, since the
	# checker's call resolution is what keeps the transparent library
	# classes' wrapper verbs emitted as provider calls).
	Function is testCodegenEmitsAndWritesC(){
		fileWrite(path: '/tmp/pure_spec_fixture.spec', content: self:fixtureSource());
		local Loader is loader: Loader:init();
		local ProgramNode is prog: loader:loadProgram(rootPath: '/tmp/pure_spec_fixture.spec');
		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is errors: tc:checkProgram(program: prog);
		Assert:areEqualInt(0, errors:length());
		local CodeGenerator is cg: CodeGenerator:init();
		cg:entryInitOwner: 'HelloCodegen';
		cg:entryInitOverloadIndex: 0;
		cg:entryInitTakesArgs: true;
		cg:registerProgram(classes: prog:classes);
		local Int is cLines: cg:generateProgramToFile(program: prog, entryClass: 'HelloCodegen', filePath: '/tmp/pure_spec_hello.c');
		Assert:isTrue(cLines > 0);
	}

	# Steps 5-6: gcc-compile the generated C and execute the binary.
	Function is testGeneratedBinaryCompilesAndRuns(){
		fileWrite(path: '/tmp/pure_spec_fixture.spec', content: self:fixtureSource());
		local Loader is loader: Loader:init();
		local ProgramNode is prog: loader:loadProgram(rootPath: '/tmp/pure_spec_fixture.spec');
		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is errors: tc:checkProgram(program: prog);
		Assert:areEqualInt(0, errors:length());
		local CodeGenerator is cg: CodeGenerator:init();
		cg:entryInitOwner: 'HelloCodegen';
		cg:entryInitOverloadIndex: 0;
		cg:entryInitTakesArgs: true;
		cg:registerProgram(classes: prog:classes);
		local String is ccBin: Process:getEnv(key: 'CC', default: 'gcc');
		local Array of String is gccArgs: ['-O2', '-w', '/tmp/pure_spec_hello.c', '-o', '/tmp/pure_spec_hello', '-pthread', '-lm'];
		local String is os: Process:osName();
		if({ os == 'linux' }, {
			gccArgs:add(item: '-ldl');
		});
		if({ os == 'windows' }, {
			gccArgs:add(item: '-lws2_32');
		});
		local Int is gccCode: Process:execute(command: ccBin, args: gccArgs);
		Assert:areEqualInt(0, gccCode);
		local Int is runCode: Process:execute(command: '/tmp/pure_spec_hello', args: []);
		Assert:areEqualInt(0, runCode);
	}
}
