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
		['base', 'compiler', 'llvm', CallLowerer],
		['base', 'compiler', 'llvm', CallLowererRegistry],
		['base', 'compiler', 'llvm', LlvmStructLayout],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Dir()],
		['base', 'sys', as File()],
		['base', 'sys', as Introspection()],
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
			. "\t\t\ti: :addOne(x: i);\n"
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
			. "\t\treturn :x + :y;\n"
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
		Assert:isTrue(ll:contains(needle: 'call i64 @spec_pal_os_name()'));
		Assert:isTrue(ll:contains(needle: 'call i1 @spec_pal_file_exists('));

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
		Assert:isTrue(ll:contains(needle: 'call i64 @spec_pal_exe_dir('));

		local Int is runRc: Process:execute(command: binPath, args: []);
		Assert:areEqualInt(0, runRc);

		File:fileRemove(path: helperPath);
		File:fileRemove(path: specPath);
		Process:execute(command: 'rmdir', args: [srcDir]);
		File:fileRemove(path: llPath);
		File:fileRemove(path: binPath);
	}

	Function is testHeldMembersAndReflectionLlvm(){
		local String is tmp: Uri:systemTempDir();
		local String is pid: Process:getPid() as String;
		local String is specPath: tmp . '/spec_llvm_p8_' . pid . '.spec';
		local String is llPath: tmp . '/spec_llvm_p8_' . pid . '.ll';
		local String is binPath: tmp . '/spec_llvm_p8_' . pid;
		if({ Process:osName() == 'windows' }, {
			binPath: binPath . '.exe';
		});

		local String is src: '''
Class is Counter {
	replace Array of Array of String is using: [
		['base', 'struct', Array]
	];
	held Int is count: 10;
	held Array of String is tags: [];
	held Function of Int is bump(Int is delta){
		return Counter:count + delta;
	}
}

Class is LlvmP8{
	replace Array of Array of String is using: [
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()]
	];
	replace Function is init(Map of String to String is args){
		local Int is b: Counter:bump(delta: 5);
		Counter:tags:add(item: 'ok');
		if({ b == 15 && Counter:count == 10 && Counter:tags:length() == 1 }, {
			line('llvm-p8-ok');
		}, {
			Process:exit(status: 2);
		});
	}
}
''';

		local Boolean is wrote: File:fileWrite(path: specPath, content: src, onSuccess: local Function(){}, onError: local Function(String is e){});
		Assert:isTrue(wrote);

		local String is specBin: Process:getEnv(key: 'SPEC_BIN', default: 'bin/spec');
		local Int is compRc: Process:execute(command: specBin, args: ['--llvm', '--emit-llvm', llPath, '--quiet', '-i', specPath, '-o', binPath]);
		Assert:areEqualInt(0, compRc);

		local String is ll: File:fileRead(path: llPath, onSuccess: local Function(String is s){}, onError: local Function(String is e){}, default: '');
		Assert:isTrue(ll:contains(needle: '@.meta.Counter = private constant'));
		Assert:isTrue(ll:contains(needle: '@spec_class_registry = constant ['));
		Assert:isTrue(ll:contains(needle: '@spec_held_registry = constant ['));
		Assert:isTrue(ll:contains(needle: '@Counter_count__ensure('));

		local Int is runRc: Process:execute(command: binPath, args: []);
		Assert:areEqualInt(0, runRc);

		File:fileRemove(path: specPath);
		File:fileRemove(path: llPath);
		File:fileRemove(path: binPath);
	}

	Function is testCallLowererPluginsRegistered(){
		local Array of CallLowerer is loaded: CallLowererRegistry:init():loadAll();
		local Array of String is loadedTypes: [];
		local Int is li: 0;
		while({ li < loaded:length() }, {
			loadedTypes:add(item: Introspection:typeIdentity(obj: loaded:get(index: li)));
			li++;
		});

		local Array of String is entries: Dir:dirList(path: 'spec/base/compiler/llvm');
		local Int is ei: 0;
		local Int is checked: 0;
		while({ ei < entries:length() }, {
			local String is f: entries:get(index: ei, default: '');
			if({ f:endsWith(suffix: 'CallLowerer.spec') && f != 'CallLowerer.spec' }, {
				local String is clsName: f:substring(start: 0, end: f:length() - 5);
				local String is qname: 'base:compiler:llvm:' . clsName;
				local Boolean is found: false;
				local Int is ti: 0;
				while({ ti < loadedTypes:length() }, {
					local String is tid: loadedTypes:get(index: ti, default: '');
					if({ tid == clsName || tid == qname }, {
						found: true;
					});
					ti++;
				});
				Assert:isTrue(found);
				checked++;
			});
			ei++;
		});
		Assert:isTrue(checked >= 8);
	}

	Function is testLlvmStructLayouts(){
		local LlvmStructLayout is hdr: LlvmStructLayout:objHeader();
		Assert:areEqualInt(0, hdr:fieldIndex(name: 'type_name'));
		Assert:areEqualInt(1, hdr:fieldIndex(name: 'vtable'));
		Assert:areEqualString('{ ptr, ptr }', hdr:llvmType());

		local LlvmStructLayout is mm: LlvmStructLayout:methodMeta();
		Assert:areEqualInt(4, mm:fieldCount());
		Assert:areEqualString('{ ptr, ptr, i32, i32 }', mm:llvmType());
		Assert:areEqualString('{ ptr, ptr, i32, i32 } { ptr @n, ptr @f, i32 1, i32 42 }', mm:formatConst(values: ['@n', '@f', '1', '42']));

		local LlvmStructLayout is cm: LlvmStructLayout:classMeta();
		Assert:areEqualInt(7, cm:fieldCount());
		Assert:areEqualInt(4, cm:fieldIndex(name: 'construct'));
		Assert:areEqualString('{ ptr, ptr, ptr, i32, ptr, ptr, i32 }', cm:llvmType());

		local LlvmStructLayout is he: LlvmStructLayout:heldEntry();
		Assert:areEqualInt(4, he:fieldCount());
		Assert:areEqualString('{ ptr, ptr, i32, ptr }', he:llvmType());
	}

	Function is testArcDestructionAndPoolLlvm(){
		local String is tmp: Uri:systemTempDir();
		local String is pid: Process:getPid() as String;
		local String is specPath: tmp . '/spec_llvm_p9_' . pid . '.spec';
		local String is llPath: tmp . '/spec_llvm_p9_' . pid . '.ll';
		local String is binPath: tmp . '/spec_llvm_p9_bin_' . pid;
		if({ Process:osName() == 'windows' }, {
			binPath: binPath . '.exe';
		});

		local String is src: '''
Class is Res{
	String is name: '';
	replace Function is init(String is name){
		:name: name;
	}
	Function of String is getName(){
		return :name;
	}
}

Class is Holder{
	Res is item;
	replace Function is init(Res is item){
		:item: item;
	}
	Function is setItem(Res is nextItem){
		:item: nextItem;
	}
	Function of Res is getItem(){
		return :item;
	}
}

Class is LlvmP9{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()]
	];
	Function of Res is makeRes(String is tag){
		return Res:init(name: tag);
	}
	replace Function is init(Map of String to String is args){
		local Res is r1: Res:init(name: 'first');
		local Holder is h: Holder:init(item: r1);
		if({ h:getItem():getName() != 'first' }, { Process:exit(status: 2); });

		h:setItem(nextItem: Res:init(name: 'second'));
		if({ h:getItem():getName() != 'second' }, { Process:exit(status: 3); });

		local Int is i: 0;
		while({ i < 10 }, {
			h:setItem(nextItem: :makeRes(tag: 'loop_' . (i as String)));
			i++;
		});
		if({ h:getItem():getName() != 'loop_9' }, { Process:exit(status: 4); });
		local Int is x: 5;
		if({ x++ != 5 || x != 6 || --x != 5 }, { Process:exit(status: 5); });
		line('llvm-p9-ok');
	}
}
''';

		local Boolean is wrote: File:fileWrite(path: specPath, content: src, onSuccess: local Function(){}, onError: local Function(String is e){});
		Assert:isTrue(wrote);

		local String is specBin: Process:getEnv(key: 'SPEC_BIN', default: 'bin/spec');
		local Int is compRc: Process:execute(command: specBin, args: ['--llvm', '--emit-llvm', llPath, '--quiet', '-i', specPath, '-o', binPath]);
		Assert:areEqualInt(0, compRc);

		local String is ll: File:fileRead(path: llPath, onSuccess: local Function(String is s){}, onError: local Function(String is e){}, default: '');
		Assert:isTrue(ll:contains(needle: 'define void @Holder__destroy(ptr %self)'));
		Assert:isTrue(ll:contains(needle: 'define void @Res__destroy(ptr %self)'));
		Assert:isTrue(ll:contains(needle: '@spec_pool_frame()'));
		Assert:isTrue(ll:contains(needle: '@spec_pool_release_to('));
		Assert:isTrue(ll:contains(needle: '@spec_claim_pool('));

		local Int is runRc: Process:execute(command: binPath, args: []);
		Assert:areEqualInt(0, runRc);

		File:fileRemove(path: specPath);
		File:fileRemove(path: llPath);
		File:fileRemove(path: binPath);
	}

	Function is testAnyBoxingRttiCastsAndCallbacksLlvm(){
		local String is tmp: Uri:systemTempDir();
		local String is pid: Process:getPid() as String;
		local String is specPath: tmp . '/spec_llvm_p10_' . pid . '.spec';
		local String is llPath: tmp . '/spec_llvm_p10_' . pid . '.ll';
		local String is dataPath: tmp . '/spec_llvm_p10_data_' . pid . '.txt';
		local String is binPath: tmp . '/spec_llvm_p10_' . pid;
		if({ Process:osName() == 'windows' }, {
			binPath: binPath . '.exe';
		});

		File:fileWrite(path: dataPath, content: 'hello-callback', onSuccess: local Function(){}, onError: local Function(String is e){});

		local String is src: '''
Class is Animal{
	String is kind: 'animal';
	replace Function is init(){ return; }
}

Class of Animal is Dog{
	Int is barks: 3;
	replace Function is init(){ return; }
}

Class is AnyBox{
	Any is val: 0;
	replace Function is init(Any is v){
		:val: v;
	}
	Function of Any is getVal(){
		return :val;
	}
}

Class is Counter{
	Int is n: 0;
	replace Function is init(){ return; }
}

Class is LlvmP10{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as File()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()]
	];
	Function of Any is echoAny(Any is x){
		return x;
	}
	replace Function is init(Map of String to String is args){
		# 1. Any boxing/unboxing with Int, Float, Boolean, Class
		local Any is aInt: 42;
		local Int is i: aInt as Int;
		if({ i != 42 }, { Process:exit(status: 2); });

		local Any is aFlt: 3.5;
		local Float is f: aFlt as Float;
		if({ f < 3.4 || f > 3.6 }, { Process:exit(status: 3); });

		local Any is aBool: true;
		local Boolean is b: aBool as Boolean;
		if({ !b }, { Process:exit(status: 4); });

		local AnyBox is box: AnyBox:init(v: 99);
		if({ (box:getVal() as Int) != 99 }, { Process:exit(status: 5); });
		local Any is echoed: :echoAny(x: 2.25);
		local Float is ef: echoed as Float;
		if({ ef < 2.2 || ef > 2.3 }, { Process:exit(status: 6); });

		# 2. Runtime class downcast & scalar->String/Hex/Bin/Oct casts
		local Animal is a: Dog:init();
		local Dog is d: a as Dog;
		if({ d:barks != 3 }, { Process:exit(status: 7); });

		local String is hx: 255 as Hex;
		if({ hx != 'ff' }, { Process:exit(status: 8); });
		local String is bn: 5 as Bin;
		if({ bn != '101' }, { Process:exit(status: 9); });
		local String is oc: 9 as Oct;
		if({ oc != '11' }, { Process:exit(status: 10); });
		local String is fs: 1.5 as String;
		if({ !fs:contains(needle: '1.5') }, { Process:exit(status: 11); });
		local String is bs: true as String;
		if({ bs != 'true' }, { Process:exit(status: 12); });
		local String is tn: d as String;
		if({ tn != 'Dog' }, { Process:exit(status: 13); });

		# 3. C-callback SpecClosure with captured variable
		local Counter is ctr: Counter:init();
		local String is content: File:fileRead(
			path: '__DATA_PATH__',
			onSuccess: local Function(String is s){
				ctr:n: ctr:n + 1;
				if({ s != 'hello-callback' }, { Process:exit(status: 14); });
			},
			onError: local Function(String is e){
				Process:exit(status: 15);
			},
			default: ''
		);
		if({ ctr:n != 1 || content != 'hello-callback' }, { Process:exit(status: 16); });
		line('llvm-p10-ok');
	}
}
''';
		src: src:replaceAll(search: '__DATA_PATH__', replacement: dataPath);

		local Boolean is wrote: File:fileWrite(path: specPath, content: src, onSuccess: local Function(){}, onError: local Function(String is e){});
		Assert:isTrue(wrote);

		local String is specBin: Process:getEnv(key: 'SPEC_BIN', default: 'bin/spec');
		local Int is compRc: Process:execute(command: specBin, args: ['--llvm', '--emit-llvm', llPath, '--quiet', '-i', specPath, '-o', binPath]);
		Assert:areEqualInt(0, compRc);

		local String is ll: File:fileRead(path: llPath, onSuccess: local Function(String is s){}, onError: local Function(String is e){}, default: '');
		Assert:isTrue(ll:contains(needle: 'define ptr @spec_cast_check('));
		Assert:isTrue(ll:contains(needle: 'define i1 @spec_is_subclass_of('));
		Assert:isTrue(ll:contains(needle: '@spec_to_string_float('));
		Assert:isTrue(ll:contains(needle: '@spec_type_name('));

		local Int is runRc: Process:execute(command: binPath, args: []);
		Assert:areEqualInt(0, runRc);

		File:fileRemove(path: specPath);
		File:fileRemove(path: llPath);
		File:fileRemove(path: dataPath);
		File:fileRemove(path: binPath);
	}
}
