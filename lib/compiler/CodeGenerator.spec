#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, Linter, TypeChecker, and CodeGenerator.

## Pure Spec C code generator translating [ProgramNode] AST to C11 code.
Class is CodeGenerator{

	replace Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:reflect:Type,
		base:reflect:ClassInfo,
		base:reflect:Member,
		base:reflect:Parameter,
		base:meta:*,
		compiler:CBackendUtils,
		compiler:RuntimePrelude,
		compiler:DeclarationGenerator,
		compiler:BuiltinCallGenerator,
		compiler:CodeGeneratorLookups,
		compiler:CodeGeneratorInference,
		compiler:CodeGeneratorExpressions,
		compiler:CodeGeneratorProgram
	];

	## Backend utilities for identifier sanitization, string escaping, and type mapping.
	local CBackendUtils is utils;

	## Runtime prelude emitter for standard C11 Spec library definitions.
	local RuntimePrelude is prelude;

	## Sub-generator for C enum, forward declaration, and struct layout definitions.
	local DeclarationGenerator is declGen;

	## Sub-generator for standard library and runtime builtin calls.
	local BuiltinCallGenerator is builtins;

	## Name of the class currently being code-generated.
	local String is currentClassName: "";

	## Return type of the method currently being code-generated.
	local String is currentMethodReturnType: "";

	## Name of the method currently being code-generated (for merge forwards).
	local String is currentMethodName: "";

	## Virtual method slot assignment: method name -> decimal slot index.
	local Map of String to String is methodSlots: Map:init();

	## Method names declared by more than one class (candidate overrides).
	local Map of String to String is overriddenMethods: Map:init();

	## Total number of virtual slots.
	local Int is methodSlotCount: 0;

	## Slot index -> method name (parallel to methodSlots).
	local Array of String is slotNames: [];

	## Classes declaring an explicit toString (static call targets).
	local Map of String to String is classesWithToString: Map:init();

	## Local variables visible in current method scope (variable name -> type name).
	local Map of String to String is localVars: Map:init();

	## Struct fields visible in current class scope (field name -> type name).
	local Map of String to String is fieldTypes: Map:init();

	## Flattened list of all classes in the program for symbol lookups.
	local Array of ClassInfo is programClasses: [];

	## Registry of all class names defined in the program.
	local Map of String to String is allClassNames: Map:init();

	## Registry of all enum type names defined in the program.
	local Map of String to String is allEnumNames: Map:init();

	## Registry of all enum variant names to their parent enum name.
	local Map of String to String is allEnumVariants: Map:init();

	## Registry of all string-backed enum names.
	local Map of String to String is allStringBackedEnums: Map:init();

	## Registry of all tagged union enum names (enums with payload variants).
	local Map of String to String is allTaggedEnums: Map:init();

	## Flag indicating whether code generation is currently inside a method body.
	local Boolean is inMethod: false;

	## Forward declaration buffer for generated anonymous static functions.
	local String is helperFunctions: "";

	## Counter for assigning unique names to anonymous functions.
	local Int is anonCounter: 0;

	## Active inline return variable name when expanding an inline closure body.
	local String is inlineReturnVar: "";

	## Active inline return label name when expanding an inline closure body.
	local String is inlineReturnLabel: "";

	replace Function is init(){
		self:utils: CBackendUtils:init();
		self:prelude: RuntimePrelude:init();
		self:declGen: DeclarationGenerator:init();
		self:builtins: BuiltinCallGenerator:init();
		self:localVars: Map:init();
		self:fieldTypes: Map:init();
		self:programClasses: [];
		self:allClassNames: Map:init();
		self:allEnumNames: Map:init();
		self:allEnumVariants: Map:init();
		self:allStringBackedEnums: Map:init();
		self:allTaggedEnums: Map:init();
		self:inMethod: false;
		self:classesWithToString: Map:init();
		self:helperFunctions: "";
		self:anonCounter: 0;
		self:inlineReturnVar: "";
		self:inlineReturnLabel: "";
	}

	local Function of String is cTypeFor(String is typeName){
		local ClassInfo is curCls: self:findClass(name: self:currentClassName);
		if (curCls:getTypeParams():indexOf(search: typeName, default: -1) >= 0) {
			return "void*";
		}
		if (typeName:startsWith(prefix: "Array")) {
			return "SpecArray*";
		}
		if (typeName:startsWith(prefix: "Map")) {
			return "SpecMap*";
		}
		if (typeName:startsWith(prefix: "Function")) {
			return "void*";
		}
		if (typeName:contains(needle: ":")) {
			local Array of String is parts: typeName:split(delimiter: ":");
			typeName: parts:get(index: 0);
		}
		if (self:allTaggedEnums:has(key: typeName)) {
			return typeName . "*";
		}
		if (self:allEnumNames:has(key: typeName)) {
			return typeName;
		}
		return self:utils:cTypeFor(typeName: typeName);
	}

	local Function of String is formatVarTypeString(Type is t){
		if (t:getName() == "Function") {
			if (t:getParams():length() > 0) {
				local Type is ret: t:getParams():get(index: 0);
				return "Function:" . self:formatTypeString(t: ret);
			}
			return "Function";
		}
		return self:formatTypeString(t: t);
	}

	local Function of String is cIdent(String is name){
		return self:utils:cIdent(name: name);
	}

	local Function of String is escapeString(String is s){
		return self:utils:escapeString(s: s);
	}

	local Function of Boolean is isBuiltinClass(String is name){
		return self:utils:isBuiltinClass(name: name);
	}

	local Function of String is formatTypeString(Type is t){
		local String is baseName: t:getName();
		if (baseName == "Function") {
			if (t:getParams():length() > 0) {
				local Type is ret: t:getParams():get(index: 0);
				return self:formatTypeString(t: ret);
			}
			return "void";
		}
		if (t:getParams():length() == 1) {
			local Type is p0: t:getParams():get(index: 0);
			return baseName . ":" . p0:getName();
		}
		if (t:getParams():length() >= 2) {
			local Type is p0: t:getParams():get(index: 0);
			local Type is p1: t:getParams():get(index: 1);
			return baseName . ":" . p0:getName() . ":" . p1:getName();
		}
		return baseName;
	}

	local Function of String is substituteTypeParam(String is rawType, ClassInfo is cls, Array of String is typeArgs){
		local Array of String is tps: cls:getTypeParams();
		if (tps:length() == 0 || typeArgs:length() == 0) {
			return rawType;
		}
		local Int is idx: tps:indexOf(search: rawType, default: -1);
		if (idx >= 0 && idx < typeArgs:length()) {
			return typeArgs:get(index: idx);
		}
		if (rawType:startsWith(prefix: "Array:") && rawType:length() > 6) {
			local String is elem: rawType:substring(start: 6, end: rawType:length());
			local Int is eIdx: tps:indexOf(search: elem, default: -1);
			if (eIdx >= 0 && eIdx < typeArgs:length()) {
				return "Array:" . typeArgs:get(index: eIdx);
			}
		}
		return rawType;
	}

	local Function of String is resolveReturnType(Type is t){
		if (t:getName() == "Function") {
			if (t:getParams():length() > 0) {
				local Type is ret: t:getParams():get(index: 0);
				return self:cTypeFor(typeName: ret:getName());
			}
			return "void";
		}
		return self:cTypeFor(typeName: t:getName());
	}

}
