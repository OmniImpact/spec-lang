#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, Linter, TypeChecker, CodeGenerator, Driver, and Loader.

## Resolves and loads multi-file package imports across the Spec project and standard library.
class Loader{

	replace local Array of String is using: [
		base:io:File,
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:reflect:Class,
		base:reflect:Member,
		compiler:Token,
		compiler:Lexer,
		compiler:Parser,
		base:meta:*
	];

	local Map of String to String is loadedFiles: Map:init();
	local Array of Class is loadedClasses: [];
	local Map of String to String is seenClassNames: Map:init();
	local Array of String is parseErrors: [];

	replace local Function is init(){
		self:loadedFiles: Map:init();
		self:loadedClasses: [];
		self:seenClassNames: Map:init();
		self:parseErrors: [];
	}

	replace local Function of Array of String is getParseErrors(){
		return self:parseErrors;
	}

	class PathConvLoop extends Loop{
		local String is src;
		local Int is pos: 0;
		local String is res: "";

		replace local Function is init(String is src){
			self:src: src;
			self:pos: 0;
			self:res: "";
		}

		replace local Function of Boolean is evaluate(){
			return self:pos < self:src:length();
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:src:charAt(index: self:pos, default: "");
			self:pos: self:pos + 1;
			if (ch == ":") {
				self:res: self:res . "/";
			} else {
				self:res: self:res . ch;
			}
			return true;
		}
	}

	## Converts a Spec package identifier path (e.g. "base:struct:Array") into a filesystem path.
	##
	## @param rawPath: Colon-separated package identifier.
	## @return: Resolved filesystem path string, or empty string if not found.
	replace local Function of String is resolvePath(String is rawPath){
		local PathConvLoop is loop: PathConvLoop:init(src: rawPath);
		While:run(loop: loop);
		local String is converted: loop:res;

		local String is cand1: converted . ".spec";
		if (File:exists(path: cand1)) {
			return cand1;
		}

		local String is cand2: "lib/" . converted . ".spec";
		if (File:exists(path: cand2)) {
			return cand2;
		}

		return "";
	}

	## Expands wildcard package import paths into standard library file lists.
	##
	## @param rawPath: Wildcard package identifier (e.g. "base:io:*").
	## @return: Array of constituent file paths.
	replace local Function of Array of String is expandWildcard(String is rawPath){
		return when (rawPath) {
			is "base:io:*": [
				"lib/base/io/File.spec",
				"lib/base/io/Input.spec",
				"lib/base/io/InputHandler.spec",
				"lib/base/io/Output.spec"
			];
			is "base:iterator:*": [
				"lib/base/iterator/Loop.spec",
				"lib/base/iterator/LoopControl.spec",
				"lib/base/iterator/LoopCallback.spec",
				"lib/base/iterator/While.spec"
			];
			is "base:meta:*": [
				"lib/base/meta/AST.spec"
			];
			is "base:reflect:*": [
				"lib/base/reflect/Type.spec",
				"lib/base/reflect/Parameter.spec",
				"lib/base/reflect/Member.spec",
				"lib/base/reflect/Class.spec"
			];
			is "base:struct:*": [
				"lib/base/struct/Array.spec",
				"lib/base/struct/Map.spec"
			];
			is "base:sys:*": [
				"lib/base/sys/Process.spec",
				"lib/base/sys/SourceLocation.spec",
				"lib/base/sys/StackFrame.spec"
			];
			is "base:math:*": [
				"lib/base/math/Math.spec"
			];
			is "compiler:*": [
				"lib/compiler/Token.spec",
				"lib/compiler/Lexer.spec",
				"lib/compiler/Parser.spec",
				"lib/compiler/Linter.spec",
				"lib/compiler/TypeChecker.spec",
				"lib/compiler/CBackendUtils.spec",
				"lib/compiler/RuntimePrelude.spec",
				"lib/compiler/DeclarationGenerator.spec",
				"lib/compiler/BuiltinCallGenerator.spec",
				"lib/compiler/CodeGenerator.spec",
				"lib/compiler/Loader.spec",
				"lib/compiler/Driver.spec"
			];
			else: [];
		};
	}

	## Recursively reads, tokenizes, and parses a source file and its transitive dependencies.
	##
	## @param filePath: Path to target `.spec` file.
	replace local Function is loadFile(String is filePath){
		if (self:loadedFiles:has(key: filePath)) {
			return;
		}
		self:loadedFiles:set(key: filePath, value: "true");

		if (!File:exists(path: filePath)) {
			return;
		}

		local String is src: File:read(path: filePath, default: "");
		local Lexer is lexer: Lexer:init(source: src);
		local Array of Token is tokens: lexer:tokenize();
		local Parser is parser: Parser:init(tokens: tokens);
		parser:setSourceFile(file: filePath);
		local ProgramNode is prog: parser:parseProgram();
		if (parser:hasErrors()) {
			parser:getErrors():each(action: local Function(String is err){
				self:parseErrors:add(item: err);
			});
		}

		prog:getClasses():each(action: local Function(Class is c){
			if (!self:seenClassNames:has(key: c:getName())) {
				self:seenClassNames:set(key: c:getName(), value: "true");
				self:loadedClasses:add(item: c);
			}
			self:collectImportsFromClass(c: c);
		});
	}

	## Gathers and loads all `using` imports declared in a class definition.
	##
	## @param c: Target [Class] definition.
	replace local Function is collectImportsFromClass(Class is c){
		c:getMembers():each(action: local Function(Member is m){
			if (m:getName() == "using" && m:getHasInit()) {
				local Expression is initExpr: m:getInitExpr();
				if (initExpr:getKind() == "ARRAY") {
					initExpr:arrayItems:each(action: local Function(Expression is item){
						local String is importStr: item:stringValue;
						local Array of String is wildcards: self:expandWildcard(rawPath: importStr);
						if (wildcards:length() > 0) {
							wildcards:each(action: local Function(String is f){
								self:loadFile(filePath: f);
							});
						} else {
							local String is resolved: self:resolvePath(rawPath: importStr);
							if (resolved != "") {
								self:loadFile(filePath: resolved);
							}
						}
					});
				}
			}
		});
	}

	## Coordinates root file loading and dependency traversal to produce a unified [ProgramNode].
	##
	## @param rootPath: Filesystem path to the application entry file.
	## @return: Merged [ProgramNode] AST containing root and imported classes.
	replace local Function of ProgramNode is loadProgram(String is rootPath){
		self:loadedFiles: Map:init();
		self:loadedClasses: [];
		self:seenClassNames: Map:init();
		self:parseErrors: [];

		self:loadFile(filePath: rootPath);

		return ProgramNode:init(classes: self:loadedClasses);
	}

}
