#! Package base:compiler:driver
#! The compiler driver: CLI orchestration over load, check, generate, clang.
##
## Coordinates the Loader (multi-file package resolution), the
## TypeChecker, the IrBuilder + OptimizerPipeline + LlvmEmitter, and
## prints progress through the CompilationReport. This is the class
## the spec binary's main dispatches to with the parsed argument map;
## it IS the entry point of the self-hosted compiler.

Class is Driver{
	namespace: ['base', 'compiler', 'driver'];

	replace Array of Array of String is using: [
		['base', 'sys', as File()],
		['base', 'sys', as Process()],
		['base', 'sys', as Dir()],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'checker', TypeChecker],
		['base', 'compiler', 'loader', Loader],
		['base', 'compiler', 'driver', CompilationReport],
		['base', 'compiler', 'driver', OsLinkFlags],
		['base', 'compiler', 'pal', RuntimePrelude],
		['base', 'compiler', 'ir', IrModule],
		['base', 'compiler', 'opt', OptimizerPipeline],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'llvm', LlvmEmitter],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator'],
		['base', 'sys', as Output()],
		['base', 'sys', as Stderr()],
		['base', 'sys', as Uri()],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'lexer', Token],
		['base', 'compiler', 'checker', TypeError],
		['base', 'compiler', Error],
		['base', 'core', SpecError],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task],
		['base', 'sys', as Conditional()]
	];

	replace Function of Boolean is SpecErrorHandler(SpecError is error){
		return false;
	}

	## Entry-init probe results (resolveEntryInit): the QUALIFIED name of
	## the class owning the CHOSEN init ('' when none was chosen — the
	## entry constructs through its synthesized zero-arg default), the
	## chosen init's parameter count, its first parameter's type name,
	## its declaration-order index among the owner's init overloads
	## (the C symbol suffix the generator must emit), whether the
	## chosen init takes the command-line Map, and whether the lattice
	## declared any init overload at all. The entry rule: feed the args
	## when an init can take them, fall back to an empty init, and only
	## error when the lattice declares overloads but neither form
	## exists.
	local String is entryInitOwner: '';
	local Int is entryInitParams: 0;
	local String is entryInitFirstParam: '';
	local Int is entryInitOverloadIndex: 0;
	local Boolean is entryInitTakesMap: false;
	local Boolean is entryInitSawAny: false;

	replace Function is init(Map of String to String is args){
		local String is inputPath: args:getString(key: 'i', default: '');
		if({ inputPath == '' }, {
			inputPath: args:getString(key: 'input', default: '');
		});
		local String is outputPath: args:getString(key: 'o', default: '');
		if({ outputPath == '' }, {
			outputPath: args:getString(key: 'output', default: '');
		});
		local Boolean is releaseMode: (args:has(key: 'release') || args:has(key: 'prod')) && !args:has(key: 'debug');
		local Boolean is debugMode: !releaseMode;
		local Boolean is quiet: args:has(key: 'quiet');
		local String is threadsStr: args:getString(key: 'threads', default: '');
		if({ threadsStr == '' }, {
			threadsStr: args:getString(key: 'j', default: '');
		});
		local Int is defaultThreads: Process:threadCount() / 2;
		if({ defaultThreads < 1 }, {
			defaultThreads: 1;
		});
		local Int is threadCount: defaultThreads;
		if({ threadsStr != '' }, {
			threadCount: threadsStr:parseInt(base: 10, default: defaultThreads);
			if({ threadCount < 1 }, {
				threadCount: 1;
			});
		});
		local Array of String is sourceDirs: Array();
		local Function is addSourceDirString: local Function(String is raw){
			if({ raw != '' }, {
				raw:split(delimiter: "\n"):each(action: local Function(String is line){
					line:split(delimiter: ','):each(action: local Function(String is item){
						local String is trimmed: item:trim();
						if({ trimmed != '' }, {
							sourceDirs:add(item: trimmed);
						});
					});
				});
			});
		};
		addSourceDirString(raw: args:getString(key: 's', default: ''));
		addSourceDirString(raw: args:getString(key: 'source-dir', default: ''));
		addSourceDirString(raw: args:getString(key: 'source-dirs', default: ''));

		if({ inputPath == '' }, {
			Output:line('Spec Compiler (Pure Spec)');
			Stderr:line('Usage: spec -i <input.spec> -o <output_binary> [-s <source_dir>...] [--emit-llvm <file>] [--threads <N>] [--release] [--debug] [--quiet]');
			Process:exit(status: 2);
		});

		if({ !fileExists(path: inputPath) }, {
			Stderr:line('Error: Source file not found: ' . inputPath);
			Process:exit(status: 1);
		});

		local String is source: fileRead(path: inputPath, default: '');
		local Int is specLines: source:lines():length();
		local Int is t0: Process:clockMs();
		local Int is loadMs: 0;
		local Int is checkMs: 0;
		local Int is genMs: 0;
		local Int is ccMs: -1;
		local CompilationReport is report: CompilationReport:init(quiet: quiet);

		local String is emitLlvmPath: args:getString(key: 'emit-llvm', default: '');
		local String is emitRuntimePath: args:getString(key: 'emit-runtime', default: '');
		if({ emitRuntimePath != '' }, {
			local RuntimePrelude is rpOut: RuntimePrelude:init();
			fileWrite(path: emitRuntimePath, content: rpOut:emitRuntime());
		});

		if({ outputPath == '' && emitLlvmPath == '' && emitRuntimePath == '' }, {
			Stderr:line('Error: Missing output binary path (-o <output_binary>)');
			Process:exit(status: 2);
		});
		if({ outputPath == '' && emitLlvmPath == '' && emitRuntimePath != '' }, {
			return;
		});

		local Int is exitCode: 0;
		ThreadScope:open(body: local Function(ThreadScope is scope){
			Process:monitorStart(scope: scope);

			# 1. Multi-file module loading and dependency resolution.
			local Int is loadT0: Process:clockMs();
			local Loader is loader: Loader:init();
			sourceDirs:each(action: local Function(String is d){
				loader:addSourceDir(dir: d);
			});
			local ProgramNode is program: loader:loadProgram(rootPath: inputPath);
			loadMs: Process:clockMs() - loadT0;

			local Int is classCount: program:classes:length();
			local Int is methodCount: 0;
			while([Int is ci: 0], { ci < classCount }, {
				local ClassInfo is c: program:classes:get(index: ci);
				while([Int is mi: 0], { mi < c:members:length() }, {
					if({ c:members:get(index: mi):kind == MemberKind:METHOD }, {
						methodCount: methodCount + 1;
					});
					mi++;
				});
				ci++;
			});
			report:stage(n: 1, total: 4, label: 'loading packages · ' . (loader:loadedFileCount() as String) . ' files, ' . (classCount as String) . ' classes · ' . ((Process:peakMemoryKb() / 1024) as String) . ' MB');
			if({ loader:getParseErrors():length() > 0 }, {
				Stderr:line('Compilation errors encountered during loading:');
				local Array of String is loadErrors: loader:getParseErrors();
				loadErrors:each(action: local Function(String is err){
					Stderr:line(err);
				});
				Stderr:line('Compilation aborted due to syntax or load errors.');
				loader:cleanup();
				Process:monitorStop();
				exitCode: 1;
				return;
			});
			loader:cleanup();

			# 2. Semantic static type checking.
			local Int is checkT0: Process:clockMs();
			local TypeChecker is tc: TypeChecker:init();
			local [TypeError] is typeErrors: tc:checkProgramScoped(program: program, scope: scope, threads: threadCount);
			checkMs: Process:clockMs() - checkT0;
			local Int is errCount: typeErrors:length();
			tc:cleanup();
			report:stage(n: 2, total: 4, label: 'type checking · ' . (errCount as String) . ' errors · ' . ((Process:peakMemoryKb() / 1024) as String) . ' MB');
			if({ errCount > 0 }, {
				Stderr:line('Type errors encountered during compilation:');
				local Int is tei: 0;
				while({ tei < errCount }, {
					Stderr:line(typeErrors:get(index: tei):toString());
					tei++;
				});
				Stderr:line('Compilation aborted due to type errors.');
				Process:monitorStop();
				exitCode: 1;
				return;
			});

			# 3. Entry class — scoped to the ROOT FILE's classes.
			if({ classCount == 0 }, {
				Stderr:line('Error: No class definitions found in source file.');
				Process:monitorStop();
				exitCode: 1;
				return;
			});
			local [ClassInfo] is rootClasses: [];
			local Int is rci: 0;
			while({ rci < program:classes:length() }, {
				local ClassInfo is c: program:classes:get(index: rci);
				if({ c:sourceFile == inputPath }, {
					rootClasses:push(item: c);
				});
				rci++;
			});
			if({ rootClasses:length() == 0 }, {
				Stderr:line('Error: No entry class found in ' . inputPath . '; a runnable program declares at least one non-enum class.');
				Process:monitorStop();
				exitCode: 1;
				return;
			});
			local String is entryName: '';
			local ClassInfo is entryClassInfo: rootClasses:get(index: 0);
			while([Int is eci: 0], { entryName == '' && eci < rootClasses:length() }, {
				local ClassInfo is c: rootClasses:get(index: eci);
				while([Int is mi: 0], { entryName == '' && mi < c:members:length() }, {
					local Member is m: c:members:get(index: mi);
					if({ m:name == 'init' && m:kind == MemberKind:METHOD && m:params:length() == 1 }, {
						local Parameter is p: m:params:get(index: 0);
						if({ p:paramType:name == 'Map' }, {
							entryName: c:name;
							entryClassInfo: c;
						});
					});
					mi++;
				});
				eci++;
			});
			if({ entryName == '' }, {
				while([Int is eci: 0], { entryName == '' && eci < rootClasses:length() }, {
					local ClassInfo is c: rootClasses:get(index: eci);
					if({ c:baseClass != 'Enum' }, {
						entryName: c:name;
						entryClassInfo: c;
					});
					eci++;
				});
			});
			if({ entryName == '' }, {
				Stderr:line('Error: No entry class found in ' . inputPath . '; a runnable program declares at least one non-enum class.');
				Process:monitorStop();
				exitCode: 1;
				return;
			});

			:entryInitOwner: '';
			:entryInitParams: 0;
			:entryInitFirstParam: '';
			:entryInitOverloadIndex: 0;
			:entryInitTakesMap: false;
			:entryInitSawAny: false;
			local Array of String is latticeVisited: Array();
			:resolveEntryInit(c: entryClassInfo, all: program:classes, visited: latticeVisited);
			if({ :entryInitOwner == '' && :entryInitSawAny }, {
				Stderr:line("Error: Entry class '" . entryName . "' requires an init that takes 'Map of String to String' or an empty init.");
				Process:monitorStop();
				exitCode: 1;
				return;
			});

			# 4. LLVM IR code generation over the FULL loaded class set.
			local Int is llvmGenT0: Process:clockMs();
			local IrBuilder is irb: IrBuilder:init();
			irb:entryInitOwner: :entryInitOwner;
			irb:entryInitOverloadIndex: :entryInitOverloadIndex;
			irb:entryInitTakesMap: :entryInitTakesMap;
			local IrModule is irMod: irb:buildProgram(program: program, entryClass: entryName);
			if({ irb:errors:length() > 0 }, {
				Stderr:line('Code generation errors encountered during compilation:');
				irb:errors:each(action: local Function(Error is err){
					Stderr:line(err:toString());
				});
				Stderr:line('Compilation aborted due to code generation errors.');
				Process:monitorStop();
				exitCode: 1;
				return;
			});
			if({ !args:has(key: 'no-opt') }, {
				local OptimizerPipeline is optPipe: OptimizerPipeline:init();
				optPipe:run(mod: irMod);
			});
			local LlvmEmitter is emitter: LlvmEmitter:init();
			emitter:debugMode: debugMode;
			local Boolean is useShards: emitLlvmPath == '' && outputPath != '' && outputPath != '/dev/null' && outputPath != 'nul' && outputPath != 'NUL' && threadCount > 1 && irMod:functions:length() >= 32;
			local Int is llLines: 0;
			local String is tempLlPath: emitLlvmPath;
			local Array of String is shardLlPaths: Array();
			if({ useShards }, {
				local Int is nShards: if({ threadCount > 8 }, { 8 }, { threadCount });
				local Array of String is shardTexts: emitter:emitShardsScoped(mod: irMod, scope: scope, shards: nShards);
				genMs: Process:clockMs() - llvmGenT0;
				local String is shardPrefix: Uri:systemTempDir() . '/_spec_shard_' . (Process:getPid() as String) . '_';
				local Int is si: 0;
				while({ si < shardTexts:length() }, {
					local String is sText: shardTexts:get(index: si, default: '');
					llLines: llLines + sText:countByte(byteVal: 10);
					local String is sPath: shardPrefix . (si as String) . '.ll';
					fileWrite(path: sPath, content: sText);
					shardLlPaths:add(item: sPath);
					si++;
				});
			}, {
				local String is llText: emitter:emitModuleScoped(mod: irMod, scope: scope, threads: threadCount);
				genMs: Process:clockMs() - llvmGenT0;
				llLines: llText:countByte(byteVal: 10);
				if({ tempLlPath == '' }, {
					tempLlPath: Uri:systemTempDir() . '/_spec_stage_' . (Process:getPid() as String) . '.ll';
				});
				fileWrite(path: tempLlPath, content: llText);
			});
			report:stage(n: 3, total: 4, label: 'generating LLVM IR · ' . (llLines as String) . ' lines · ' . ((Process:peakMemoryKb() / 1024) as String) . ' MB');

			if({ outputPath == '' || outputPath == '/dev/null' || outputPath == 'nul' || outputPath == 'NUL' }, {
				if({ emitLlvmPath == '' }, { fileRemove(path: tempLlPath, onError: local Function(SpecError of FileError is e){}); });
				Process:monitorStop();
				report:summary(inputPath: inputPath, outputPath: emitLlvmPath, classCount: classCount, methodCount: methodCount, specLines: specLines, cLines: llLines, totalMs: Process:clockMs() - t0, loadMs: loadMs, checkMs: checkMs, genMs: genMs, ccMs: -1, peakKb: Process:monitorPeakMemKb(), avgMemKb: Process:monitorAvgMemKb(), avgCpuPct: Process:monitorAvgCpuPct(), peakCpuPct: Process:monitorPeakCpuPct(), binKb: -1);
				return;
			});

			# 5. Ensure spec_runtime.o exists and compile/link via clang.
			local String is cacheDir: Uri:runtimeCacheDir();
			local String is runtimeC: cacheDir . '/spec_runtime.c';
			local String is runtimeO: cacheDir . '/spec_runtime.o';
			if({ args:has(key: 'clean-cache') }, {
				fileRemove(path: runtimeO, onError: local Function(SpecError of FileError is e){});
				fileRemove(path: runtimeC, onError: local Function(SpecError of FileError is e){});
			});
			local RuntimePrelude is rp: RuntimePrelude:init();
			local String is rtText: rp:emitRuntime();
			if({ !fileExists(path: runtimeO) || Dir:fileSize(path: runtimeC) != rtText:length() || args:has(key: 'clean-cache') }, {
				Process:execute(command: 'mkdir', args: Array(['-p', cacheDir]));
				if({ !fileWrite(path: runtimeC, content: rtText) }, {
					cacheDir: Uri:systemTempDir() . '/spec_cache/runtime';
					runtimeC: cacheDir . '/spec_runtime.c';
					runtimeO: cacheDir . '/spec_runtime.o';
					Process:execute(command: 'mkdir', args: Array(['-p', cacheDir]));
					fileWrite(path: runtimeC, content: rtText);
				});
				Process:execute(command: 'clang', args: Array(['-O2', '-c', runtimeC, '-o', runtimeO, '-pthread']));
			});

			if({ Process:osName() == 'linux' }, {
				local Boolean is usesAudio: false;
				local Int is aci: 0;
				while({ !usesAudio && aci < program:classes:length() }, {
					if({ program:classes:get(index: aci):name == 'Audio' }, {
						usesAudio: true;
					});
					aci++;
				});
				if({ usesAudio && !fileExists(path: '/usr/include/alsa/asoundlib.h') }, {
					Stderr:line('Notice: Program uses base:audio. If ALSA development headers are missing, please install:\n  Debian/Ubuntu: sudo apt-get install libasound2-dev\n  Fedora/RHEL:   sudo dnf install alsa-lib-devel');
				});
			});

			local String is optFlag: if({ debugMode }, { '-O0' }, { '-O2' });
			local Array of String is llOsFlags: OsLinkFlags:init(noPie: true):flags();
			local Int is llCcT0: Process:clockMs();
			local Int is llStat: 0;
			if({ useShards }, {
				local Array of String is shardObjPaths: Array();
				local [Task of Int] is ccTasks: [];
				local Int is ci: 0;
				while({ ci < shardLlPaths:length() }, {
					local String is sLl: shardLlPaths:get(index: ci, default: '');
					local String is sObj: sLl . '.o';
					shardObjPaths:add(item: sObj);
					local Array of String is cArgs: Array([optFlag, '-Wno-override-module', '-c', sLl, '-o', sObj]);
					if({ debugMode }, {
						cArgs:add(item: '-g');
					});
					local Task of Int is ct: scope:spawn(task: local Function of Int(){
						return Process:execute(command: 'clang', args: cArgs);
					});
					ccTasks:push(item: ct);
					ci++;
				});
				local Int is wi: 0;
				while({ wi < ccTasks:length() }, {
					local Int is stCode: ccTasks:get(index: wi):await();
					if({ stCode != 0 && llStat == 0 }, {
						llStat: stCode;
					});
					wi++;
				});
				shardLlPaths:each(action: local Function(String is sp){
					fileRemove(path: sp, onError: local Function(SpecError of FileError is e){});
				});
				if({ llStat == 0 }, {
					local Array of String is linkArgs: Array();
					shardObjPaths:each(action: local Function(String is op){
						linkArgs:add(item: op);
					});
					linkArgs:add(item: runtimeO);
					linkArgs:add(item: '-o');
					linkArgs:add(item: outputPath);
					linkArgs:add(item: '-pthread');
					linkArgs:add(item: '-lm');
					llOsFlags:each(action: local Function(String is fl){
						linkArgs:add(item: fl);
					});
					if({ debugMode }, {
						linkArgs:add(item: '-g');
					});
					llStat: Process:execute(command: 'clang', args: linkArgs);
				});
				shardObjPaths:each(action: local Function(String is op){
					fileRemove(path: op, onError: local Function(SpecError of FileError is e){});
				});
			}, {
				local Array of String is llArgs: Array([optFlag, '-Wno-override-module', tempLlPath, runtimeO, '-o', outputPath, '-pthread', '-lm']);
				llOsFlags:each(action: local Function(String is fl){
					llArgs:add(item: fl);
				});
				if({ debugMode }, {
					llArgs:add(item: '-g');
				});
				llStat: Process:execute(command: 'clang', args: llArgs);
				if({ emitLlvmPath == '' }, { fileRemove(path: tempLlPath, onError: local Function(SpecError of FileError is e){}); });
			});
			ccMs: Process:clockMs() - llCcT0;
			if({ llStat != 0 }, {
				fileRemove(path: runtimeO, onError: local Function(SpecError of FileError is e){});
				fileRemove(path: runtimeC, onError: local Function(SpecError of FileError is e){});
				Process:monitorStop();
				Stderr:line('Error: clang failed on LLVM IR with exit status ' . (llStat as String));
				exitCode: 1;
				return;
			});

			local Int is binBytes: Dir:fileSize(path: outputPath);
			report:stage(n: 4, total: 4, label: 'compiling (clang) · ' . (ccMs as String) . 'ms');
			Process:monitorStop();
			report:summary(inputPath: inputPath, outputPath: outputPath, classCount: classCount, methodCount: methodCount, specLines: specLines, cLines: llLines, totalMs: Process:clockMs() - t0, loadMs: loadMs, checkMs: checkMs, genMs: genMs, ccMs: ccMs, peakKb: Process:monitorPeakMemKb(), avgMemKb: Process:monitorAvgMemKb(), avgCpuPct: Process:monitorAvgCpuPct(), peakCpuPct: Process:monitorPeakCpuPct(), binKb: binBytes);
		});
		if({ exitCode != 0 }, {
			Process:exit(status: exitCode);
		});
	}

	## Walks the inheritance lattice from [c] and classifies every init
	## overload the entry could construct through. Preference: an init
	## that takes the command-line 'Map of String to String' wins over
	## an empty init wherever each sits on the lattice; within a
	## preference class the first in visit order wins. Overloads that
	## are neither — any other required parameters — are not
	## constructible from the command line and are skipped. Depth-first
	## over baseClasses in declaration order, with a visited set as the
	## cycle guard: a revisit terminates the branch, never a depth
	## count. Results land in the driver's entry-init probe fields.
	##
	## @param c: The class to probe (the entry class).
	## @param all: The full loaded class set (lattice preloads included).
	## @param visited: Names already probed on this walk.
	Function is resolveEntryInit(ClassInfo is c, [ClassInfo] is all, Array of String is visited){
		if({ visited:indexOf(search: c:name, default: -1) >= 0 || :entryInitTakesMap }, {
			return;
		});
		if({ c:name == 'Loadable' || c:name == 'Class' || c:name == 'Stringable' || c:name == 'Any' || c:name == 'Enum' }, {
			return;
		});
		visited:add(item: c:name);
		local Int is initSeen: 0;
		while([Int is mi: 0], { mi < c:members:length() }, {
			local Member is m: c:members:get(index: mi);
			if({ m:name == 'init' && m:kind == MemberKind:METHOD }, {
				:entryInitSawAny: true;
				local Int is arity: m:params:length();
				local String is first: '';
				if({ arity == 1 }, {
					local Parameter is p: m:params:get(index: 0);
					first: p:paramType:name;
				});
				if({ arity == 1 && first == 'Map' && !:entryInitTakesMap }, {
					# The argv-capable form: overrides any empty choice.
					:entryInitOwner: c:qualifiedName();
					:entryInitParams: arity;
					:entryInitFirstParam: first;
					:entryInitOverloadIndex: initSeen;
					:entryInitTakesMap: true;
				}, {
					if({ arity == 0 && :entryInitOwner == '' }, {
						# Empty fallback: provisional until an argv-capable
						# init appears further along the lattice.
						:entryInitOwner: c:qualifiedName();
						:entryInitParams: arity;
						:entryInitFirstParam: first;
						:entryInitOverloadIndex: initSeen;
					});
				});
				# The declaration-order index among the owner's init
				# overloads rides the chosen member: the C symbol for an
				# overload is the owner's base symbol with an (idx+1)
				# suffix, first overload unsuffixed — the generator's
				# overloadIndexOf counts exactly this order.
				initSeen: initSeen + 1;
			});
			mi++;
		});
		if({ !:entryInitTakesMap }, {
			c:baseClasses:each(action: local Function(String is baseName){
				local Int is ai: 0;
				while({ !:entryInitTakesMap && ai < all:length() }, {
					local ClassInfo is cand: all:get(index: ai);
					if({ cand:name == baseName }, {
						:resolveEntryInit(c: cand, all: all, visited: visited);
					});
					ai++;
				});
			});
		});
	}
}
