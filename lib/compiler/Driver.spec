#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, Linter, TypeChecker, CodeGenerator, and Driver.

## Main compiler driver coordinating file loading, lexing, parsing, type checking, and code generation.
class Driver{

	replace local Array of String is using: [
		base:io:*,
		base:sys:Process,
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:reflect:Class,
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

	replace local Function is init(Map of String to String is args){
		local String is inputPath: args:getString(key: "i", default: "");
		if (inputPath == "") {
			inputPath: args:getString(key: "input", default: "");
		}
		if (inputPath == "") {
			inputPath: args:getString(key: "lint", default: "");
		}
		local String is outputPath: args:getString(key: "o", default: "");
		if (outputPath == "") {
			outputPath: args:getString(key: "output", default: "");
		}
		local Boolean is lintMode: args:has(key: "lint");

		if (inputPath == "") {
			output:line("Spec Compiler v0.000.014 (Pure Spec - Self-Hosted)");
			output:line("Usage: spec -i <input.spec> -o <output_binary> [--lint]");
			return;
		}

		if (!File:exists(path: inputPath)) {
			output:line("Error: Source file not found: " . inputPath);
			return;
		}

		local String is source: File:read(path: inputPath, default: "");

		# 1. Linter Mode Check
		if (lintMode) {
			local Lexer is lexer: Lexer:init(source: source);
			local Array of Token is tokens: lexer:tokenize();
			local Parser is parser: Parser:init(tokens: tokens);
			parser:setSourceFile(file: inputPath);
			local ProgramNode is lintProgram: parser:parseProgram();
			if (parser:hasErrors()) {
				output:line("Syntax errors encountered during linting:");
				parser:getErrors():each(action: local Function(String is err){
					output:line(err);
				});
			}

			local Linter is linter: Linter:init();
			local Array of LintIssue is issues: linter:lint(source: source, program: lintProgram);
			linter:report(filePath: inputPath, issues: issues);
			return;
		}

		local String is emitCPath: args:getString(key: "c", default: "");
		if (emitCPath == "") {
			emitCPath: args:getString(key: "emit-c", default: "");
		}

		if (outputPath == "" && emitCPath == "") {
			output:line("Error: Missing output binary path (-o <output_binary>)");
			return;
		}

		# 2. Multi-File Module Loading & Dependency Resolution
		local Loader is loader: Loader:init();
		local ProgramNode is program: loader:loadProgram(rootPath: inputPath);
		if (loader:getParseErrors():length() > 0) {
			output:line("Syntax errors encountered during compilation:");
			loader:getParseErrors():each(action: local Function(String is err){
				output:line(err);
			});
			output:line("Compilation aborted due to syntax errors.");
			return;
		}

		# 4. Semantic Static Type Checking
		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is typeErrors: tc:checkProgram(program: program);
		if (typeErrors:length() > 0) {
			output:line("Type errors encountered during compilation:");
			typeErrors:each(action: local Function(TypeError is err){
				output:line(err:toString());
			});
			output:line("Compilation aborted due to type errors.");
			return;
		}

		# 5. Determine Entry Class
		if (program:getClasses():length() == 0) {
			output:line("Error: No class definitions found in source file.");
			return;
		}

		local String is entryName: "";
		program:getClasses():each(action: local Function(Class is c){
			c:getMembers():each(action: local Function(Member is m){
				if (m:getName() == "init" && m:getParameters():length() == 1) {
					local Parameter is p: m:getParameters():get(index: 0);
					if (p:getType():getName() == "Map") {
						entryName: c:getName();
					}
				}
			});
		});
		if (entryName == "") {
			program:getClasses():each(action: local Function(Class is c){
				if (entryName == "" && c:getBaseClass() != "Enum") {
					entryName: c:getName();
				}
			});
		}
		if (entryName == "") {
			local Class is firstClass: program:getClasses():get(index: 0);
			entryName: firstClass:getName();
		}

		# 6. C11 Code Generation
		local CodeGenerator is cg: CodeGenerator:init();
		local String is cCode: cg:generateProgram(program: program, entryClass: entryName);

		local String is tempCPath: emitCPath;
		if (tempCPath == "") {
			tempCPath: "/tmp/_spec_stage_" . Process:getPid() . ".c";
		}
		local Boolean is written: File:write(path: tempCPath, content: cCode);
		if (!written) {
			output:line("Error: Failed to write intermediate C code to " . tempCPath);
			return;
		}

		if (outputPath == "") {
			output:line("Emitted C code for " . inputPath . " -> " . emitCPath . " successfully!");
			return;
		}

		# 7. GCC C Compilation
		local Array of String is gccArgs: ["-O2", tempCPath, "-o", outputPath, "-pthread", "-lm"];
		local Int is gccStatus: Process:execute(command: "gcc", args: gccArgs);
		if (emitCPath == "") {
			File:remove(path: tempCPath);
		}
		if (gccStatus != 0) {
			output:line("Error: Backend C compiler (gcc) failed with exit status " . gccStatus);
			return;
		}

		output:line("Compiled " . inputPath . " -> " . outputPath . " successfully!");
	}

}
