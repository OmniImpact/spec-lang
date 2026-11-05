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
	local String is currentClassName: '';

	## Return type of the method currently being code-generated.
	local String is currentMethodReturnType: '';

	## Name of the method currently being code-generated (for merge forwards).
	local String is currentMethodName: '';

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
	local String is helperFunctions: '';

	## Counter for assigning unique names to anonymous functions.
	local Int is anonCounter: 0;

	## Active inline return variable name when expanding an inline closure body.
	local String is inlineReturnVar: '';

	## Active inline return label name when expanding an inline closure body.
	local String is inlineReturnLabel: '';

	## Registry of local variables declared in the current function scope (for SPEC_AUTO injection).
	local Map of String to String is localScopeVars: Map:init();

	## True when the current inline-return target (fold accumulator, map result)
	## holds an ARC value and reassignment must go through spec_assign.
	local Boolean is inlineReturnArc: false;

	## True while generating a read position (arguments, conditions, chain targets,
	## operands): claim-yielding subexpressions are handed to the runtime claim
	## pool. False in consumption positions (initializers, returns, container
	## stores) where claims are adopted or borrows retained directly.
	local Boolean is argMode: true;

	## Garbage collection mode: "" (default ARC) or "boehm"
	local String is gcMode: '';

	## Declared-type context for the container literal currently being generated
	## (consumed by the ARRAY/MAP literal emitters; empty otherwise).
	local String is containerHint: '';

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
		self:helperFunctions: '';
		self:anonCounter: 0;
		self:inlineReturnVar: '';
		self:inlineReturnLabel: '';
		self:localScopeVars: Map:init();
		self:gcMode: '';
		self:containerHint: '';
	}

	Function is setGcMode(String is mode){
		self:gcMode: mode;
		self:prelude:setGcMode(mode: mode);
	}

	Function is setContainerHint(String is t){
		self:containerHint: t;
	}

	Function is setArgMode(Boolean is m){
		self:argMode: true;
	}

	Function of Boolean is isArcType(String is typeName){
		if (typeName == '' || typeName == 'Int' || typeName == 'int' || typeName == 'Real' || typeName == 'Float' || typeName == 'float' || typeName == 'Bool' || typeName == 'bool' || typeName == 'Byte' || typeName == 'byte' || typeName == 'Nil' || typeName == 'Void' || typeName == 'void') {
			return false;
		}
		if (typeName == 'String' || typeName == 'string') {
			return true;
		}
		if (typeName:contains(needle: ':')) {
			local Array of String is parts: typeName:split(delimiter: ':');
			typeName: parts:get(index: 0);
		}
		if (self:allEnumNames:has(key: typeName) && !self:allTaggedEnums:has(key: typeName)) {
			return false;
		}
		if (self:allTaggedEnums:has(key: typeName)) {
			return true;
		}
		if (typeName:startsWith(prefix: 'Array') || typeName:startsWith(prefix: 'Map') || typeName:startsWith(prefix: 'List') || typeName:startsWith(prefix: 'Function') || typeName == 'LoopControl') {
			return true;
		}
		if (self:allClassNames:has(key: typeName)) {
			return true;
		}
		return false;
	}

	## Classifies a container's element/value ownership from a canonical container
	## type string ("Array of X", "Array:X", "Map of K to V", "Map:K:V",
	## "List of X", "List:X").
	## Returns "object" (ARC-managed), "string" (container-owned copy),
	## "byte" (compact byte-buffer element), or
	## "none" (primitives, Any-typed, or unknown — never element-owned).
	Function of String is containerElemKind(String is containerType){
		local String is elem: '';
		if (containerType:startsWith(prefix: 'Array of ')) {
			elem: containerType:substring(start: 9, end: containerType:length());
		} else if (containerType:startsWith(prefix: 'Array:')) {
			elem: containerType:substring(start: 6, end: containerType:length());
		} else if (containerType:startsWith(prefix: 'List of ')) {
			elem: containerType:substring(start: 7, end: containerType:length());
		} else if (containerType:startsWith(prefix: 'List:')) {
			elem: containerType:substring(start: 5, end: containerType:length());
		} else if (containerType:startsWith(prefix: 'Map of ')) {
			local String is rest: containerType:substring(start: 7, end: containerType:length());
			local Int is toIdx: rest:indexOf(needle: ' to ', default: -1);
			if (toIdx >= 0) {
				elem: rest:substring(start: toIdx + 4, end: rest:length());
			}
		} else if (containerType:startsWith(prefix: 'Map:')) {
			local String is rest: containerType:substring(start: 4, end: containerType:length());
			local Int is colonIdx: rest:indexOf(needle: ':', default: -1);
			if (colonIdx >= 0) {
				elem: rest:substring(start: colonIdx + 1, end: rest:length());
			}
		} else {
			return 'none';
		}
		if (elem == '' || elem == 'Any') {
			return 'none';
		}
		if (elem == 'Byte' || elem == 'byte') {
			return 'byte';
		}
		if (self:isArcType(typeName: elem)) {
			return 'object';
		}
		return 'none';
	}

	## Generates the per-type constructor call for a `:` assignment.
	## Each type has a canonical construction path: primitives are casts,
	## String wraps raw bytes into a managed value, containers allocate.
	## The claim/retain logic is embedded in the constructor, replacing the
	## ad-hoc per-site emission.
	Function of String is generateTypedConstructor(String is typeName, String is valueC, Expression is expr, String is cType){
		local Boolean is claims: self:yieldsClaim(expr: expr);
		when (typeName) {
			is 'String', 'string': {
				if (claims) {
					return valueC;
				}
				return 'spec_construct_string(' . valueC . ')';
			}
			is 'Byte', 'byte': {
				return 'spec_construct_byte((long long)(' . valueC . '))';
			}
			is 'Int', 'int': {
				return valueC;
			}
			is 'Float', 'float': {
				return valueC;
			}
			is 'Boolean', 'bool': {
				return valueC;
			}
			is 'Array': {
				if (claims) {
					return '(' . cType . ')((' . valueC . '))';
				}
				return '(' . cType . ')spec_retain((void*)(' . valueC . '))';
			}
			is 'List': {
				if (claims) {
					return '(' . cType . ')((' . valueC . '))';
				}
				return '(' . cType . ')spec_retain((void*)(' . valueC . '))';
			}
			is 'Map': {
				if (claims) {
					return '(' . cType . ')((' . valueC . '))';
				}
				return '(' . cType . ')spec_retain((void*)(' . valueC . '))';
			}
			else: {
				if (self:isArcType(typeName: typeName)) {
					if (claims) {
						return '(' . cType . ')((' . valueC . '))';
					}
					return '(' . cType . ')spec_retain((void*)(' . valueC . '))';
				}
				return valueC;
			}
		}
	}

	## Determines whether a container's element/value type is ARC-managed, from a
	## canonical container type string. Any-typed and unknown containers are
	## never element-owned.
	Function of Boolean is containerElemIsArc(String is containerType){
		return self:containerElemKind(containerType: containerType) == 'object';
	}

	## Determines whether evaluating [expr] yields a transferred ownership claim:
	## constructors, user-class method calls, concat chains, ARC-typed literals,
	## and fresh-returning builtin methods hand one claim to the caller. Borrowing
	## expressions (locals, fields, container getters, primitives) do not.
	Function of Boolean is yieldsClaim(Expression is expr){
		local String is kind: expr:getKind();
		if (kind == 'ARRAY' || kind == 'MAP') {
			return true;
		}
		if (kind == 'BINARY') {
			return expr:binaryOp == '.';
		}
		if (kind == 'CALL') {
			local String is resT: self:inferTargetType(expr: expr);
			if (!self:isArcType(typeName: resT)) {
				return false;
			}
			local String is targetT0: self:inferTargetType(expr: expr:methodTarget);
			local String is targetT: targetT0;
			if (targetT:contains(needle: ':')) {
				local Array of String is parts0: targetT:split(delimiter: ':');
				targetT: parts0:get(index: 0);
			}
			if (self:allClassNames:has(key: targetT) && !self:allEnumNames:has(key: targetT)) {
				local String is mRet: self:lookupMethodReturnType(className: targetT, methodName: expr:methodName);
				if (mRet == '' || mRet == 'void' || mRet == 'Void') {
					return false;
				}
				if (mRet == targetT && expr:methodName != 'init' && expr:methodName != targetT) {
					return false;
				}
			}
			if (self:isBuiltinClass(name: targetT) || targetT == 'List' || targetT == 'String') {
				if (expr:methodName == 'get') {
					return targetT:startsWith(prefix: 'Map');
				}
				when (expr:methodName) {
					is 'pop', 'removeAt', 'substring', 'trim', 'replace', 'join', 'split', 'lines', 'keys',
					'getString', 'read', 'fromCharCode', 'toString', 'map', 'filter', 'slice', 'charAt': {
						return true;
					}
					else: {
						return false;
					}
				}
			}
			return true;
		}
		return false;
	}

	## A constructor call (`ClassName:init(...)` / `ClassName:new(...)`) produces a
	## provably fresh value: the creator abandons the initial ref, so the caller
	## owns it without an extra retain.
	Function of Boolean is isFreshConstructorCall(Expression is expr){
		if (expr:getKind() != 'CALL') {
			return false;
		}
		local String is m: expr:methodName;
		if (!(m == 'init' || m == 'new')) {
			return false;
		}
		local String is targetT: self:inferTargetType(expr: expr:methodTarget);
		return self:allClassNames:has(key: targetT);
	}

	Function of String is cTypeFor(String is typeName){
		local ClassInfo is curCls: self:findClass(name: self:currentClassName);
		if (curCls:getTypeParams():indexOf(search: typeName, default: -1) >= 0) {
			return 'void*';
		}
		if (typeName:startsWith(prefix: 'List')) {
			if (typeName == 'List:Byte' || typeName == 'List of Byte') {
				return 'SpecByteBuffer*';
			}
			return 'SpecVec*';
		}
		if (typeName:startsWith(prefix: 'Array')) {
			return 'SpecArray*';
		}
		if (typeName:startsWith(prefix: 'Map')) {
			return 'SpecMap*';
		}
		if (typeName:startsWith(prefix: 'Function')) {
			return 'SpecClosure*';
		}
		if (typeName:contains(needle: ':')) {
			local Array of String is parts: typeName:split(delimiter: ':');
			typeName: parts:get(index: 0);
		}
		if (self:allTaggedEnums:has(key: typeName)) {
			return typeName . '*';
		}
		if (self:allEnumNames:has(key: typeName)) {
			return typeName;
		}
		return self:utils:cTypeFor(typeName: typeName);
	}

	local Function of String is formatVarTypeString(Type is t){
		if (t:getName() == 'Function') {
			if (t:getParams():length() > 0) {
				local Type is ret: t:getParams():get(index: 0);
				return 'Function:' . self:formatTypeString(t: ret);
			}
			return 'Function';
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
		if (baseName == 'Function') {
			if (t:getParams():length() > 0) {
				local Type is ret: t:getParams():get(index: 0);
				return self:formatTypeString(t: ret);
			}
			return 'void';
		}
		if (t:getParams():length() == 1) {
			local Type is p0: t:getParams():get(index: 0);
			return baseName . ':' . self:formatTypeString(t: p0);
		}
		if (t:getParams():length() >= 2) {
			local Type is p0: t:getParams():get(index: 0);
			local Type is p1: t:getParams():get(index: 1);
			return baseName . ':' . self:formatTypeString(t: p0) . ':' . self:formatTypeString(t: p1);
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
		if (rawType:startsWith(prefix: 'Array:') && rawType:length() > 6) {
			local String is elem: rawType:substring(start: 6, end: rawType:length());
			local Int is eIdx: tps:indexOf(search: elem, default: -1);
			if (eIdx >= 0 && eIdx < typeArgs:length()) {
				return 'Array:' . typeArgs:get(index: eIdx);
			}
		}
		return rawType;
	}

	local Function of String is resolveReturnType(Type is t){
		if (t:getName() == 'Function') {
			if (t:getParams():length() > 0) {
				local Type is ret: t:getParams():get(index: 0);
				return self:cTypeFor(typeName: ret:getName());
			}
			return 'void';
		}
		return self:cTypeFor(typeName: t:getName());
	}

}
