#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, Linter, TypeChecker, CodeGenerator, and Driver.

## Main compiler driver coordinating file loading, lexing, parsing, type checking, and code generation.
Class is Driver{

	replace Array of String is using: [
		base:io:*,
		base:sys:Process,
		base:sysinternal:Dir,
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:reflect:ClassInfo,
		compiler:Token,
		compiler:Lexer,
		compiler:Parser,
		compiler:Linter,
		compiler:TypeChecker,
		compiler:CBackendUtils,
		compiler:RuntimePrelude,
		compiler:DeclarationGenerator,
		compiler:BuiltinCallGenerator,
		compiler:CodeGenerator,
		compiler:Loader
	];

	replace Function is init(Map of String to String is args){
		local String is inputPath: args:getString(key: 'i', default: '');
		if (inputPath == '') {
			inputPath: args:getString(key: 'input', default: '');
		}
		if (inputPath == '') {
			inputPath: args:getString(key: 'lint', default: '');
		}
		local String is outputPath: args:getString(key: 'o', default: '');
		if (outputPath == '') {
			outputPath: args:getString(key: 'output', default: '');
		}
		local Boolean is lintMode: args:has(key: 'lint');
		local Boolean is quiet: args:has(key: 'quiet');
		local String is gcMode: args:getString(key: 'gc', default: '');
		if (gcMode != '' && gcMode != 'boehm') {
			error:line('Error: Unsupported GC mode \'' . gcMode . '\'. Supported modes: boehm');
			Process:exit(status: 1);
		}

		if (inputPath == '') {
			output:line('Spec Compiler v0.000.014 (Pure Spec - Self-Hosted)');
			error:line('Usage: spec -i <input.spec> -o <output_binary> [--lint] [--gc=boehm]');
			Process:exit(status: 2);
		}

		if (!File:exists(path: inputPath)) {
			error:line('Error: Source file not found: ' . inputPath);
			Process:exit(status: 1);
		}

		local String is source: File:read(path: inputPath, default: '');
		local Int is specLines: source:lines():length();
		local Int is t0: Process:clockMs();
		local Int is loadMs: 0;
		local Int is checkMs: 0;
		local Int is genMs: 0;
		local Int is ccMs: 0;

		# 1. Linter Mode Check
		if (lintMode) {
			local Lexer is lexer: Lexer:init(source: source);
			local Array of Token is tokens: lexer:tokenize();
			if (lexer:hasErrors()) {
				error:line('Lexical errors encountered during linting:');
				lexer:getErrors():each(action: local Function(String is err){
					error:line('  [' . inputPath . '] ' . err);
				});
				Process:exit(status: 1);
			}
			local Parser is parser: Parser:init(tokens: tokens);
			parser:setSourceFile(file: inputPath);
			local ProgramNode is lintProgram: parser:parseProgram();
			if (parser:hasErrors()) {
				error:line('Syntax errors encountered during linting:');
				parser:getErrors():each(action: local Function(String is err){
					error:line(err);
				});
				Process:exit(status: 1);
			}

			local Linter is linter: Linter:init();
			local Array of LintIssue is issues: linter:lint(source: source, program: lintProgram);
			linter:report(filePath: inputPath, issues: issues);
			return;
		}

		local String is emitCPath: args:getString(key: 'c', default: '');
		if (emitCPath == '') {
			emitCPath: args:getString(key: 'emit-c', default: '');
		}

		if (outputPath == '' && emitCPath == '') {
			error:line('Error: Missing output binary path (-o <output_binary>)');
			Process:exit(status: 2);
		}

		# 2. Multi-File Module Loading & Dependency Resolution
		local Int is loadT0: Process:clockMs();
		local Loader is loader: Loader:init();
		local ProgramNode is program: loader:loadProgram(rootPath: inputPath);
		loadMs: Process:clockMs() - loadT0;

		# Compilation metrics: class and method totals across the program.
		local Int is classCount: program:getClasses():length();
		local Int is methodCount: 0;
		program:getClasses():each(action: local Function(ClassInfo is c){
			c:getMembers():each(action: local Function(Member is m){
				if (m:getKind() == 'METHOD') {
					methodCount: methodCount + 1;
				}
			});
		});
		if (!quiet) {
			output:line('  [1/4] loading packages · ' . loader:loadedFileCount() . ' files, ' . classCount . ' classes');
		}
		if (loader:getParseErrors():length() > 0) {
			error:line('Compilation errors encountered during loading:');
			loader:getParseErrors():each(action: local Function(String is err){
				error:line(err);
			});
			error:line('Compilation aborted due to syntax or load errors.');
			Process:exit(status: 1);
		}

		# 4. Semantic Static Type Checking
		local Int is checkT0: Process:clockMs();
		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is typeErrors: tc:checkProgram(program: program);
		checkMs: Process:clockMs() - checkT0;
		if (!quiet) {
			output:line('  [2/4] type checking · ' . typeErrors:length() . ' errors');
		}
		if (typeErrors:length() > 0) {
			error:line('Type errors encountered during compilation:');
			typeErrors:each(action: local Function(TypeError is err){
				error:line(err:toString());
			});
			error:line('Compilation aborted due to type errors.');
			Process:exit(status: 1);
		}

		# 5. Determine Entry ClassInfo
		if (program:getClasses():length() == 0) {
			error:line('Error: No class definitions found in source file.');
			Process:exit(status: 1);
		}

		local String is entryName: '';
		program:getClasses():each(action: local Function(ClassInfo is c){
			if (entryName == '') {
				c:getMembers():each(action: local Function(Member is m){
					if (entryName == '' && m:getName() == 'init' && m:getParameters():length() == 1) {
						local Parameter is p: m:getParameters():get(index: 0);
						if (p:getType():getName() == 'Map') {
							entryName: c:getName();
						}
					}
				});
			}
		});
		if (entryName == '') {
			program:getClasses():each(action: local Function(ClassInfo is c){
				if (entryName == '' && c:getBaseClass() != 'Enum') {
					entryName: c:getName();
				}
			});
		}
		if (entryName == '') {
			local ClassInfo is firstClass: program:getClasses():get(index: 0);
			entryName: firstClass:getName();
		}

		# 6. C11 Code Generation
		local CodeGenerator is cg: CodeGenerator:init();
		if (gcMode != '') {
			cg:setGcMode(mode: gcMode);
		}
		local Int is genT0: Process:clockMs();
		local String is cCode: cg:generateProgram(program: program, entryClass: entryName);
		genMs: Process:clockMs() - genT0;
		local Int is cLines: cCode:lines():length();
		if (!quiet) {
			output:line('  [3/4] generating C · ' . cLines . ' lines');
		}

		local String is tempCPath: emitCPath;
		if (tempCPath == '') {
			tempCPath: '/tmp/_spec_stage_' . Process:getPid() . '.c';
		}
		local Boolean is written: File:write(path: tempCPath, content: cCode);
		if (!written) {
			error:line('Error: Failed to write intermediate C code to ' . tempCPath);
			Process:exit(status: 1);
		}

		if (outputPath == '') {
			if (!quiet) {
				output:line('');
				output:line('  ' . inputPath . ' -> ' . emitCPath);
				output:line('  ' . classCount . ' classes · ' . methodCount . ' methods · ' . specLines . ' lines of spec -> ' . cLines . ' lines of C');
				output:line('  time ' . (Process:clockMs() - t0) . 'ms  (load ' . loadMs . ' · check ' . checkMs . ' · gen ' . genMs . ')');
				output:line('  peak memory ' . (Process:peakMemoryKb() / 1024) . ' MB');
			}
			return;
		}

		# 7. GCC C Compilation
		local Array of String is gccArgs: ['-O2', '-w', tempCPath, '-o', outputPath, '-pthread', '-lm'];
		if (gcMode == 'boehm') {
			if (File:exists(path: '/usr/lib/x86_64-linux-gnu/libgc.so.1') || File:exists(path: '/usr/lib/libgc.so.1')) {
				gccArgs:add(item: '-l:libgc.so.1');
			} else {
				gccArgs:add(item: '-lgc');
			}
		}
		local Int is ccT0: Process:clockMs();
		local Int is gccStatus: Process:execute(command: 'gcc', args: gccArgs);
		ccMs: Process:clockMs() - ccT0;
		if (emitCPath == '') {
			File:remove(path: tempCPath);
		}
		if (gccStatus != 0) {
			error:line('Error: Backend C compiler (gcc) failed with exit status ' . gccStatus);
			Process:exit(status: 1);
		}

		if (!quiet) {
			local Int is binBytes: Dir:fileSize(path: outputPath);
			output:line('  [4/4] compiling (gcc) · ' . ccMs . 'ms');
			output:line('');
			output:line('  ' . inputPath . ' -> ' . outputPath);
			output:line('  ' . classCount . ' classes · ' . methodCount . ' methods · ' . specLines . ' lines of spec -> ' . cLines . ' lines of C');
			output:line('  time ' . (Process:clockMs() - t0) . 'ms  (load ' . loadMs . ' · check ' . checkMs . ' · gen ' . genMs . ' · cc ' . ccMs . ')');
			output:line('  peak memory ' . (Process:peakMemoryKb() / 1024) . ' MB · binary ' . (binBytes / 1024) . ' KB');
		}
	}

}
