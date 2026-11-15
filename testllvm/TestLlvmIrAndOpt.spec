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

	Function is testClosureCapturesAndMatchLlvm(){
		local String is tmp: Uri:systemTempDir();
		local String is pid: Process:getPid() as String;
		local String is specPath: tmp . '/spec_llvm_mcap_' . pid . '.spec';
		local String is llPath: tmp . '/spec_llvm_mcap_' . pid . '.ll';
		local String is binPath: tmp . '/spec_llvm_mcap_' . pid;
		if({ Process:osName() == 'windows' }, {
			binPath: binPath . '.exe';
		});

		local String is src: "Class is LlvmMatchCap{\n"
			. "\treplace Array of Array of String is using: [\n"
			. "\t\t['base', 'struct', Map],\n"
			. "\t\t['base', 'sys', as Conditional()],\n"
			. "\t\t['base', 'sys', as Output()],\n"
			. "\t\t['base', 'sys', as Process()]\n"
			. "\t];\n"
			. "\treplace Function is init(Map of String to String is args){\n"
			. "\t\tlocal Int is base: 100;\n"
			. "\t\tlocal String is prefix: 'hi-';\n"
			. "\t\tlocal Function of Int is addBase: local Function of Int(Int is x){\n"
			. "\t\t\treturn base + x;\n"
			. "\t\t};\n"
			. "\t\tlocal Function of String is tagger: local Function of String(String is s){\n"
			. "\t\t\treturn prefix . s;\n"
			. "\t\t};\n"
			. "\t\tlocal Int is sum: addBase(x: 23);\n"
			. "\t\tlocal String is tag: tagger(s: 'two');\n"
			. "\t\tlocal String is label: match(when: [\n"
			. "\t\t\t{ sum == 100 }: { 'hundred' },\n"
			. "\t\t\t{ sum == 123 }: { 'two' },\n"
			. "\t\t\telse: { 'other' }\n"
			. "\t\t]);\n"
			. "\t\tlocal Int is score: match(on: tag, when: [\n"
			. "\t\t\t'hi-one': { 10 },\n"
			. "\t\t\t'hi-two': { 42 }\n"
			. "\t\t], default: { 0 });\n"
			. "\t\tif({ sum == 123 && label == 'two' && score == 42 }, {\n"
			. "\t\t\tline('llvm-mcap-ok');\n"
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
		Assert:isTrue(ll:contains(needle: '%struct.__env_'));
		Assert:isTrue(ll:contains(needle: '_destroy('));

		local Int is runRc: Process:execute(command: binPath, args: []);
		Assert:areEqualInt(0, runRc);

		File:fileRemove(path: specPath);
		File:fileRemove(path: llPath);
		File:fileRemove(path: binPath);
	}

	Function is testEnumsInheritanceAndEachLlvm(){
		local String is tmp: Uri:systemTempDir();
		local String is pid: Process:getPid() as String;
		local String is specPath: tmp . '/spec_llvm_adt_' . pid . '.spec';
		local String is llPath: tmp . '/spec_llvm_adt_' . pid . '.ll';
		local String is binPath: tmp . '/spec_llvm_adt_' . pid;
		if({ Process:osName() == 'windows' }, {
			binPath: binPath . '.exe';
		});

		local String is src: "Enum is Expr {\n"
			. "\tNum(Int is v),\n"
			. "\tPair(Int is a, Int is b)\n"
			. "}\n\n"
			. "Class is BaseBox {\n"
			. "\tInt is x: 10;\n"
			. "\treplace Function is init(){\n"
			. "\t\treturn;\n"
			. "\t}\n"
			. "}\n\n"
			. "Class of BaseBox is SubBox {\n"
			. "\tInt is y: 5;\n"
			. "\treplace Function is init(){\n"
			. "\t\treturn;\n"
			. "\t}\n"
			. "\tFunction of Int is total(){\n"
			. "\t\treturn self:x + self:y;\n"
			. "\t}\n"
			. "}\n\n"
			. "Class is LlvmAdt{\n"
			. "\treplace Array of Array of String is using: [\n"
			. "\t\t['base', 'struct', Array],\n"
			. "\t\t['base', 'struct', Map],\n"
			. "\t\t['base', 'sys', as Conditional()],\n"
			. "\t\t['base', 'sys', as Output()],\n"
			. "\t\t['base', 'sys', as Process()]\n"
			. "\t];\n"
			. "\treplace Function is init(Map of String to String is args){\n"
			. "\t\tlocal Expr is e1: Expr:Num(v: 19);\n"
			. "\t\tlocal Expr is e2: Expr:Pair(a: 20, b: 3);\n"
			. "\t\tlocal Int is v1: match(on: e1, when: [\n"
			. "\t\t\tExpr:Num: local Function of Int(Int is v){ return v; },\n"
			. "\t\t\tExpr:Pair: local Function of Int(Int is a, Int is b){ return a + b; }\n"
			. "\t\t]);\n"
			. "\t\tlocal Int is v2: match(on: e2, when: [\n"
			. "\t\t\tExpr:Num: local Function of Int(Int is v){ return v; },\n"
			. "\t\t\tExpr:Pair: local Function of Int(Int is a, Int is b){ return a + b; }\n"
			. "\t\t]);\n"
			. "\t\tlocal SubBox is sb: SubBox:init();\n"
			. "\t\tlocal Int is st: sb:total();\n"
			. "\t\tlocal Array of Int is xs: [1, 2, 3];\n"
			. "\t\tlocal Array of Int is acc: [];\n"
			. "\t\txs:each(action: local Function(Int is item){\n"
			. "\t\t\tacc:add(item: item * 2);\n"
			. "\t\t});\n"
			. "\t\tif({ v1 == 19 && v2 == 23 && st == 15 && acc:length() == 3 && acc[2] == 6 }, {\n"
			. "\t\t\tline('llvm-adt-ok');\n"
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
		Assert:isTrue(ll:contains(needle: '%struct.Expr_Num = type'));
		Assert:isTrue(ll:contains(needle: '%struct.SubBox = type'));

		local Int is runRc: Process:execute(command: binPath, args: []);
		Assert:areEqualInt(0, runRc);

		File:fileRemove(path: specPath);
		File:fileRemove(path: llPath);
		File:fileRemove(path: binPath);
	}

	Function is testSysinternalPluginsLlvm(){
		local String is tmp: Uri:systemTempDir();
		local String is pid: Process:getPid() as String;
		local String is specPath: tmp . '/spec_llvm_sys_' . pid . '.spec';
		local String is llPath: tmp . '/spec_llvm_sys_' . pid . '.ll';
		local String is binPath: tmp . '/spec_llvm_sys_' . pid;
		local String is dataPath: tmp . '/spec_llvm_sys_data_' . pid . '.txt';
		if({ Process:osName() == 'windows' }, {
			binPath: binPath . '.exe';
		});

		local String is src: "Class is LlvmSys{\n"
			. "\treplace Array of Array of String is using: [\n"
			. "\t\t['base', 'struct', Map],\n"
			. "\t\t['base', 'sys', as Conditional()],\n"
			. "\t\t['base', 'sys', as Output()],\n"
			. "\t\t['base', 'sys', as Process()],\n"
			. "\t\t['base', 'sys', as File()]\n"
			. "\t];\n"
			. "\treplace Function is init(Map of String to String is args){\n"
			. "\t\tlocal String is os: Process:osName();\n"
			. "\t\tlocal Int is p: Process:getPid();\n"
			. "\t\tlocal Int is t: Process:clockMs();\n"
			. "\t\tlocal String is path: '" . dataPath . "';\n"
			. "\t\tlocal Boolean is w: File:fileWrite(path: path, content: 'sys-ok', onSuccess: local Function(){}, onError: local Function(String is e){});\n"
			. "\t\tlocal Boolean is ex: File:fileExists(path: path);\n"
			. "\t\tlocal String is txt: File:fileRead(path: path, onSuccess: local Function(String is s){}, onError: local Function(String is e){}, default: '');\n"
			. "\t\tlocal Boolean is rm: File:fileRemove(path: path);\n"
			. "\t\tif({ os != '' && p > 0 && t >= 0 && w && ex && txt == 'sys-ok' && rm }, {\n"
			. "\t\t\tline('llvm-sys-ok');\n"
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
		Assert:isTrue(ll:contains(needle: 'call ptr @spec_process_os_name()'));
		Assert:isTrue(ll:contains(needle: 'call i1 @spec_file_exists('));

		local Int is runRc: Process:execute(command: binPath, args: []);
		Assert:areEqualInt(0, runRc);

		File:fileRemove(path: specPath);
		File:fileRemove(path: llPath);
		File:fileRemove(path: binPath);
		File:fileRemove(path: dataPath);
	}

	Function is testVtableDispatchAndUsingAsLlvm(){
		local String is tmp: Uri:systemTempDir();
		local String is pid: Process:getPid() as String;
		local String is specPath: tmp . '/spec_llvm_vt_' . pid . '.spec';
		local String is llPath: tmp . '/spec_llvm_vt_' . pid . '.ll';
		local String is binPath: tmp . '/spec_llvm_vt_' . pid;
		if({ Process:osName() == 'windows' }, {
			binPath: binPath . '.exe';
		});

		local String is src: "Class is Animal {\n"
			. "\treplace Function is init(){ return; }\n"
			. "\tFunction of Int is speak(){ return 1; }\n"
			. "}\n\n"
			. "Class of Animal is Dog {\n"
			. "\treplace Function is init(){ return; }\n"
			. "\treplace Function of Int is speak(){ return 42; }\n"
			. "}\n\n"
			. "Class is LlvmVt{\n"
			. "\treplace Array of Array of String is using: [\n"
			. "\t\t['base', 'struct', Map],\n"
			. "\t\t['base', 'sys', as Conditional()],\n"
			. "\t\t['base', 'sys', as Output()],\n"
			. "\t\t['base', 'sys', as Process()]\n"
			. "\t];\n"
			. "\treplace Function is init(Map of String to String is args){\n"
			. "\t\tlocal Animal is a: Dog:init();\n"
			. "\t\tlocal Int is s: a:speak();\n"
			. "\t\tif({ s == 42 }, {\n"
			. "\t\t\tline('llvm-vt-ok');\n"
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
		Assert:isTrue(ll:contains(needle: '@.vtable.Dog = constant'));
		Assert:isTrue(ll:contains(needle: 'getelementptr ptr, ptr'));

		local Int is runRc: Process:execute(command: binPath, args: []);
		Assert:areEqualInt(0, runRc);

		File:fileRemove(path: specPath);
		File:fileRemove(path: llPath);
		File:fileRemove(path: binPath);
	}

	Function is testDirTimeMathAndUserUsingAsLlvm(){
		local String is tmp: Uri:systemTempDir();
		local String is pid: Process:getPid() as String;
		local String is srcDir: tmp . '/spec_llvm_p7_' . pid;
		local String is helperPath: srcDir . '/MathHelper.spec';
		local String is specPath: srcDir . '/LlvmP7.spec';
		local String is llPath: tmp . '/spec_llvm_p7_' . pid . '.ll';
		local String is binPath: tmp . '/spec_llvm_p7_bin_' . pid;
		if({ Process:osName() == 'windows' }, {
			binPath: binPath . '.exe';
		});

		Process:execute(command: 'mkdir', args: ['-p', srcDir]);

		local String is helperSrc: '''
Class is MathHelper {
	namespace: ['demo'];
	replace Function is init(){ return; }
	Function of Int is triple(Int is x){ return x * 3; }
}
''';

		local String is src: ```
Class is LlvmP7{
	replace Array of Array of String is using: [
		['base', 'struct', Map],
		['base', 'math', as Math()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()],
		['base', 'sys', as Dir()],
		['base', 'sys', as Time()],
		['demo', as MathHelper()]
	];
	replace Function is init(Map of String to String is args){
		local Int is tri: triple(x: 7);
		local Int is sq: toInt(value: sqrt(value: 9.0));
		local Int is sn: toInt(value: sin(value: 0.0));
		local Int is tNs: monotonicNs();
		local Int is tMs: nowMs();
		local String is ed: exeDir();
		local Int is fsz: fileSize(path: '{{specPath}}');
		if({ tri == 21 && sq == 3 && sn == 0 && tNs > 0 && tMs > 0 && ed != '' && fsz > 0 }, {
			line('llvm-p7-ok');
		}, {
			Process:exit(status: 2);
		});
	}
}
```;

		local Boolean is wroteHelper: File:fileWrite(path: helperPath, content: helperSrc, onSuccess: local Function(){}, onError: local Function(String is e){});
		local Boolean is wrote: File:fileWrite(path: specPath, content: src, onSuccess: local Function(){}, onError: local Function(String is e){});
		Assert:isTrue(wroteHelper && wrote);

		local String is specBin: Process:getEnv(key: 'SPEC_BIN', default: 'bin/spec');
		local Int is compRc: Process:execute(command: specBin, args: ['--llvm', '--emit-llvm', llPath, '--quiet', '-s', srcDir, '-i', specPath, '-o', binPath]);
		Assert:areEqualInt(0, compRc);

		local String is ll: File:fileRead(path: llPath, onSuccess: local Function(String is s){}, onError: local Function(String is e){}, default: '');
		Assert:isTrue(ll:contains(needle: 'call double @sqrt('));
		Assert:isTrue(ll:contains(needle: 'call i64 @spec_time_monotonic_ns()'));
		Assert:isTrue(ll:contains(needle: 'call ptr @spec_exe_dir()'));

		local Int is runRc: Process:execute(command: binPath, args: []);
		Assert:areEqualInt(0, runRc);

		File:fileRemove(path: helperPath);
		File:fileRemove(path: specPath);
		Process:execute(command: 'rmdir', args: [srcDir]);
		File:fileRemove(path: llPath);
		File:fileRemove(path: binPath);
	}
}
