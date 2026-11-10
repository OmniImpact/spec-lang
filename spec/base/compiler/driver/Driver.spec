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
		['base', 'sysinternal', as Arena()],
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
		Conditional:if(check: { inputPath == '' }, then: {
			Output:line('Spec Compiler (Pure Spec)');
			Stderr:line('Usage: spec -i <input.spec> -o <output_binary> [--emit-c <file>] [--lint] [--audit] [--quiet]');
			Process:exit(status: 2);
		});

		Conditional:if(check: { !fileExists(path: inputPath) }, then: {
			Stderr:line('Error: Source file not found: ' . inputPath);
			Process:exit(status: 1);
		});

		# The compiler process routes its own allocations through the
		# object arena (immortal + wholesale drain at exit). User programs
		# never activate it and stay refcounted.
		Arena:activateProcessArena();

		local String is source: fileRead(path: inputPath, default: '');
		local Int is specLines: source:lines():length();
		local Int is t0: Process:clockMs();
		local Int is loadMs: 0;
		local Int is checkMs: 0;
		local Int is genMs: 0;
		local Int is ccMs: -1;
		local CompilationReport is report: CompilationReport:init(quiet: quiet);

		# 1. Lint mode: scan, parse, report standards issues; no emission.
		Conditional:if(check: { lintMode }, then: {
			local Lexer is lexer: Lexer:init(source: source);
			local Array of Token is tokens: lexer:tokenize();
			Conditional:if(check: { lexer:hasErrors() }, then: {
				Stderr:line('Lexical errors encountered during linting:');
				local Array of Error is lexErrors: lexer:getErrors();
				lexErrors:each(action: local Function(Error is err){
					Stderr:line('  [' . inputPath . '] ' . err:toString());
				});
				Process:exit(status: 1);
			});
			local Parser is parser: Parser:init(tokens: tokens);
			parser:setSourceFile(file: inputPath);
			local ProgramNode is lintProgram: parser:parseProgram();
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
		report:stage(n: 1, total: 4, label: 'loading packages · ' . (loader:loadedFileCount() as String) . ' files, ' . (classCount as String) . ' classes');
		Conditional:if(check: { loader:getParseErrors():length() > 0 }, then: {
			Stderr:line('Compilation errors encountered during loading:');
			local Array of String is loadErrors: loader:getParseErrors();
			loadErrors:each(action: local Function(String is err){
				Stderr:line(err);
			});
			Stderr:line('Compilation aborted due to syntax or load errors.');
			Process:exit(status: 1);
		});

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
		report:stage(n: 2, total: 4, label: 'type checking · ' . (typeErrors:length() as String) . ' errors');
		Conditional:if(check: { typeErrors:length() > 0 }, then: {
			Stderr:line('Type errors encountered during compilation:');
			typeErrors:each(action: local Function(TypeError is err){
				Stderr:line(err:toString());
			});
			Stderr:line('Compilation aborted due to type errors.');
			Process:exit(status: 1);
		});

		# 4. Entry class: the first with a Map-parameter init, else the
		# first non-enum, else the first class.
		Conditional:if(check: { classCount == 0 }, then: {
			Stderr:line('Error: No class definitions found in source file.');
			Process:exit(status: 1);
		});
		local String is entryName: '';
		program:classes:each(action: local Function(ClassInfo is c){
			Conditional:if(check: { entryName == '' }, then: {
				c:members:each(action: local Function(Member is m){
					Conditional:if(check: { entryName == '' && m:name == 'init' && m:kind == MemberKind:METHOD && m:params:length() == 1 }, then: {
						local Parameter is p: m:params:get(index: 0);
						Conditional:if(check: { p:paramType:name == 'Map' }, then: {
							entryName: c:name;
						});
					});
				});
			});
		});
		Conditional:if(check: { entryName == '' }, then: {
			program:classes:each(action: local Function(ClassInfo is c){
				Conditional:if(check: { entryName == '' && c:baseClass != 'Enum' }, then: {
					entryName: c:name;
				});
			});
		});
		Conditional:if(check: { entryName == '' }, then: {
			local ClassInfo is firstClass: program:classes:get(index: 0);
			entryName: firstClass:name;
		});

		# 5. C11 code generation over the FULL loaded class set.
		local CodeGenerator is cg: CodeGenerator:init();
		cg:registerProgram(classes: program:classes);
		local Int is genT0: Process:clockMs();
		local String is cCode: cg:generateProgram(program: program, entryClass: entryName);
		genMs: Process:clockMs() - genT0;
		local Int is cLines: cCode:lines():length();
		report:stage(n: 3, total: 4, label: 'generating C · ' . (cLines as String) . ' lines');

		local String is tempCPath: emitCPath;
		Conditional:if(check: { tempCPath == '' }, then: {
			tempCPath: fileTemp(template: '/tmp/_spec_stage_XXXXXX.c');
			Conditional:if(check: { tempCPath == '' }, then: {
				tempCPath: '/tmp/_spec_stage_' . (Process:getPid() as String) . '.c';
			});
		});
		local Boolean is written: fileWrite(path: tempCPath, content: cCode);
		Conditional:if(check: { !written }, then: {
			Stderr:line('Error: Failed to write intermediate C code to ' . tempCPath);
			Process:exit(status: 1);
		});

		Conditional:if(check: { outputPath == '' }, then: {
			report:summary(inputPath: inputPath, outputPath: emitCPath, classCount: classCount, methodCount: methodCount, specLines: specLines, cLines: cLines, totalMs: Process:clockMs() - t0, loadMs: loadMs, checkMs: checkMs, genMs: genMs, ccMs: -1, peakKb: Process:peakMemoryKb(), binKb: -1);
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
			Stderr:line('Error: Backend C compiler (gcc) failed with exit status ' . (gccStatus as String));
			Process:exit(status: 1);
		});

		local Int is binBytes: Dir:fileSize(path: outputPath);
		report:stage(n: 4, total: 4, label: 'compiling (gcc) · ' . (ccMs as String) . 'ms');
		report:summary(inputPath: inputPath, outputPath: outputPath, classCount: classCount, methodCount: methodCount, specLines: specLines, cLines: cLines, totalMs: Process:clockMs() - t0, loadMs: loadMs, checkMs: checkMs, genMs: genMs, ccMs: ccMs, peakKb: Process:peakMemoryKb(), binKb: binBytes);
	}
}
