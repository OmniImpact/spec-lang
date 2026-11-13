#! Package base:compiler:driver
#! The compiler driver: CLI orchestration over load, check, generate, cc.
##
## Coordinates the Loader (multi-file package resolution), the
## TypeChecker, and the CodeGenerator, and prints progress through
## the CompilationReport. This is the class the spec binary's main
## dispatches to with the parsed argument map; it IS
## the entry point of the self-hosted compiler.

Class is Driver{
	namespace: ['base', 'compiler', 'driver'];

	replace Array of Array of String is using: [
		['base', 'sys', as File()],
		['base', 'sys', Output],
		['base', 'sys', as Process()],
		['base', 'sys', as Dir()],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'checker', TypeChecker],
		['base', 'compiler', 'loader', Loader],
		['base', 'compiler', 'driver', CompilationReport],
		['base', 'compiler', 'gen', CodeGenerator],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator'],
		['base', 'sys', as Output()],
		['base', 'sys', as Stderr()]
,
		['base', 'compiler', 'ast', Parameter]
,
		['base', 'compiler', 'lexer', Token]
,
		['base', 'compiler', 'checker', TypeError],
		['base', 'sys', as Conditional()]
	];

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
		local Boolean is debugMode: args:has(key: 'debug');
		local Boolean is quiet: args:has(key: 'quiet');
		local String is threadsStr: args:getString(key: 'threads', default: '');
		if({ threadsStr == '' }, {
			threadsStr: args:getString(key: 'j', default: '');
		});
		local Int is threadCount: 2;
		if({ threadsStr != '' }, {
			threadCount: threadsStr:parseInt(base: 10, default: 2);
			if({ threadCount < 1 }, {
				threadCount: 1;
			});
		});
		if({ inputPath == '' }, {
			Output:line('Spec Compiler (Pure Spec)');
			Stderr:line('Usage: spec -i <input.spec> -o <output_binary> [--emit-c <file>] [--threads <N>] [--debug] [--quiet]');
			Process:exit(status: 2);
		});

		if({ !fileExists(path: inputPath) }, {
			Stderr:line('Error: Source file not found: ' . inputPath);
			Process:exit(status: 1);
		});

		local String is source: fileRead(path: inputPath, default: '');
		local Int is specLines: source:lines():length();
		Process:monitorStart();
		local Int is t0: Process:clockMs();
		local Int is loadMs: 0;
		local Int is checkMs: 0;
		local Int is genMs: 0;
		local Int is ccMs: -1;
		local CompilationReport is report: CompilationReport:init(quiet: quiet);

		local String is emitCPath: args:getString(key: 'c', default: '');
		if({ emitCPath == '' }, {
			emitCPath: args:getString(key: 'emit-c', default: '');
		});

		if({ outputPath == '' && emitCPath == '' }, {
			Stderr:line('Error: Missing output binary path (-o <output_binary>)');
			Process:exit(status: 2);
		});

		# 1. Multi-file module loading and dependency resolution.
		local Int is loadT0: Process:clockMs();
		local Loader is loader: Loader:init();
		local ProgramNode is program: loader:loadProgram(rootPath: inputPath);
		loadMs: Process:clockMs() - loadT0;

		local Int is classCount: program:classes:length();
		local Int is methodCount: 0;
		program:classes:each(action: local Function(ClassInfo is c){
			c:members:each(action: local Function(Member is m){
				if({ m:kind == MemberKind:METHOD }, {
					methodCount: methodCount + 1;
				});
			});
		});
		report:stage(n: 1, total: 4, label: 'loading packages · ' . (loader:loadedFileCount() as String) . ' files, ' . (classCount as String) . ' classes · ' . ((Process:peakMemoryKb() / 1024) as String) . ' MB');
		if({ loader:getParseErrors():length() > 0 }, {
			Stderr:line('Compilation errors encountered during loading:');
			local Array of String is loadErrors: loader:getParseErrors();
			loadErrors:each(action: local Function(String is err){
				Stderr:line(err);
			});
			Stderr:line('Compilation aborted due to syntax or load errors.');
			Process:exit(status: 1);
		});
		loader:cleanup();

		# 2. Semantic static type checking.
		local Int is checkT0: Process:clockMs();
		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is typeErrors: tc:checkProgram(program: program);
		checkMs: Process:clockMs() - checkT0;
		local Int is errCount: typeErrors:length();
		tc:cleanup();
		report:stage(n: 2, total: 4, label: 'type checking · ' . (errCount as String) . ' errors · ' . ((Process:peakMemoryKb() / 1024) as String) . ' MB');
		if({ errCount > 0 }, {
			Stderr:line('Type errors encountered during compilation:');
			typeErrors:each(action: local Function(TypeError is err){
				Stderr:line(err:toString());
			});
			Stderr:line('Compilation aborted due to type errors.');
			Process:exit(status: 1);
		});

		# 3. Entry class — scoped to the ROOT FILE's classes. The loader
		# preloads the root lattice (Any, Loadable, String, ...) into the
		# program set ahead of user code, so an unscoped fallback would
		# select a lattice class and emit a main that constructs Any.
		# The parser stamps every loaded class with its declaring file,
		# and the root file is this compile's input path.
		if({ classCount == 0 }, {
			Stderr:line('Error: No class definitions found in source file.');
			Process:exit(status: 1);
		});
		local Array of ClassInfo is rootClasses: [];
		program:classes:each(action: local Function(ClassInfo is c){
			if({ c:sourceFile == inputPath }, {
				rootClasses:add(item: c);
			});
		});
		if({ rootClasses:length() == 0 }, {
			Stderr:line('Error: No entry class found in ' . inputPath . '; a runnable program declares at least one non-enum class.');
			Process:exit(status: 1);
		});
		local String is entryName: '';
		local ClassInfo is entryClassInfo: rootClasses:get(index: 0);
		rootClasses:each(action: local Function(ClassInfo is c){
			if({ entryName == '' }, {
				c:members:each(action: local Function(Member is m){
					if({ entryName == '' && m:name == 'init' && m:kind == MemberKind:METHOD && m:params:length() == 1 }, {
						local Parameter is p: m:params:get(index: 0);
						if({ p:paramType:name == 'Map' }, {
							entryName: c:name;
							entryClassInfo: c;
						});
					});
				});
			});
		});
		if({ entryName == '' }, {
			rootClasses:each(action: local Function(ClassInfo is c){
				if({ entryName == '' && c:baseClass != 'Enum' }, {
					entryName: c:name;
					entryClassInfo: c;
				});
			});
		});
		if({ entryName == '' }, {
			Stderr:line('Error: No entry class found in ' . inputPath . '; a runnable program declares at least one non-enum class.');
			Process:exit(status: 1);
		});

		# The entry rule: feed the command-line args when an init can
		# take them (the argv Map), else construct through an empty
		# init, else — only when the lattice declares overloads but
		# neither form exists — a compile-time diagnostic, never a raw
		# backend-C failure. An entry with no init at all constructs
		# through its synthesized zero-arg default and is fine.
		self:entryInitOwner: '';
		self:entryInitParams: 0;
		self:entryInitFirstParam: '';
		self:entryInitOverloadIndex: 0;
		self:entryInitTakesMap: false;
		self:entryInitSawAny: false;
		local Array of String is latticeVisited: [];
		self:resolveEntryInit(c: entryClassInfo, all: program:classes, visited: latticeVisited);
		if({ self:entryInitOwner == '' && self:entryInitSawAny }, {
			Stderr:line("Error: Entry class '" . entryName . "' requires an init that takes 'Map of String to String' or an empty init.");
			Process:exit(status: 1);
		});

		local String is tempCPath: emitCPath;
		if({ tempCPath == '' }, {
			tempCPath: fileTemp(template: '/tmp/_spec_stage_XXXXXX.c');
			if({ tempCPath == '' }, {
				tempCPath: '/tmp/_spec_stage_' . (Process:getPid() as String) . '.c';
			});
		});

		# 4. C11 code generation over the FULL loaded class set streamed to disk.
		local CodeGenerator is cg: CodeGenerator:init();
		cg:genThreads: threadCount;
		# --debug: statements carry #line directives to their Spec source,
		# locals stay volatile so the optimizer cannot fold or hoist them,
		# and the backend compiles -O2 -g — full speed with inspectable
		# values, Spec-line breakpoints and stepping under gdb.
		cg:policy:debugEmission: debugMode;
		cg:entryInitOwner: self:entryInitOwner;
		cg:entryInitOverloadIndex: self:entryInitOverloadIndex;
		cg:entryInitTakesArgs: self:entryInitTakesMap;
		cg:registerProgram(classes: program:classes);
		local Int is genT0: Process:clockMs();
		local Int is cLines: cg:generateProgramToFile(program: program, entryClass: entryName, filePath: tempCPath);
		genMs: Process:clockMs() - genT0;
		if({ cLines < 0 }, {
			Stderr:line('Error: Failed to write intermediate C code to ' . tempCPath);
			Process:exit(status: 1);
		});
		report:stage(n: 3, total: 4, label: 'generating C · ' . (cLines as String) . ' lines · ' . ((Process:peakMemoryKb() / 1024) as String) . ' MB');

		if({ outputPath == '' }, {
			Process:monitorStop();
			report:summary(inputPath: inputPath, outputPath: emitCPath, classCount: classCount, methodCount: methodCount, specLines: specLines, cLines: cLines, totalMs: Process:clockMs() - t0, loadMs: loadMs, checkMs: checkMs, genMs: genMs, ccMs: -1, peakKb: Process:monitorPeakMemKb(), avgMemKb: Process:monitorAvgMemKb(), avgCpuPct: Process:monitorAvgCpuPct(), peakCpuPct: Process:monitorPeakCpuPct(), binKb: -1);
			return;
		});

		# 5. Backend C compile.
		local String is ccBin: Process:getEnv(key: 'CC', default: 'gcc');
		local Array of String is gccArgs: ['-O2', '-w', tempCPath, '-o', outputPath, '-pthread', '-lm'];
		if({ debugMode }, {
			# Debug info rides full optimization: -g costs nothing, and the
			# volatile-locals emission already keeps values inspectable.
			gccArgs:add(item: '-g');
		});
		local Int is ccT0: Process:clockMs();
		local Int is gccStatus: Process:execute(command: ccBin, args: gccArgs);
		ccMs: Process:clockMs() - ccT0;
		if({ emitCPath == '' }, {
			fileRemove(path: tempCPath);
		});
		if({ gccStatus != 0 }, {
			Process:monitorStop();
			Stderr:line('Error: Backend C compiler (' . ccBin . ') failed with exit status ' . (gccStatus as String));
			Process:exit(status: 1);
		});

		local Int is binBytes: Dir:fileSize(path: outputPath);
		report:stage(n: 4, total: 4, label: 'compiling (' . ccBin . ') · ' . (ccMs as String) . 'ms');
		Process:monitorStop();
		report:summary(inputPath: inputPath, outputPath: outputPath, classCount: classCount, methodCount: methodCount, specLines: specLines, cLines: cLines, totalMs: Process:clockMs() - t0, loadMs: loadMs, checkMs: checkMs, genMs: genMs, ccMs: ccMs, peakKb: Process:monitorPeakMemKb(), avgMemKb: Process:monitorAvgMemKb(), avgCpuPct: Process:monitorAvgCpuPct(), peakCpuPct: Process:monitorPeakCpuPct(), binKb: binBytes);
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
	Function is resolveEntryInit(ClassInfo is c, Array of ClassInfo is all, Array of String is visited){
		if({ visited:indexOf(search: c:name, default: -1) >= 0 || self:entryInitTakesMap }, {
			return;
		});
		visited:add(item: c:name);
		local Int is initSeen: 0;
		c:members:each(action: local Function(Member is m){
			if({ m:name == 'init' && m:kind == MemberKind:METHOD }, {
				self:entryInitSawAny: true;
				local Int is arity: m:params:length();
				local String is first: '';
				if({ arity == 1 }, {
					local Parameter is p: m:params:get(index: 0);
					first: p:paramType:name;
				});
				if({ arity == 1 && first == 'Map' && !self:entryInitTakesMap }, {
					# The argv-capable form: overrides any empty choice.
					self:entryInitOwner: c:qualifiedName();
					self:entryInitParams: arity;
					self:entryInitFirstParam: first;
					self:entryInitOverloadIndex: initSeen;
					self:entryInitTakesMap: true;
				}, {
					if({ arity == 0 && self:entryInitOwner == '' }, {
						# Empty fallback: provisional until an argv-capable
						# init appears further along the lattice.
						self:entryInitOwner: c:qualifiedName();
						self:entryInitParams: arity;
						self:entryInitFirstParam: first;
						self:entryInitOverloadIndex: initSeen;
					});
				});
				# The declaration-order index among the owner's init
				# overloads rides the chosen member: the C symbol for an
				# overload is the owner's base symbol with an (idx+1)
				# suffix, first overload unsuffixed — the generator's
				# overloadIndexOf counts exactly this order.
				initSeen: initSeen + 1;
			});
		});
		if({ !self:entryInitTakesMap }, {
			c:baseClasses:each(action: local Function(String is baseName){
				all:each(action: local Function(ClassInfo is cand){
					if({ !self:entryInitTakesMap && cand:name == baseName }, {
						self:resolveEntryInit(c: cand, all: all, visited: visited);
					});
				});
			});
		});
	}
}
