#! Package base:compiler:driver
#! The compiler driver: CLI orchestration over load, check, generate, cc.
##
## Coordinates the Loader (multi-file package resolution), the Linter,
## the TypeChecker, and the CodeGenerator, and prints progress through
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
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'checker', TypeChecker],
		['base', 'compiler', 'linter', Linter],
		['base', 'compiler', 'linter', LintIssue],
		['base', 'compiler', 'loader', Loader],
		['base', 'compiler', 'driver', CompilationReport],
		['base', 'compiler', 'gen', CodeGenerator],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator'],
		['base', 'sys', as Output()],
		['base', 'sys', as Stderr()]
,
		['base', 'compiler', Error]
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
		Conditional:if(check: { inputPath == '' }, then: {
			inputPath: args:getString(key: 'input', default: '');
		});
		Conditional:if(check: { inputPath == '' }, then: {
			inputPath: args:getString(key: 'lint', default: '');
		});
		local String is outputPath: args:getString(key: 'o', default: '');
		Conditional:if(check: { outputPath == '' }, then: {
			outputPath: args:getString(key: 'output', default: '');
		});
		local Boolean is lintMode: args:has(key: 'lint');
		local Boolean is auditMode: args:has(key: 'audit');
		local Boolean is quiet: args:has(key: 'quiet');
		local String is threadsStr: args:getString(key: 'threads', default: '');
		Conditional:if(check: { threadsStr == '' }, then: {
			threadsStr: args:getString(key: 'j', default: '');
		});
		local Int is threadCount: 2;
		Conditional:if(check: { threadsStr != '' }, then: {
			threadCount: threadsStr:parseInt(base: 10, default: 2);
			Conditional:if(check: { threadCount < 1 }, then: {
				threadCount: 1;
			});
		});
		Conditional:if(check: { inputPath == '' }, then: {
			Output:line('Spec Compiler (Pure Spec)');
			Stderr:line('Usage: spec -i <input.spec> -o <output_binary> [--emit-c <file>] [--threads <N>] [--lint] [--audit] [--quiet]');
			Process:exit(status: 2);
		});

		Conditional:if(check: { !fileExists(path: inputPath) }, then: {
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

		# 1. Lint mode: scan, parse, report standards issues; no emission.
		Conditional:if(check: { lintMode }, then: {
			local Lexer is lexer: Lexer:init(source: source);
			local Parser is parser: Parser:init(tokens: []);
			parser:setLexer(lexer: lexer);
			parser:setSourceFile(file: inputPath);
			local ProgramNode is lintProgram: parser:parseProgram();
			Conditional:if(check: { lexer:hasErrors() }, then: {
				Stderr:line('Lexical errors encountered during linting:');
				local Array of Error is lexErrors: lexer:getErrors();
				lexErrors:each(action: local Function(Error is err){
					Stderr:line('  [' . inputPath . '] ' . err:toString());
				});
				Process:exit(status: 1);
			});
			Conditional:if(check: { parser:hasErrors() }, then: {
				Stderr:line('Syntax errors encountered during linting:');
				local Array of Error is parseErrs: parser:getErrors();
				parseErrs:each(action: local Function(Error is err){
					Stderr:line(err:toString());
				});
				Process:exit(status: 1);
			});

			local Linter is linter: Linter:init();
			local Array of LintIssue is issues: linter:lint(source: source, program: lintProgram);
			linter:report(filePath: inputPath, issues: issues);
			return;
		});

		local String is emitCPath: args:getString(key: 'c', default: '');
		Conditional:if(check: { emitCPath == '' }, then: {
			emitCPath: args:getString(key: 'emit-c', default: '');
		});

		Conditional:if(check: { !auditMode && outputPath == '' && emitCPath == '' }, then: {
			Stderr:line('Error: Missing output binary path (-o <output_binary>)');
			Process:exit(status: 2);
		});

		# 2. Multi-file module loading and dependency resolution.
		local Int is loadT0: Process:clockMs();
		local Loader is loader: Loader:init();
		local ProgramNode is program: loader:loadProgram(rootPath: inputPath);
		loadMs: Process:clockMs() - loadT0;

		local Int is classCount: program:classes:length();
		local Int is methodCount: 0;
		program:classes:each(action: local Function(ClassInfo is c){
			c:members:each(action: local Function(Member is m){
				Conditional:if(check: { m:kind == MemberKind:METHOD }, then: {
					methodCount: methodCount + 1;
				});
			});
		});
		report:stage(n: 1, total: 4, label: 'loading packages · ' . (loader:loadedFileCount() as String) . ' files, ' . (classCount as String) . ' classes · ' . ((Process:peakMemoryKb() / 1024) as String) . ' MB');
		Conditional:if(check: { loader:getParseErrors():length() > 0 }, then: {
			Stderr:line('Compilation errors encountered during loading:');
			local Array of String is loadErrors: loader:getParseErrors();
			loadErrors:each(action: local Function(String is err){
				Stderr:line(err);
			});
			Stderr:line('Compilation aborted due to syntax or load errors.');
			Process:exit(status: 1);
		});
		loader:cleanup();

		# 2.5 Instance-model worklist audit (Phase 0.5): with the
		# full program loaded, report class-name-receiver call sites. Purely
		# informational; always exits 0.
		Conditional:if(check: { auditMode }, then: {
			local Linter is auditor: Linter:init();
			local Array of LintIssue is auditIssues: auditor:auditProgram(program: program);
			auditor:auditReport(filePath: inputPath, issues: auditIssues);
			return;
		});

		# 3. Semantic static type checking.
		local Int is checkT0: Process:clockMs();
		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is typeErrors: tc:checkProgram(program: program);
		checkMs: Process:clockMs() - checkT0;
		local Int is errCount: typeErrors:length();
		tc:cleanup();
		report:stage(n: 2, total: 4, label: 'type checking · ' . (errCount as String) . ' errors · ' . ((Process:peakMemoryKb() / 1024) as String) . ' MB');
		Conditional:if(check: { errCount > 0 }, then: {
			Stderr:line('Type errors encountered during compilation:');
			typeErrors:each(action: local Function(TypeError is err){
				Stderr:line(err:toString());
			});
			Stderr:line('Compilation aborted due to type errors.');
			Process:exit(status: 1);
		});

		# 4. Entry class — scoped to the ROOT FILE's classes. The loader
		# preloads the root lattice (Any, Loadable, String, ...) into the
		# program set ahead of user code, so an unscoped fallback would
		# select a lattice class and emit a main that constructs Any.
		# The parser stamps every loaded class with its declaring file,
		# and the root file is this compile's input path.
		Conditional:if(check: { classCount == 0 }, then: {
			Stderr:line('Error: No class definitions found in source file.');
			Process:exit(status: 1);
		});
		local Array of ClassInfo is rootClasses: [];
		program:classes:each(action: local Function(ClassInfo is c){
			Conditional:if(check: { c:sourceFile == inputPath }, then: {
				rootClasses:add(item: c);
			});
		});
		Conditional:if(check: { rootClasses:length() == 0 }, then: {
			Stderr:line('Error: No entry class found in ' . inputPath . '; a runnable program declares at least one non-enum class.');
			Process:exit(status: 1);
		});
		local String is entryName: '';
		local ClassInfo is entryClassInfo: rootClasses:get(index: 0);
		rootClasses:each(action: local Function(ClassInfo is c){
			Conditional:if(check: { entryName == '' }, then: {
				c:members:each(action: local Function(Member is m){
					Conditional:if(check: { entryName == '' && m:name == 'init' && m:kind == MemberKind:METHOD && m:params:length() == 1 }, then: {
						local Parameter is p: m:params:get(index: 0);
						Conditional:if(check: { p:paramType:name == 'Map' }, then: {
							entryName: c:name;
							entryClassInfo: c;
						});
					});
				});
			});
		});
		Conditional:if(check: { entryName == '' }, then: {
			rootClasses:each(action: local Function(ClassInfo is c){
				Conditional:if(check: { entryName == '' && c:baseClass != 'Enum' }, then: {
					entryName: c:name;
					entryClassInfo: c;
				});
			});
		});
		Conditional:if(check: { entryName == '' }, then: {
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
		Conditional:if(check: { self:entryInitOwner == '' && self:entryInitSawAny }, then: {
			Stderr:line("Error: Entry class '" . entryName . "' requires an init that takes 'Map of String to String' or an empty init.");
			Process:exit(status: 1);
		});

		local String is tempCPath: emitCPath;
		Conditional:if(check: { tempCPath == '' }, then: {
			tempCPath: fileTemp(template: '/tmp/_spec_stage_XXXXXX.c');
			Conditional:if(check: { tempCPath == '' }, then: {
				tempCPath: '/tmp/_spec_stage_' . (Process:getPid() as String) . '.c';
			});
		});

		# 5. C11 code generation over the FULL loaded class set streamed to disk.
		local CodeGenerator is cg: CodeGenerator:init();
		cg:genThreads: threadCount;
		cg:entryInitOwner: self:entryInitOwner;
		cg:entryInitOverloadIndex: self:entryInitOverloadIndex;
		cg:entryInitTakesArgs: self:entryInitTakesMap;
		cg:registerProgram(classes: program:classes);
		local Int is genT0: Process:clockMs();
		local Int is cLines: cg:generateProgramToFile(program: program, entryClass: entryName, filePath: tempCPath);
		genMs: Process:clockMs() - genT0;
		Conditional:if(check: { cLines < 0 }, then: {
			Stderr:line('Error: Failed to write intermediate C code to ' . tempCPath);
			Process:exit(status: 1);
		});
		report:stage(n: 3, total: 4, label: 'generating C · ' . (cLines as String) . ' lines · ' . ((Process:peakMemoryKb() / 1024) as String) . ' MB');

		Conditional:if(check: { outputPath == '' }, then: {
			Process:monitorStop();
			report:summary(inputPath: inputPath, outputPath: emitCPath, classCount: classCount, methodCount: methodCount, specLines: specLines, cLines: cLines, totalMs: Process:clockMs() - t0, loadMs: loadMs, checkMs: checkMs, genMs: genMs, ccMs: -1, peakKb: Process:monitorPeakMemKb(), avgMemKb: Process:monitorAvgMemKb(), avgCpuPct: Process:monitorAvgCpuPct(), peakCpuPct: Process:monitorPeakCpuPct(), binKb: -1);
			return;
		});

		# 6. GCC backend compile.
		local Array of String is gccArgs: ['-O2', '-w', tempCPath, '-o', outputPath, '-pthread', '-lm'];
		local Int is ccT0: Process:clockMs();
		local Int is gccStatus: Process:execute(command: 'gcc', args: gccArgs);
		ccMs: Process:clockMs() - ccT0;
		Conditional:if(check: { emitCPath == '' }, then: {
			fileRemove(path: tempCPath);
		});
		Conditional:if(check: { gccStatus != 0 }, then: {
			Process:monitorStop();
			Stderr:line('Error: Backend C compiler (gcc) failed with exit status ' . (gccStatus as String));
			Process:exit(status: 1);
		});

		local Int is binBytes: Dir:fileSize(path: outputPath);
		report:stage(n: 4, total: 4, label: 'compiling (gcc) · ' . (ccMs as String) . 'ms');
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
		Conditional:if(check: { visited:indexOf(search: c:name, default: -1) >= 0 || self:entryInitTakesMap }, then: {
			return;
		});
		visited:add(item: c:name);
		local Int is initSeen: 0;
		c:members:each(action: local Function(Member is m){
			Conditional:if(check: { m:name == 'init' && m:kind == MemberKind:METHOD }, then: {
				self:entryInitSawAny: true;
				local Int is arity: m:params:length();
				local String is first: '';
				Conditional:if(check: { arity == 1 }, then: {
					local Parameter is p: m:params:get(index: 0);
					first: p:paramType:name;
				});
				Conditional:if(check: { arity == 1 && first == 'Map' && !self:entryInitTakesMap }, then: {
					# The argv-capable form: overrides any empty choice.
					self:entryInitOwner: c:qualifiedName();
					self:entryInitParams: arity;
					self:entryInitFirstParam: first;
					self:entryInitOverloadIndex: initSeen;
					self:entryInitTakesMap: true;
				}, else: {
					Conditional:if(check: { arity == 0 && self:entryInitOwner == '' }, then: {
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
		Conditional:if(check: { !self:entryInitTakesMap }, then: {
			c:baseClasses:each(action: local Function(String is baseName){
				all:each(action: local Function(ClassInfo is cand){
					Conditional:if(check: { !self:entryInitTakesMap && cand:name == baseName }, then: {
						self:resolveEntryInit(c: cand, all: all, visited: visited);
					});
				});
			});
		});
	}
}
