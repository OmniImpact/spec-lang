#! priorityPosition: -100
#! SpecUnit sweep (from phase6_codegen_test.spec): the pure-Spec code
#! generator pipeline — parse the target program, load it through the
#! resolver cascade, typecheck, emit LLVM IR, compile it with clang,
#! and execute the produced binary.

Class of SpecUnitTest is TestPhase6Codegen{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator'],
		['base', 'compiler', 'lexer', Token],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'loader', Loader],
		['base', 'compiler', 'checker', TypeChecker],
		['base', 'compiler', 'driver', Driver],
		['base', 'compiler', 'ir', IrModule],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'llvm', LlvmEmitter],
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
		return "Class is HelloCodegen{\n\treplace Array of Array of String is using: [\n\t\t['base', 'sys', as Output()]\n\t];\n\treplace Function is init(Map of String to String is args){\n\t\tlocal String is msg: \"Hello from Pure Spec Code Generator!\";\n\t\tOutput:line(msg);\n\t}\n}";
	}

	# Step 1: lexing & parsing the target program.
	Function is testParseFixtureProgram(){
		local Lexer is lexer: Lexer:init(source: :fixtureSource());
		local Array of Token is tokens: lexer:tokenize();
		local Parser is parser: Parser:init(tokens: tokens);
		local ProgramNode is prog: parser:parseProgram();
		Assert:areEqualInt(1, prog:classes:length());
	}

	# Step 2: the loaded program passes static type checking.
	Function is testLoadedProgramTypechecks(){
		fileWrite(path: '/tmp/pure_spec_fixture.spec', content: :fixtureSource());
		local Loader is loader: Loader:init();
		local ProgramNode is prog: loader:loadProgram(rootPath: '/tmp/pure_spec_fixture.spec');
		Assert:isTrue(prog:classes:length() >= 1);
		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is errors: tc:checkProgram(program: prog);
		Assert:areEqualInt(0, errors:length());
	}

	# Steps 3-4: generate the LLVM IR module and write it out.
	Function is testCodegenEmitsAndWritesLlvm(){
		fileWrite(path: '/tmp/pure_spec_fixture.spec', content: :fixtureSource());
		local Loader is loader: Loader:init();
		local ProgramNode is prog: loader:loadProgram(rootPath: '/tmp/pure_spec_fixture.spec');
		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is errors: tc:checkProgram(program: prog);
		Assert:areEqualInt(0, errors:length());
		local IrBuilder is irb: IrBuilder:init();
		irb:entryInitOwner: 'HelloCodegen';
		irb:entryInitOverloadIndex: 0;
		irb:entryInitTakesMap: true;
		local IrModule is irMod: irb:buildProgram(program: prog, entryClass: 'HelloCodegen');
		local LlvmEmitter is emitter: LlvmEmitter:init();
		local String is llText: emitter:emitModule(mod: irMod);
		fileWrite(path: '/tmp/pure_spec_hello.ll', content: llText);
		Assert:isTrue(llText:length() > 0);
	}

	# Steps 5-6: compile via Driver and execute the binary.
	Function is testGeneratedBinaryCompilesAndRuns(){
		fileWrite(path: '/tmp/pure_spec_fixture.spec', content: :fixtureSource());
		local Map of String to String is cli: Map:init();
		cli:set(key: 'i', value: '/tmp/pure_spec_fixture.spec');
		cli:set(key: 'o', value: '/tmp/pure_spec_hello');
		cli:set(key: 'quiet', value: 'true');
		local Driver is d: Driver:init(args: cli);
		local Int is runCode: Process:execute(command: '/tmp/pure_spec_hello', args: []);
		Assert:areEqualInt(0, runCode);
		fileRemove(path: '/tmp/pure_spec_hello');
		fileRemove(path: '/tmp/pure_spec_hello.ll');
		fileRemove(path: '/tmp/pure_spec_fixture.spec');
	}
}
