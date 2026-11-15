#! Unit and end-to-end tests for the experimental Spec IR, SpecOptimizer
#! pipeline, and LLVM (.ll) backend.

Class of SpecUnitTest is TestLlvmIrAndOpt{
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
		['base', 'compiler', 'ir', IrModule],
		['base', 'compiler', 'ir', IrFunction],
		['base', 'compiler', 'ir', IrBlock],
		['base', 'compiler', 'ir', IrInst],
		['base', 'compiler', 'opt', SpecOptimizer],
		['base', 'compiler', 'opt', ConstantFoldPass],
		['base', 'compiler', 'opt', OptimizerPipeline],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'llvm', LlvmEmitter],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as File()],
		['base', 'sys', as Process()],
		['base', 'sys', as Uri()]
	];

	Function is testOptimizerPipelineDiscoversAndFoldsConstants(){
		local String is src: "Class is FoldSample{\n\tFunction of Int is compute(){\n\t\treturn 2 + 3 * 4;\n\t}\n}\n";
		local Lexer is lex: Lexer:init(source: src);
		local Parser is parser: Parser:init(tokens: lex:tokenize());
		local ProgramNode is prog: parser:parseProgram();
		Assert:areEqualInt(0, parser:errors:length());

		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is errs: tc:checkProgram(program: prog);
		Assert:areEqualInt(0, errs:length());

		local IrBuilder is builder: IrBuilder:init();
		local IrModule is mod: builder:buildProgram(program: prog, entryClass: '');

		local OptimizerPipeline is pipe: OptimizerPipeline:init();
		Assert:isTrue(pipe:passes:length() >= 1);
		local SpecOptimizer is p0: pipe:passes:get(index: 0);
		Assert:areEqualString('constant-fold', p0:name());
		pipe:run(mod: mod);

		local LlvmEmitter is emitter: LlvmEmitter:init();
		local String is ll: emitter:emitModule(mod: mod);
		# 3 * 4 = 12, 2 + 12 = 14 must appear as a folded ConstInt in the emitted IR
		Assert:isTrue(ll:contains(needle: 'add i64 0, 14'));
	}

	Function is testEndToEndLlvmCompileAndRun(){
		local String is tmp: Uri:systemTempDir();
		local String is pid: Process:getPid() as String;
		local String is specPath: tmp . '/spec_llvm_e2e_' . pid . '.spec';
		local String is llPath: tmp . '/spec_llvm_e2e_' . pid . '.ll';
		local String is binPath: tmp . '/spec_llvm_e2e_' . pid;
		if({ Process:osName() == 'windows' }, {
			binPath: binPath . '.exe';
		});

		local String is src: "Class is LlvmE2E{\n"
			. "\treplace Array of Array of String is using: [\n"
			. "\t\t['base', 'sys', as Conditional()],\n"
			. "\t\t['base', 'sys', as Loops()],\n"
			. "\t\t['base', 'sys', as Output()]\n"
			. "\t];\n"
			. "\tFunction of Int is addOne(Int is x){\n"
			. "\t\treturn x + 1;\n"
			. "\t}\n"
			. "\treplace Function is init(Map of String to String is args){\n"
			. "\t\tlocal Int is sum: 0;\n"
			. "\t\tlocal Int is i: 1;\n"
			. "\t\twhile({ i <= 10 }, {\n"
			. "\t\t\tsum: sum + i;\n"
			. "\t\t\ti: self:addOne(x: i);\n"
			. "\t\t});\n"
			. "\t\tlocal Int is folded: 2 + 3 * 4;\n"
			. "\t\tif({ sum == 55 && folded == 14 }, {\n"
			. "\t\t\tline('llvm-e2e-ok');\n"
			. "\t\t});\n"
			. "\t}\n"
			. "}\n";

		local Boolean is wrote: File:fileWrite(path: specPath, content: src, onSuccess: local Function(){}, onError: local Function(String is e){});
		Assert:isTrue(wrote);

		local String is specBin: Process:getEnv(key: 'SPEC_BIN', default: 'bin/spec');
		local Int is compRc: Process:execute(command: specBin, args: ['--llvm', '--emit-llvm', llPath, '--quiet', '-i', specPath, '-o', binPath]);
		Assert:areEqualInt(0, compRc);

		local String is ll: File:fileRead(path: llPath, onSuccess: local Function(String is s){}, onError: local Function(String is e){}, default: '');
		Assert:isTrue(ll:contains(needle: 'define i64 @main('));
		Assert:isTrue(ll:contains(needle: 'add i64 0, 14'));

		local Int is runRc: Process:execute(command: binPath, args: []);
		Assert:areEqualInt(0, runRc);

		File:fileRemove(path: specPath);
		File:fileRemove(path: llPath);
		File:fileRemove(path: binPath);
	}

	Function is testContainersClosuresAndArcLlvm(){
		local String is tmp: Uri:systemTempDir();
		local String is pid: Process:getPid() as String;
		local String is specPath: tmp . '/spec_llvm_cca_' . pid . '.spec';
		local String is llPath: tmp . '/spec_llvm_cca_' . pid . '.ll';
		local String is binPath: tmp . '/spec_llvm_cca_' . pid;
		if({ Process:osName() == 'windows' }, {
			binPath: binPath . '.exe';
		});

		local String is src: "Class is LlvmCCA{\n"
			. "\treplace Array of Array of String is using: [\n"
			. "\t\t['base', 'struct', Array],\n"
			. "\t\t['base', 'struct', Map],\n"
			. "\t\t['base', 'sys', as Conditional()],\n"
			. "\t\t['base', 'sys', as Output()],\n"
			. "\t\t['base', 'sys', as Process()]\n"
			. "\t];\n"
			. "\treplace Function is init(Map of String to String is args){\n"
			. "\t\tlocal Array of Int is nums: [10, 20];\n"
			. "\t\tnums:add(item: 30);\n"
			. "\t\tlocal Int is total: nums[0] + nums:get(index: 1) + nums[2];\n"
			. "\t\tlocal Map of String to String is mp: ['lang': 'spec'];\n"
			. "\t\tmp:set(key: 'mode', value: 'llvm');\n"
			. "\t\tlocal String is mode: mp:get(key: 'mode', default: '');\n"
			. "\t\tlocal Function of Int is addTen: local Function of Int(Int is x){\n"
			. "\t\t\treturn x + 10;\n"
			. "\t\t};\n"
			. "\t\tlocal Int is res: addTen(x: total);\n"
			. "\t\tif({ nums:length() == 3 && mp:has(key: 'lang') && mode == 'llvm' && mode:length() == 4 && mode:contains(needle: 'lv') && res == 70 }, {\n"
			. "\t\t\tline('llvm-cca-ok');\n"
			. "\t\t}, {\n"
			. "\t\t\tProcess:exit(status: 2);\n"
			. "\t\t});\n"
			. "\t}\n"
			. "}\n";

		local Boolean is wrote: File:fileWrite(path: specPath, content: src, onSuccess: local Function(){}, onError: local Function(String is e){});
		Assert:isTrue(wrote);

		local String is specBin: Process:getEnv(key: 'SPEC_BIN', default: 'bin/spec');
		local Int is compRc: Process:execute(command: specBin, args: ['--llvm', '--emit-llvm', llPath, '--quiet', '-i', specPath, '-o', binPath]);
		Assert:areEqualInt(0, compRc);

		local String is ll: File:fileRead(path: llPath, onSuccess: local Function(String is s){}, onError: local Function(String is e){}, default: '');
		Assert:isTrue(ll:contains(needle: 'call ptr @spec_rt_alloc('));
		Assert:isTrue(ll:contains(needle: 'call void @spec_rt_release('));
		Assert:isTrue(ll:contains(needle: 'call ptr @spec_rt_closure_new('));

		local Int is runRc: Process:execute(command: binPath, args: []);
		Assert:areEqualInt(0, runRc);

		File:fileRemove(path: specPath);
		File:fileRemove(path: llPath);
		File:fileRemove(path: binPath);
	}
}
