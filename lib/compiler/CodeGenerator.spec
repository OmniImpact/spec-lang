#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, Linter, TypeChecker, and CodeGenerator.

## Pure Spec C code generator translating [ProgramNode] AST to C11 code.
class CodeGenerator{

	replace local Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:reflect:Type,
		base:reflect:Class,
		base:reflect:Member,
		base:reflect:Parameter,
		base:meta:*,
		compiler:CBackendUtils,
		compiler:RuntimePrelude,
		compiler:DeclarationGenerator,
		compiler:BuiltinCallGenerator
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

	## Local variables visible in current method scope (variable name -> type name).
	local Map of String to String is localVars: Map:init();

	## Struct fields visible in current class scope (field name -> type name).
	local Map of String to String is fieldTypes: Map:init();

	## Flattened list of all classes in the program for symbol lookups.
	local Array of Class is programClasses: [];

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

	replace local Function is init(){
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
		self:helperFunctions: "";
		self:anonCounter: 0;
		self:inlineReturnVar: "";
		self:inlineReturnLabel: "";
	}

	replace local Function of String is cTypeFor(String is typeName){
		local Class is curCls: self:findClass(name: self:currentClassName);
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

	replace local Function of String is formatVarTypeString(Type is t){
		if (t:getName() == "Function") {
			if (t:getParams():length() > 0) {
				local Type is ret: t:getParams():get(index: 0);
				return "Function:" . self:formatTypeString(t: ret);
			}
			return "Function";
		}
		return self:formatTypeString(t: t);
	}

	replace local Function of String is cIdent(String is name){
		return self:utils:cIdent(name: name);
	}

	replace local Function of String is escapeString(String is s){
		return self:utils:escapeString(s: s);
	}

	replace local Function of Boolean is isBuiltinClass(String is name){
		return self:utils:isBuiltinClass(name: name);
	}

	replace local Function of String is formatTypeString(Type is t){
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

	replace local Function of String is substituteTypeParam(String is rawType, Class is cls, Array of String is typeArgs){
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

	replace local Function of String is resolveReturnType(Type is t){
		if (t:getName() == "Function") {
			if (t:getParams():length() > 0) {
				local Type is ret: t:getParams():get(index: 0);
				return self:cTypeFor(typeName: ret:getName());
			}
			return "void";
		}
		return self:cTypeFor(typeName: t:getName());
	}

	replace local Function of String is generatePrelude(){
		return self:prelude:emitRuntime();
	}

	class ClassSearchLoop extends Loop{
		local Array of Class is list;
		local String is target;
		local Int is idx: 0;
		local Class is res;
		local Boolean is found: false;

		replace local Function is init(Array of Class is list, String is target){
			self:list: list;
			self:target: target;
			self:idx: 0;
			self:found: false;
		}

		replace local Function of Boolean is evaluate(){
			return !self:found && self:idx < self:list:length();
		}

		replace local Function of Boolean is iteration(LoopControl is c){
			local Class is cand: self:list:get(index: self:idx);
			self:idx: self:idx + 1;
			if (cand:getName() == self:target) {
				self:res: cand;
				self:found: true;
				return false;
			}
			return true;
		}
	}

	replace local Function of Class is findClass(String is name){
		local ClassSearchLoop is s: ClassSearchLoop:init(list: self:programClasses, target: name);
		While:run(loop: s);
		if (s:found) {
			return s:res;
		}
		return Class:init(name: "", baseClass: "", members: []);
	}

	class FieldMemberLoop extends Loop{
		local Array of Member is members;
		local String is fieldName;
		local Int is idx: 0;
		local Member is res;
		local Boolean is found: false;

		replace local Function is init(Array of Member is members, String is fieldName){
			self:members: members;
			self:fieldName: fieldName;
			self:idx: 0;
			self:found: false;
		}

		replace local Function of Boolean is evaluate(){
			return !self:found && self:idx < self:members:length();
		}

		replace local Function of Boolean is iteration(LoopControl is c){
			local Member is m: self:members:get(index: self:idx);
			self:idx: self:idx + 1;
			if (m:getKind() == "FIELD" && m:getName() == self:fieldName) {
				self:res: m;
				self:found: true;
				return false;
			}
			return true;
		}
	}

	replace local Function of String is lookupFieldType(String is className, String is fieldName){
		if (className == "" || className == "Any") {
			return "";
		}
		local Array of String is parts: className:split(delimiter: ":");
		local String is baseClassName: parts:get(index: 0);
		local Array of String is typeArgs: parts:slice(start: 1, end: parts:length());
		local Class is cls: self:findClass(name: baseClassName);
		if (cls:getName() == "") {
			return "";
		}
		local FieldMemberLoop is fl: FieldMemberLoop:init(members: cls:getMembers(), fieldName: fieldName);
		While:run(loop: fl);
		if (fl:found) {
			local Member is foundM: fl:res;
			local String is rawT: self:formatTypeString(t: foundM:getType());
			return self:substituteTypeParam(rawType: rawT, cls: cls, typeArgs: typeArgs);
		}
		local String is inherited: "";
		cls:getBaseClasses():each(action: local Function(String is baseName){
			if (inherited == "") {
				inherited: self:lookupFieldType(className: baseName, fieldName: fieldName);
			}
		});
		return inherited;
	}

	class MethodMemberLoop extends Loop{
		local Array of Member is members;
		local String is methodName;
		local Int is idx: 0;
		local Member is res;
		local Boolean is found: false;

		replace local Function is init(Array of Member is members, String is methodName){
			self:members: members;
			self:methodName: methodName;
			self:idx: 0;
			self:found: false;
		}

		replace local Function of Boolean is evaluate(){
			return !self:found && self:idx < self:members:length();
		}

		replace local Function of Boolean is iteration(LoopControl is c){
			local Member is m: self:members:get(index: self:idx);
			self:idx: self:idx + 1;
			if (m:getKind() == "METHOD" && m:getName() == self:methodName) {
				self:res: m;
				self:found: true;
				return false;
			}
			return true;
		}
	}

	replace local Function of Member is lookupEnumVariant(String is enumName, String is variantName){
		local Class is cls: self:findClass(name: enumName);
		local FieldMemberLoop is fl: FieldMemberLoop:init(members: cls:getMembers(), fieldName: variantName);
		While:run(loop: fl);
		if (fl:found) {
			return fl:res;
		}
		return Member:init(kind: "");
	}

	replace local Function of String is generateWhenCondition(Expression is subjExpr, String is subjC, Expression is c){
		if (c:getKind() == "CALL" && self:allEnumVariants:has(key: c:methodName)) {
			local String is eName: self:allEnumVariants:getString(key: c:methodName, default: "");
			if (self:allTaggedEnums:has(key: eName)) {
				return "((" . subjC . ") && (" . subjC . ")->_tag == " . eName . "_TAG_" . self:cIdent(name: c:methodName) . ")";
			}
		}
		if (c:getKind() == "IDENT" && self:allEnumVariants:has(key: c:stringValue)) {
			local String is eName: self:allEnumVariants:getString(key: c:stringValue, default: "");
			if (self:allTaggedEnums:has(key: eName)) {
				return "((" . subjC . ") && (" . subjC . ")->_tag == " . eName . "_TAG_" . self:cIdent(name: c:stringValue) . ")";
			}
		}
		if (c:getKind() == "PATH" && c:pathSegments:length() >= 2 && self:allTaggedEnums:has(key: c:pathSegments:get(index: 0))) {
			local String is eName: c:pathSegments:get(index: 0);
			local String is vName: c:pathSegments:get(index: 1);
			return "((" . subjC . ") && (" . subjC . ")->_tag == " . eName . "_TAG_" . self:cIdent(name: vName) . ")";
		}
		local String is cVal: self:generateExpression(expr: c);
		if (self:isStringExpr(expr: subjExpr)) {
			return "spec_str_equals(" . subjC . ", " . cVal . ")";
		}
		return "((" . subjC . ") == (" . cVal . "))";
	}

	replace local Function of String is generateWhenBindings(String is subjC, WhenArm is arm){
		local String is binds: "";
		arm:conditions:each(action: local Function(Expression is c){
			if (c:getKind() == "CALL" && self:allEnumVariants:has(key: c:methodName)) {
				local String is eName: self:allEnumVariants:getString(key: c:methodName, default: "");
				if (self:allTaggedEnums:has(key: eName)) {
					local Member is vMem: self:lookupEnumVariant(enumName: eName, variantName: c:methodName);
					local String is vNameC: self:cIdent(name: c:methodName);
					local Int is idx: 0;
					c:methodArgs:each(action: local Function(NamedArg is arg){
						if (idx < vMem:getParameters():length()) {
							local Expression is av: arg:getValue();
							if (av:getKind() == "IDENT") {
								local Parameter is pDef: vMem:getParameters():get(index: idx);
								local String is bindName: av:stringValue;
								self:localVars:set(key: bindName, value: self:formatVarTypeString(t: pDef:getType()));
								local String is pCType: self:cTypeFor(typeName: pDef:getType():getName());
								binds: binds . "        " . pCType . " " . self:cIdent(name: bindName) . " = (" . subjC . ")->" . vNameC . "_" . self:cIdent(name: pDef:getName()) . ";\n";
							}
						}
						idx: idx + 1;
					});
				}
			}
		});
		return binds;
	}

	replace local Function of String is findMethodImplementingClass(String is className, String is methodName, Int is paramCount){
		if (className == "" || className == "Any") {
			return "";
		}
		local Array of String is parts: className:split(delimiter: ":");
		local String is baseClassName: parts:get(index: 0);
		local Class is cls: self:findClass(name: baseClassName);
		if (cls:getName() == "") {
			return "";
		}
		local MethodMemberLoop is ml: MethodMemberLoop:init(members: cls:getMembers(), methodName: methodName);
		While:run(loop: ml);
		if (ml:found) {
			local Member is subM: ml:res;
			if (subM:getBody():length() > 0 && (paramCount < 0 || subM:getParameters():length() == paramCount)) {
				return baseClassName;
			}
		}
		local String is inherited: "";
		cls:getBaseClasses():each(action: local Function(String is baseName){
			if (inherited == "") {
				inherited: self:findMethodImplementingClass(className: baseName, methodName: methodName, paramCount: paramCount);
			}
		});
		return inherited;
	}

	replace local Function of Member is lookupMethodMember(String is className, String is methodName){
		if (className == "" || className == "Any") {
			return Member:init(kind: "");
		}
		local Array of String is parts: className:split(delimiter: ":");
		local String is baseClassName: parts:get(index: 0);
		local Class is cls: self:findClass(name: baseClassName);
		if (cls:getName() == "") {
			return Member:init(kind: "");
		}
		local MethodMemberLoop is ml: MethodMemberLoop:init(members: cls:getMembers(), methodName: methodName);
		While:run(loop: ml);
		if (ml:found) {
			return ml:res;
		}
		local Member is inherited: Member:init(kind: "");
		cls:getBaseClasses():each(action: local Function(String is baseName){
			if (inherited:getKind() == "") {
				inherited: self:lookupMethodMember(className: baseName, methodName: methodName);
			}
		});
		return inherited;
	}

	replace local Function of String is formatCallArguments(String is className, String is methodName, Array of NamedArg is args){
		local Member is m: self:lookupMethodMember(className: className, methodName: methodName);
		local Array of String is parts: className:split(delimiter: ":");
		local String is baseClassName: parts:get(index: 0);
		local Class is cls: self:findClass(name: baseClassName);
		local Array of String is tps: cls:getTypeParams();
		if (m:getKind() == "METHOD") {
			local Array of Parameter is params: m:getParameters();
			if (params:length() > 0) {
				local String is joined: "";
				local Int is pIdx: 0;
				params:each(action: local Function(Parameter is p){
					local String is pName: p:getName();
					local Boolean is matched: false;
					local String is argC: "0";
					args:each(action: local Function(NamedArg is a){
						if (!matched && a:getName() == pName && pName != "") {
							argC: self:generateExpression(expr: a:getValue());
							matched: true;
						}
					});
					if (!matched && pIdx < args:length()) {
						local NamedArg is posArg: args:get(index: pIdx);
						if (posArg:getName() == "") {
							argC: self:generateExpression(expr: posArg:getValue());
							matched: true;
						}
					}
					if (!matched && p:getHasDefault()) {
						argC: self:generateExpression(expr: p:getDefaultExpr());
						matched: true;
					}
					if (tps:indexOf(search: p:getType():getName(), default: -1) >= 0) {
						argC: "(void*)(intptr_t)(" . argC . ")";
					}
					joined: joined . ", " . argC;
					pIdx: pIdx + 1;
				});
				return joined;
			}
		}
		local String is fallbackJoined: "";
		args:each(action: local Function(NamedArg is arg){
			fallbackJoined: fallbackJoined . ", " . self:generateExpression(expr: arg:getValue());
		});
		return fallbackJoined;
	}

	replace local Function of String is lookupMethodReturnType(String is className, String is methodName){
		if (className == "" || className == "Any") {
			return "";
		}
		local Array of String is parts: className:split(delimiter: ":");
		local String is baseClassName: parts:get(index: 0);
		local Array of String is typeArgs: parts:slice(start: 1, end: parts:length());
		if (methodName == "init" && self:allClassNames:has(key: baseClassName) && !self:allEnumNames:has(key: baseClassName)) {
			return className;
		}
		local Class is cls: self:findClass(name: baseClassName);
		if (cls:getName() == "") {
			return "";
		}
		local MethodMemberLoop is ml: MethodMemberLoop:init(members: cls:getMembers(), methodName: methodName);
		While:run(loop: ml);
		if (ml:found) {
			local Member is foundM: ml:res;
			local String is rawT: self:formatTypeString(t: foundM:getType());
			if (rawT == "" || rawT == "void" || rawT == "Void") {
				return className;
			}
			return self:substituteTypeParam(rawType: rawT, cls: cls, typeArgs: typeArgs);
		}
		local String is inherited: "";
		cls:getBaseClasses():each(action: local Function(String is baseName){
			if (inherited == "") {
				inherited: self:lookupMethodReturnType(className: baseName, methodName: methodName);
			}
		});
		return inherited;
	}

	class PathTypeResolveLoop extends Loop{
		local CodeGenerator is cg;
		local Array of String is segs;
		local Int is idx: 1;
		local String is currType: "";

		replace local Function is init(CodeGenerator is cg, Array of String is segs, String is rootType){
			self:cg: cg;
			self:segs: segs;
			self:currType: rootType;
			self:idx: 1;
		}

		replace local Function of Boolean is evaluate(){
			return self:currType != "" && self:idx < self:segs:length();
		}

		replace local Function of Boolean is iteration(LoopControl is c){
			local String is seg: self:segs:get(index: self:idx);
			self:idx: self:idx + 1;
			if (self:cg:allEnumNames:has(key: self:currType)) {
				return true;
			}
			self:currType: self:cg:lookupFieldType(className: self:currType, fieldName: seg);
			return true;
		}
	}

	## Infers the target type of an expression for method dispatch and type conversion.
	replace local Function of String is inferTargetType(Expression is expr){
		local String is resolved: expr:getResolvedType();
		if (resolved != "" && resolved != "Any") {
			return resolved;
		}

		local String is kind: expr:getKind();
		if (kind == "STRING") { return "String"; }
		if (kind == "NUMBER") { return "Int"; }
		if (kind == "FLOAT") { return "Float"; }
		if (kind == "BOOL") { return "Boolean"; }

		if (kind == "IDENT") {
			local String is name: expr:stringValue;
			if (name == "self") { return self:currentClassName; }
			if (self:localVars:has(key: name)) {
				return self:localVars:getString(key: name, default: "");
			}
			if (self:fieldTypes:has(key: name)) {
				return self:fieldTypes:getString(key: name, default: "");
			}
			if (self:allEnumVariants:has(key: name)) {
				return self:allEnumVariants:getString(key: name, default: "");
			}
			if (self:allClassNames:has(key: name)) {
				return name;
			}
			return "";
		}
		if (kind == "PATH") {
			local Array of String is segs: expr:pathSegments;
			if (segs:length() > 0) {
				local String is root: segs:get(index: 0);
				local String is rootType: "";
				if (root == "self") {
					rootType: self:currentClassName;
				} else if (self:localVars:has(key: root)) {
					rootType: self:localVars:getString(key: root, default: "");
				} else if (self:fieldTypes:has(key: root)) {
					rootType: self:fieldTypes:getString(key: root, default: "");
				} else if (self:allEnumNames:has(key: root) || self:allClassNames:has(key: root)) {
					rootType: root;
				}
				local PathTypeResolveLoop is pLoop: PathTypeResolveLoop:init(cg: self, segs: segs, rootType: rootType);
				While:run(loop: pLoop);
				return pLoop:currType;
			}
			return "";
		}
		if (kind == "CALL") {
			local String is tgtType: self:inferTargetType(expr: expr:methodTarget);
			if (tgtType == "" || tgtType == "self") {
				tgtType: self:currentClassName;
			}
			local String is m: expr:methodName;
			if (tgtType:startsWith(prefix: "Array:") && (m == "get" || m == "pop" || m == "removeAt")) {
				return tgtType:substring(start: 6, end: tgtType:length());
			}
			if (self:allEnumNames:has(key: tgtType)) {
				if (m == "name") { return "String"; }
				if (m == "ordinal") { return "Int"; }
				if (m == "values") { return "Array:" . tgtType; }
				if (m == "value") {
					return if (self:allStringBackedEnums:has(key: tgtType)) "String" else "Int";
				}
			}
			if (tgtType == "String" && m == "fromCharCode") {
				return "String";
			}
			if (tgtType == "Math" || tgtType == "math") {
				if (m == "toInt") { return "Int"; }
				if (m == "round" || m == "floor" || m == "ceil" || m == "ceiling" || m == "random" || m == "abs" || m == "min" || m == "max" || m == "clamp" || m == "sqrt" || m == "sin" || m == "cos" || m == "tan" || m == "atan2" || m == "log" || m == "log2" || m == "pow" || m == "toFloat") {
					return "Float";
				}
			}
			local String is methodRet: self:lookupMethodReturnType(className: tgtType, methodName: m);
			if (methodRet != "" && methodRet != "void") {
				return methodRet;
			}
			return "";
		}
		if (kind == "INDEX") {
			local String is leftT: self:inferTargetType(expr: expr:leftExpr);
			if (leftT:startsWith(prefix: "Array:") && leftT:length() > 6) {
				return leftT:substring(start: 6, end: leftT:length());
			}
			return "";
		}
		return "";
	}

	## Wraps non-string expressions with runtime string conversion helpers.
	##
	## @param expr: AST [Expression] node.
	## @param exprC: Generated C expression string.
	## @return: Wrapped C expression string.
	replace local Function of String is wrapToString(Expression is expr, String is exprC){
		local String is resolved: self:inferTargetType(expr: expr);
		when (resolved) {
			is "Int", "int": {
				return "spec_to_string_int(" . exprC . ")";
			}
			is "Float", "float": {
				return "spec_to_string_float(" . exprC . ")";
			}
			is "Boolean", "bool": {
				return "spec_to_string_bool(" . exprC . ")";
			}
			is "String", "string": {
				return exprC;
			}
			else: {}
		}

		local String is kind: expr:getKind();
		when (kind) {
			is "NUMBER": {
				return "spec_to_string_int(" . exprC . ")";
			}
			is "FLOAT": {
				return "spec_to_string_float(" . exprC . ")";
			}
			is "BOOL": {
				return "spec_to_string_bool(" . exprC . ")";
			}
			is "BINARY": {
				local String is op: expr:binaryOp;
				if (op == "+" || op == "-" || op == "*" || op == "/" || op == "%") {
					return "spec_to_string_int(" . exprC . ")";
				}
				if (op == "==" || op == "!=" || op == "<" || op == "<=" || op == ">" || op == ">=" || op == "&&" || op == "||") {
					return "spec_to_string_bool(" . exprC . ")";
				}
				return exprC;
			}
			is "UNARY": {
				if (expr:unaryOp == "!") {
					return "spec_to_string_bool(" . exprC . ")";
				}
				return "spec_to_string_int(" . exprC . ")";
			}
			else: {
				return exprC;
			}
		}
	}

	## Determines whether an expression produces a string value.
	replace local Function of Boolean is isStringExpr(Expression is expr){
		local String is resolved: self:inferTargetType(expr: expr);
		if (resolved == "String" || resolved == "string") {
			return true;
		}
		local String is kind: expr:getKind();
		if (kind == "STRING") {
			return true;
		}
		if (kind == "BINARY" && expr:binaryOp == ".") {
			return true;
		}
		return false;
	}

	replace local Function of Boolean is isSubclassOf(String is subName, String is baseName){
		if (subName == "" || baseName == "" || subName == baseName) {
			return false;
		}
		local Class is subCls: self:findClass(name: subName);
		if (subCls:getName() == "") {
			return false;
		}
		local Boolean is matched: false;
		subCls:getBaseClasses():each(action: local Function(String is parent){
			if (parent == baseName) {
				matched: true;
			} else if (!matched && self:isSubclassOf(subName: parent, baseName: baseName)) {
				matched: true;
			}
		});
		return matched;
	}

	## Emits constructor factory functions for all classes.
	##
	## @param classes: Array of [Class] definitions.
	## @return: C constructor functions text.
	replace local Function of String is generateConstructors(Array of Class is classes){
		local String is out: "/* Constructor Implementations */\n";

		classes:each(action: local Function(Class is c){
			if (!self:isBuiltinClass(name: c:getName()) && c:getBaseClass() != "Enum") {
				self:currentClassName: c:getName();
				self:fieldTypes: Map:init();
				local Array of Member is allFields: [];
				self:declGen:collectStructFields(c: c, allClasses: classes, acc: allFields);
				allFields:each(action: local Function(Member is f){
					self:fieldTypes:set(key: f:getName(), value: self:formatTypeString(t: f:getType()));
				});

				out: out . c:getName() . "* " . c:getName() . "_new(void) {\n";
				out: out . "    " . c:getName() . "* self = (" . c:getName() . "*)calloc(1, sizeof(" . c:getName() . "));\n";
				out: out . "    self->_type_name = \"" . c:getName() . "\";\n";
				allFields:each(action: local Function(Member is m){
					if (m:hasInit) {
						out: out . "    self->" . self:cIdent(name: m:getName()) . " = " . self:generateExpression(expr: m:initExpr) . ";\n";
					} else {
						local String is ft: m:getType():getName();
						if (ft == "String" || ft == "string") {
							out: out . "    self->" . self:cIdent(name: m:getName()) . " = \"\";\n";
						} else if (ft == "Array") {
							out: out . "    self->" . self:cIdent(name: m:getName()) . " = spec_array_new();\n";
						} else if (ft == "Map") {
							out: out . "    self->" . self:cIdent(name: m:getName()) . " = spec_map_new();\n";
						}
					}
				});
				out: out . "    return self;\n";
				out: out . "}\n\n";
			}
		});
		return out;
	}

	replace local Function of String is generateInlineArrayOp(String is mode, String is targetC, Expression is fnExpr){
		self:anonCounter: self:anonCounter + 1;
		local Int is id: self:anonCounter;
		local String is savedRetVar: self:inlineReturnVar;
		local String is savedRetLbl: self:inlineReturnLabel;
		self:inlineReturnLabel: "_loop_next_" . id;
		if (mode == "each") {
			self:inlineReturnVar: "";
		} else {
			self:inlineReturnVar: "_pred_" . id;
		}

		local Map of String to String is savedVars: Map:init();
		local Array of String is outerKeys: self:localVars:keys();
		outerKeys:each(action: local Function(String is k){
			savedVars:set(key: k, value: self:localVars:getString(key: k, default: ""));
		});

		local String is paramDecl: "";
		if (fnExpr:anonParams:length() > 0) {
			local Parameter is p: fnExpr:anonParams:get(index: 0);
			self:localVars:set(key: p:getName(), value: self:formatTypeString(t: p:getType()));
			local String is pCType: self:cTypeFor(typeName: p:getType():getName());
			paramDecl: "        " . pCType . " " . self:cIdent(name: p:getName()) . " = (" . pCType . ")(intptr_t)_a_" . id . "->items[_i_" . id . "];\n";
		}

		local String is bodyC: "";
		fnExpr:anonBody:each(action: local Function(Statement is s){
			bodyC: bodyC . self:generateStatement(stmt: s);
		});

		self:localVars: savedVars;
		self:inlineReturnVar: savedRetVar;
		self:inlineReturnLabel: savedRetLbl;

		local String is arrVar: "_a_" . id;
		local String is idxVar: "_i_" . id;
		local String is predVar: "_pred_" . id;
		local String is nextLbl: "_loop_next_" . id;

		if (mode == "each") {
			local String is out: "({ SpecArray* " . arrVar . " = " . targetC . "; if (" . arrVar . ") { for (size_t " . idxVar . " = 0; " . idxVar . " < " . arrVar . "->length; " . idxVar . "++) {\n";
			out: out . paramDecl . bodyC . "        " . nextLbl . ": ;\n    } } })";
			return out;
		}
		if (mode == "filter") {
			local String is outVar: "_out_" . id;
			local String is out: "({ SpecArray* " . arrVar . " = " . targetC . "; SpecArray* " . outVar . " = spec_array_new(); if (" . arrVar . ") { for (size_t " . idxVar . " = 0; " . idxVar . " < " . arrVar . "->length; " . idxVar . "++) {\n";
			out: out . paramDecl . "        bool " . predVar . " = false;\n" . bodyC . "        " . nextLbl . ": ;\n        if (" . predVar . ") spec_array_add(" . outVar . ", " . arrVar . "->items[" . idxVar . "]);\n    } } " . outVar . "; })";
			return out;
		}
		if (mode == "count") {
			local String is cntVar: "_cnt_" . id;
			local String is out: "({ SpecArray* " . arrVar . " = " . targetC . "; long long " . cntVar . " = 0; if (" . arrVar . ") { for (size_t " . idxVar . " = 0; " . idxVar . " < " . arrVar . "->length; " . idxVar . "++) {\n";
			out: out . paramDecl . "        bool " . predVar . " = false;\n" . bodyC . "        " . nextLbl . ": ;\n        if (" . predVar . ") " . cntVar . "++;\n    } } " . cntVar . "; })";
			return out;
		}
		if (mode == "any") {
			local String is fndVar: "_fnd_" . id;
			local String is out: "({ SpecArray* " . arrVar . " = " . targetC . "; bool " . fndVar . " = false; if (" . arrVar . ") { for (size_t " . idxVar . " = 0; " . idxVar . " < " . arrVar . "->length; " . idxVar . "++) {\n";
			out: out . paramDecl . "        bool " . predVar . " = false;\n" . bodyC . "        " . nextLbl . ": ;\n        if (" . predVar . ") { " . fndVar . " = true; break; }\n    } } " . fndVar . "; })";
			return out;
		}
		if (mode == "map") {
			local String is outVar: "_out_" . id;
			local String is retCType: self:cTypeFor(typeName: fnExpr:anonReturnType:getName());
			if (retCType == "void") { retCType: "void*"; }
			local String is out: "({ SpecArray* " . arrVar . " = " . targetC . "; SpecArray* " . outVar . " = spec_array_new(); if (" . arrVar . ") { for (size_t " . idxVar . " = 0; " . idxVar . " < " . arrVar . "->length; " . idxVar . "++) {\n";
			out: out . paramDecl . "        " . retCType . " " . predVar . " = 0;\n" . bodyC . "        " . nextLbl . ": ;\n        spec_array_add(" . outVar . ", (void*)(intptr_t)(" . predVar . "));\n    } } " . outVar . "; })";
			return out;
		}
		return "0";
	}

	replace local Function of String is generateInlineArrayFold(String is targetC, Expression is initExpr, Expression is fnExpr){
		self:anonCounter: self:anonCounter + 1;
		local Int is id: self:anonCounter;
		local String is savedRetVar: self:inlineReturnVar;
		local String is savedRetLbl: self:inlineReturnLabel;

		local Map of String to String is savedVars: Map:init();
		local Array of String is outerKeys: self:localVars:keys();
		outerKeys:each(action: local Function(String is k){
			savedVars:set(key: k, value: self:localVars:getString(key: k, default: ""));
		});

		local String is accVar: "_acc_" . id;
		local String is nextLbl: "_loop_next_" . id;
		local String is arrVar: "_a_" . id;
		local String is idxVar: "_i_" . id;

		local String is initC: self:generateExpression(expr: initExpr);
		local String is accTypeName: self:inferTargetType(expr: initExpr);
		if (accTypeName == "" && fnExpr:anonReturnType:getName() != "Void" && fnExpr:anonReturnType:getName() != "void") {
			accTypeName: fnExpr:anonReturnType:getName();
		}
		local String is accCType: self:cTypeFor(typeName: accTypeName);
		if (accCType == "void") { accCType: "long long"; }

		self:inlineReturnVar: accVar;
		self:inlineReturnLabel: nextLbl;

		local String is paramDecl: "";
		if (fnExpr:anonParams:length() >= 1) {
			local Parameter is p0: fnExpr:anonParams:get(index: 0);
			self:localVars:set(key: p0:getName(), value: accTypeName);
			paramDecl: paramDecl . "        " . accCType . " " . self:cIdent(name: p0:getName()) . " = " . accVar . ";\n";
		}
		if (fnExpr:anonParams:length() >= 2) {
			local Parameter is p1: fnExpr:anonParams:get(index: 1);
			self:localVars:set(key: p1:getName(), value: self:formatTypeString(t: p1:getType()));
			local String is p1CType: self:cTypeFor(typeName: p1:getType():getName());
			paramDecl: paramDecl . "        " . p1CType . " " . self:cIdent(name: p1:getName()) . " = (" . p1CType . ")(intptr_t)" . arrVar . "->items[" . idxVar . "];\n";
		}

		local String is bodyC: "";
		fnExpr:anonBody:each(action: local Function(Statement is s){
			bodyC: bodyC . self:generateStatement(stmt: s);
		});

		self:localVars: savedVars;
		self:inlineReturnVar: savedRetVar;
		self:inlineReturnLabel: savedRetLbl;

		local String is out: "({ SpecArray* " . arrVar . " = " . targetC . "; " . accCType . " " . accVar . " = " . initC . "; if (" . arrVar . ") { for (size_t " . idxVar . " = 0; " . idxVar . " < " . arrVar . "->length; " . idxVar . "++) {\n";
		out: out . paramDecl . bodyC . "        " . nextLbl . ": ;\n    } } " . accVar . "; })";
		return out;
	}

	replace local Function of String is generateInlineMapEach(String is targetC, Expression is fnExpr){
		self:anonCounter: self:anonCounter + 1;
		local Int is id: self:anonCounter;
		local String is savedRetVar: self:inlineReturnVar;
		local String is savedRetLbl: self:inlineReturnLabel;

		local Map of String to String is savedVars: Map:init();
		local Array of String is outerKeys: self:localVars:keys();
		outerKeys:each(action: local Function(String is k){
			savedVars:set(key: k, value: self:localVars:getString(key: k, default: ""));
		});

		local String is mapVar: "_m_" . id;
		local String is bVar: "_b_" . id;
		local String is eVar: "_e_" . id;
		local String is nextLbl: "_map_next_" . id;

		self:inlineReturnVar: "";
		self:inlineReturnLabel: nextLbl;

		local String is paramDecl: "";
		if (fnExpr:anonParams:length() >= 1) {
			local Parameter is p0: fnExpr:anonParams:get(index: 0);
			self:localVars:set(key: p0:getName(), value: "String");
			paramDecl: paramDecl . "            const char* " . self:cIdent(name: p0:getName()) . " = " . eVar . "->key;\n";
		}
		if (fnExpr:anonParams:length() >= 2) {
			local Parameter is p1: fnExpr:anonParams:get(index: 1);
			self:localVars:set(key: p1:getName(), value: self:formatTypeString(t: p1:getType()));
			local String is p1CType: self:cTypeFor(typeName: p1:getType():getName());
			paramDecl: paramDecl . "            " . p1CType . " " . self:cIdent(name: p1:getName()) . " = (" . p1CType . ")(intptr_t)" . eVar . "->value;\n";
		}

		local String is bodyC: "";
		fnExpr:anonBody:each(action: local Function(Statement is s){
			bodyC: bodyC . self:generateStatement(stmt: s);
		});

		self:localVars: savedVars;
		self:inlineReturnVar: savedRetVar;
		self:inlineReturnLabel: savedRetLbl;

		local String is out: "({ SpecMap* " . mapVar . " = " . targetC . "; if (" . mapVar . ") { for (size_t " . bVar . " = 0; " . bVar . " < SPEC_MAP_BUCKETS; " . bVar . "++) { for (SpecMapEntry* " . eVar . " = " . mapVar . "->buckets[" . bVar . "]; " . eVar . "; " . eVar . " = " . eVar . "->next) {\n";
		out: out . paramDecl . bodyC . "            " . nextLbl . ": ;\n        } } } })";
		return out;
	}

	replace local Function of String is generateInlineWhileCondition(Expression is evalExpr, Expression is iterExpr){
		self:anonCounter: self:anonCounter + 1;
		local Int is id: self:anonCounter;
		local String is savedRetVar: self:inlineReturnVar;
		local String is savedRetLbl: self:inlineReturnLabel;

		local String is evVar: "_ev_" . id;
		local String is evLbl: "_ev_done_" . id;
		self:inlineReturnVar: evVar;
		self:inlineReturnLabel: evLbl;
		local String is evalBodyC: "";
		evalExpr:anonBody:each(action: local Function(Statement is s){
			evalBodyC: evalBodyC . self:generateStatement(stmt: s);
		});

		local String is itLbl: "_it_done_" . id;
		self:inlineReturnVar: "";
		self:inlineReturnLabel: itLbl;
		local String is iterBodyC: "";
		iterExpr:anonBody:each(action: local Function(Statement is s){
			iterBodyC: iterBodyC . self:generateStatement(stmt: s);
		});

		self:inlineReturnVar: savedRetVar;
		self:inlineReturnLabel: savedRetLbl;

		local String is out: "({ while (1) {\n        bool " . evVar . " = false;\n" . evalBodyC . "        " . evLbl . ": ;\n        if (!" . evVar . ") break;\n" . iterBodyC . "        " . itLbl . ": ;\n    } })";
		return out;
	}

	class PathChainLoop extends Loop{
		local Array of String is segs;
		local CBackendUtils is utils;
		local Int is idx: 1;
		local String is res: "";

		replace local Function is init(Array of String is segs, String is rootC, CBackendUtils is utils){
			self:segs: segs;
			self:res: rootC;
			self:utils: utils;
			self:idx: 1;
		}

		replace local Function of Boolean is evaluate(){
			return self:idx < self:segs:length();
		}

		replace local Function of Boolean is iteration(LoopControl is c){
			self:res: self:res . "->" . self:utils:cIdent(name: self:segs:get(index: self:idx));
			self:idx: self:idx + 1;
			return true;
		}
	}

	## Generates C code for an expression node.
	##
	## @param expr: [Expression] AST node.
	## @return: C expression code string.
	replace local Function of String is generateExpression(Expression is expr){
		local String is kind: expr:getKind();

		when (kind) {
			is "ARRAY": {
				local String is res: "({ SpecArray* _arr = spec_array_new();";
				expr:arrayItems:each(action: local Function(Expression is item){
					local String is itemC: self:generateExpression(expr: item);
					res: res . " spec_array_add(_arr, (void*)(" . itemC . "));";
				});
				res: res . " _arr; })";
				return res;
			}
			is "MAP": {
				local String is res: "({ SpecMap* _map = spec_map_new();";
				local Int is idx: 0;
				expr:mapKeys:each(action: local Function(Expression is kExpr){
					local Expression is vExpr: expr:mapValues:get(index: idx);
					local String is kC: self:generateExpression(expr: kExpr);
					local String is vC: self:generateExpression(expr: vExpr);
					if (self:isStringExpr(expr: vExpr)) {
						res: res . " spec_map_set(_map, " . kC . ", " . vC . ");";
					} else {
						res: res . " spec_map_set_any(_map, " . kC . ", (void*)(intptr_t)(" . vC . "));";
					}
					idx: idx + 1;
				});
				res: res . " _map; })";
				return res;
			}
			is "STRING": {
				return "\"" . self:escapeString(s: expr:stringValue) . "\"";
			}
			is "NUMBER": {
				if (expr:stringValue != "") {
					return expr:stringValue;
				}
				return "0";
			}
			is "FLOAT": {
				if (expr:stringValue != "") {
					return expr:stringValue;
				}
				return "0.0";
			}
			is "BOOL": {
				return if (expr:boolValue) "true" else "false";
			}
			is "IDENT": {
				local String is name: expr:stringValue;
				if (name == "self" || name == "true" || name == "false") {
					return name;
				}
				if (self:allEnumVariants:has(key: name)) {
					local String is enumName: self:allEnumVariants:getString(key: name, default: "");
					if (self:allTaggedEnums:has(key: enumName)) {
						return enumName . "_" . self:cIdent(name: name) . "_ctor()";
					}
					return enumName . "_" . self:cIdent(name: name);
				}
				if (self:localVars:has(key: name)) {
					return self:cIdent(name: name);
				}
				if (self:fieldTypes:has(key: name)) {
					return "self->" . self:cIdent(name: name);
				}
				return self:cIdent(name: name);
			}
			is "PATH": {
				local Array of String is segs: expr:pathSegments;
				if (segs:length() == 1) {
					return segs:get(index: 0);
				}
				if (segs:length() >= 2) {
					local String is root: segs:get(index: 0);
					if (self:allEnumNames:has(key: root)) {
						if (self:allTaggedEnums:has(key: root)) {
							return root . "_" . self:cIdent(name: segs:get(index: 1)) . "_ctor()";
						}
						return root . "_" . self:cIdent(name: segs:get(index: 1));
					}
					local String is rootC: self:cIdent(name: root);
					if (!self:localVars:has(key: root) && self:fieldTypes:has(key: root)) {
						rootC: "self->" . rootC;
					}
					local PathChainLoop is pathLoop: PathChainLoop:init(segs: segs, rootC: rootC, utils: self:utils);
					While:run(loop: pathLoop);
					local String is resC: pathLoop:res;
					if (root != "self") {
						local String is resolvedT: expr:getResolvedType();
						local String is rootT: self:localVars:getString(key: root, default: "");
						if (rootT:contains(needle: ":") && !rootT:startsWith(prefix: "Array:") && !rootT:startsWith(prefix: "Map:") && resolvedT != "" && resolvedT != "Any") {
							local String is castT: self:cTypeFor(typeName: resolvedT);
							resC: "((" . castT . ")(intptr_t)(" . resC . "))";
						}
					}
					return resC;
				}
				return "";
			}
			is "BINARY": {
				local String is op: expr:binaryOp;
				when (op) {
					is ".": {
						local String is leftC: self:generateExpression(expr: expr:leftExpr);
						local String is rightC: self:generateExpression(expr: expr:rightExpr);
						local String is leftWrap: self:wrapToString(expr: expr:leftExpr, exprC: leftC);
						local String is rightWrap: self:wrapToString(expr: expr:rightExpr, exprC: rightC);
						return "spec_str_concat(" . leftWrap . ", " . rightWrap . ")";
					}
					is "is", "==": {
						local String is leftC: self:generateExpression(expr: expr:leftExpr);
						local String is rightC: self:generateExpression(expr: expr:rightExpr);
						if (self:isStringExpr(expr: expr:leftExpr) || self:isStringExpr(expr: expr:rightExpr)) {
							return "spec_str_equals(" . leftC . ", " . rightC . ")";
						}
						return "((" . leftC . ") == (" . rightC . "))";
					}
					is "!=": {
						local String is leftC: self:generateExpression(expr: expr:leftExpr);
						local String is rightC: self:generateExpression(expr: expr:rightExpr);
						if (self:isStringExpr(expr: expr:leftExpr) || self:isStringExpr(expr: expr:rightExpr)) {
							return "(!spec_str_equals(" . leftC . ", " . rightC . "))";
						}
						return "((" . leftC . ") != (" . rightC . "))";
					}
					is "<", "<=", ">", ">=", "+", "-", "*", "/", "%", "&&", "||": {
						local String is leftC: self:generateExpression(expr: expr:leftExpr);
						local String is rightC: self:generateExpression(expr: expr:rightExpr);
						return "((" . leftC . ") " . op . " (" . rightC . "))";
					}
					else: {
						return "0";
					}
				}
			}
			is "INDEX": {
				local String is targetC: self:generateExpression(expr: expr:leftExpr);
				local String is indexC: self:generateExpression(expr: expr:rightExpr);
				local String is targetType: self:inferTargetType(expr: expr:leftExpr);
				if (targetType:startsWith(prefix: "Map:") || targetType == "Map") {
					local String is valType: "String";
					if (targetType:startsWith(prefix: "Map:")) {
						local String is afterMap: targetType:substring(start: 4, end: targetType:length());
						local Int is colonIdx: afterMap:indexOf(needle: ":", default: -1);
						if (colonIdx >= 0 && colonIdx + 1 < afterMap:length()) {
							valType: afterMap:substring(start: colonIdx + 1, end: afterMap:length());
						}
					}
					if (valType == "String" || valType == "string") {
						return "spec_map_get_string(" . targetC . ", " . indexC . ", \"\")";
					}
					if (valType == "Int" || valType == "int") {
						return "spec_map_get_int(" . targetC . ", " . indexC . ", 0)";
					}
					if (valType == "Float" || valType == "float") {
						return "spec_map_get_float(" . targetC . ", " . indexC . ", 0.0)";
					}
					if (valType == "Boolean" || valType == "bool") {
						return "spec_map_get_bool(" . targetC . ", " . indexC . ", false)";
					}
					local String is valCType: self:cTypeFor(typeName: valType);
					return "((" . valCType . ")(intptr_t)spec_map_get(" . targetC . ", " . indexC . ", NULL))";
				}
				if (targetType == "Array:String" || targetType == "Array of String") {
					return "((const char*)spec_array_get(" . targetC . ", (size_t)(" . indexC . ")))";
				}
				if (targetType:startsWith(prefix: "Array:") && targetType:length() > 6) {
					local String is elemT: targetType:substring(start: 6, end: targetType:length());
					local String is elemCType: self:cTypeFor(typeName: elemT);
					return "((" . elemCType . ")(intptr_t)spec_array_get(" . targetC . ", (size_t)(" . indexC . ")))";
				}
				return "((long long)(intptr_t)spec_array_get(" . targetC . ", (size_t)(" . indexC . ")))";
			}
			is "UNARY": {
				local String is innerC: self:generateExpression(expr: expr:unaryExpr);
				return "(" . expr:unaryOp . "(" . innerC . "))";
			}
			is "CALL": {
				local String is targetC: self:generateExpression(expr: expr:methodTarget);

				local String is targetType: self:inferTargetType(expr: expr:methodTarget);
				local String is fieldKey: targetC;
				if (targetC:startsWith(prefix: "self->")) {
					fieldKey: targetC:substring(start: 6, end: targetC:length());
				}
				if (targetType == "") {
					targetType: self:localVars:getString(key: fieldKey, default: "");
				}
				if (targetType == "") {
					targetType: self:fieldTypes:getString(key: fieldKey, default: "");
				}

				local String is builtinC: self:builtins:generateBuiltinCall(expr: expr, targetC: targetC, targetType: targetType, cg: self);
				if (builtinC != "") {
					return builtinC;
				}

				# Direct invocation of a Function variable or field: fnVar(arg1, arg2)
				if (targetC == "self" && (self:localVars:has(key: expr:methodName) || self:fieldTypes:has(key: expr:methodName))) {
					local String is fnVarT: self:localVars:getString(key: expr:methodName, default: self:fieldTypes:getString(key: expr:methodName, default: ""));
					if (fnVarT:startsWith(prefix: "Function")) {
						local String is fnPtrC: if (self:localVars:has(key: expr:methodName)) self:cIdent(name: expr:methodName) else "self->" . self:cIdent(name: expr:methodName);
						local String is retTName: if (fnVarT:startsWith(prefix: "Function:") && fnVarT:length() > 9) fnVarT:substring(start: 9, end: fnVarT:length()) else "Void";
						local String is retCType: self:cTypeFor(typeName: retTName);
						local String is pTypesC: "";
						local String is cArgsC: "";
						local Boolean is firstA: true;
						expr:methodArgs:each(action: local Function(NamedArg is arg){
							if (!firstA) {
								pTypesC: pTypesC . ", ";
								cArgsC: cArgsC . ", ";
							}
							local String is aValC: self:generateExpression(expr: arg:getValue());
							local String is aT: self:inferTargetType(expr: arg:getValue());
							local String is aCType: self:cTypeFor(typeName: aT);
							pTypesC: pTypesC . aCType;
							cArgsC: cArgsC . aValC;
							firstA: false;
						});
						if (firstA) { pTypesC: "void"; }
						return "((" . retCType . " (*)(" . pTypesC . "))(" . fnPtrC . "))(" . cArgsC . ")";
					}
				}

				# Tagged enum variant constructor invocation: EnumName:Variant(...) or Variant(...)
				if (self:allEnumVariants:has(key: expr:methodName) && (self:allTaggedEnums:has(key: targetC) || targetC == "self")) {
					local String is eName: self:allEnumVariants:getString(key: expr:methodName, default: "");
					if (self:allTaggedEnums:has(key: eName)) {
						local Member is vMem: self:lookupEnumVariant(enumName: eName, variantName: expr:methodName);
						local Array of Parameter is vParams: vMem:getParameters();
						local String is vArgsC: "";
						local Int is pIdx: 0;
						vParams:each(action: local Function(Parameter is p){
							if (pIdx > 0) { vArgsC: vArgsC . ", "; }
							local String is pName: p:getName();
							local Boolean is matched: false;
							local String is argC: "0";
							expr:methodArgs:each(action: local Function(NamedArg is a){
								if (!matched && a:getName() == pName && pName != "") {
									argC: self:generateExpression(expr: a:getValue());
									matched: true;
								}
							});
							if (!matched && pIdx < expr:methodArgs:length()) {
								local NamedArg is posArg: expr:methodArgs:get(index: pIdx);
								argC: self:generateExpression(expr: posArg:getValue());
								matched: true;
							}
							vArgsC: vArgsC . argC;
							pIdx: pIdx + 1;
						});
						return eName . "_" . self:cIdent(name: expr:methodName) . "(" . vArgsC . ")";
					}
				}

				# Class constructor or static method invocation: ClassName:init(...) or ClassName:method(...)
				if (self:allClassNames:has(key: targetC) && !self:allEnumNames:has(key: targetC)) {
					local String is argsJoined: self:formatCallArguments(className: targetC, methodName: expr:methodName, args: expr:methodArgs);
					if (expr:methodName == "init") {
						return "({ " . targetC . "* _inst = " . targetC . "_new(); " . targetC . "_init(_inst" . argsJoined . "); _inst; })";
					}
					local Member is mDef: self:lookupMethodMember(className: targetC, methodName: expr:methodName);
					if (mDef:getKind() == "METHOD") {
						local String is mRetType: mDef:getType():getName();
						if (mRetType != "" && mRetType != "Void" && mRetType != "void") {
							return targetC . "_" . expr:methodName . "(NULL" . argsJoined . ")";
						}
					}
					return "({ " . targetC . "* _inst = " . targetC . "_new(); " . targetC . "_" . expr:methodName . "(_inst" . argsJoined . "); _inst; })";
				}

				# Instance method invocation
				local String is objType: targetType;
				if (objType == "") {
					objType: self:localVars:getString(key: targetC, default: "");
				}
				if (objType == "") {
					objType: self:fieldTypes:getString(key: targetC, default: "");
				}
				if (objType == "" || objType == "Any" || targetC == "self") {
					objType: self:currentClassName;
				}
				local String is fullObjType: objType;
				if (objType:startsWith(prefix: "Array:")) {
					objType: "Array";
				} else if (objType:startsWith(prefix: "Map:")) {
					objType: "Map";
				} else if (objType:contains(needle: ":")) {
					local Array of String is parts: objType:split(delimiter: ":");
					objType: parts:get(index: 0);
				}
				local String is dispatchCls: self:findMethodImplementingClass(className: objType, methodName: expr:methodName, paramCount: -1);
				local String is targetExprC: targetC;
				if (dispatchCls != "" && dispatchCls != objType) {
					objType: dispatchCls;
					targetExprC: "((" . dispatchCls . "*)" . targetC . ")";
				}
				local String is callStr: objType . "_" . expr:methodName . "(" . targetExprC . self:formatCallArguments(className: fullObjType, methodName: expr:methodName, args: expr:methodArgs) . ")";
				local Member is targetM: self:lookupMethodMember(className: objType, methodName: expr:methodName);
				local Class is targetCls: self:findClass(name: objType);
				if (targetM:getKind() == "METHOD" && targetCls:getTypeParams():length() > 0) {
					local String is rawRet: self:formatTypeString(t: targetM:getType());
					if (targetCls:getTypeParams():indexOf(search: rawRet, default: -1) >= 0) {
						local String is resolvedRet: expr:getResolvedType();
						if (resolvedRet != "" && resolvedRet != "Any") {
							local String is castCType: self:cTypeFor(typeName: resolvedRet);
							callStr: "((" . castCType . ")(intptr_t)(" . callStr . "))";
						}
					}
				}
				return callStr;
			}
			is "IF_ELSE": {
				local String is condC: self:generateExpression(expr: expr:condExpr);
				local String is thenC: self:generateExpression(expr: expr:thenExpr);
				local String is elseC: self:generateExpression(expr: expr:elseExpr);
				return "((" . condC . ") ? (" . thenC . ") : (" . elseC . "))";
			}
			is "WHEN": {
				local String is subjC: self:generateExpression(expr: expr:whenSubject);
				local String is chain: "0";
				expr:whenArms:each(action: local Function(WhenArm is arm){
					if (arm:isElse && arm:hasValueExpr) {
						chain: self:generateExpression(expr: arm:valueExpr);
					}
				});
				expr:whenArms:each(action: local Function(WhenArm is arm){
					if (!arm:isElse && arm:hasValueExpr) {
						local String is bindsC: self:generateWhenBindings(subjC: subjC, arm: arm);
						local String is armVal: self:generateExpression(expr: arm:valueExpr);
						if (bindsC != "") {
							armVal: "({ " . bindsC . " " . armVal . "; })";
						}
						local String is condOr: "";
						arm:conditions:each(action: local Function(Expression is c){
							local String is cmp: self:generateWhenCondition(subjExpr: expr:whenSubject, subjC: subjC, c: c);
							if (condOr == "") {
								condOr: cmp;
							} else {
								condOr: condOr . " || " . cmp;
							}
						});
						chain: "((" . condOr . ") ? (" . armVal . ") : (" . chain . "))";
					}
				});
				return chain;
			}
			is "ANON_FN": {
				self:anonCounter: self:anonCounter + 1;
				local Int is id: self:anonCounter;
				local String is fnName: "_anon_fn_" . id;
				local String is retC: self:cTypeFor(typeName: expr:anonReturnType:getName());

				local Map of String to String is savedVars: Map:init();
				local Array of String is outerKeys: self:localVars:keys();
				outerKeys:each(action: local Function(String is k){
					savedVars:set(key: k, value: self:localVars:getString(key: k, default: ""));
				});

				local String is paramsC: "";
				local Boolean is firstP: true;
				local Array of String is paramNames: [];
				expr:anonParams:each(action: local Function(Parameter is p){
					paramNames:add(item: p:getName());
					self:localVars:set(key: p:getName(), value: self:formatVarTypeString(t: p:getType()));
					if (!firstP) { paramsC: paramsC . ", "; }
					paramsC: paramsC . self:cTypeFor(typeName: p:getType():getName()) . " " . self:cIdent(name: p:getName());
					firstP: false;
				});
				if (firstP) { paramsC: "void"; }

				local String is savedRetVar: self:inlineReturnVar;
				local String is savedRetLbl: self:inlineReturnLabel;
				self:inlineReturnVar: "";
				self:inlineReturnLabel: "";
				local String is bodyC: "";
				expr:anonBody:each(action: local Function(Statement is s){
					bodyC: bodyC . self:generateStatement(stmt: s);
				});
				self:inlineReturnVar: savedRetVar;
				self:inlineReturnLabel: savedRetLbl;
				self:localVars: savedVars;

				local String is capDecls: "";
				local String is capBinds: "";
				local String is capAssigns: "";
				if (self:inMethod && self:currentClassName != "" && !self:isBuiltinClass(name: self:currentClassName) && !self:allEnumNames:has(key: self:currentClassName) && bodyC:contains(needle: "self")) {
					capDecls: capDecls . "static " . self:currentClassName . "* _cap_" . id . "_self = NULL;\n";
					capBinds: capBinds . "    " . self:currentClassName . "* self = _cap_" . id . "_self;\n    (void)self;\n";
					capAssigns: capAssigns . " _cap_" . id . "_self = self;";
				}
				outerKeys:each(action: local Function(String is k){
					if (paramNames:indexOf(search: k, default: -1) < 0) {
						local String is cVar: self:cIdent(name: k);
						if (bodyC:contains(needle: cVar)) {
							local String is vType: savedVars:getString(key: k, default: "");
							local String is vCType: self:cTypeFor(typeName: vType);
							if (vCType != "void" && vCType != "") {
								capDecls: capDecls . "static " . vCType . " _cap_" . id . "_" . cVar . ";\n";
								capBinds: capBinds . "    " . vCType . " " . cVar . " = _cap_" . id . "_" . cVar . ";\n    (void)" . cVar . ";\n";
								capAssigns: capAssigns . " _cap_" . id . "_" . cVar . " = " . cVar . ";";
							}
						}
					}
				});

				self:helperFunctions: self:helperFunctions . capDecls . "static " . retC . " " . fnName . "(" . paramsC . ") {\n" . capBinds . bodyC . "}\n\n";
				if (capAssigns != "") {
					return "({" . capAssigns . " " . fnName . "; })";
				}
				return fnName;
			}
			else: {
				return "0";
			}
		}
	}

	## Resolves a simple local variable or `self` field expression to its C identifier without side effects.
	##
	## @param expr: Target [Expression] node.
	## @return: C lvalue string if simple variable/field, or empty string otherwise.
	replace local Function of String is tryGenerateTargetOnly(Expression is expr){
		if (expr:getKind() == "IDENT") {
			if (self:localVars:has(key: expr:stringValue)) {
				return self:cIdent(name: expr:stringValue);
			}
			if (self:inMethod && self:fieldTypes:has(key: expr:stringValue)) {
				return "self->" . self:cIdent(name: expr:stringValue);
			}
			return self:cIdent(name: expr:stringValue);
		}
		if (expr:getKind() == "PATH" && expr:pathSegments:length() == 2 && expr:pathSegments:get(index: 0) == "self") {
			return "self->" . self:cIdent(name: expr:pathSegments:get(index: 1));
		}
		return "";
	}

	## Optimizes left-recursive string concatenation chains (`s: s . a . b`) into amortized O(1) `spec_str_append` calls.
	##
	## @param expr: Right-hand side assignment [Expression].
	## @param targetC: Generated C lvalue of the assignment target.
	## @return: `spec_str_append` call chain string if optimizable, or empty string otherwise.
	replace local Function of String is tryGenerateAppendChain(Expression is expr, String is targetC){
		if (targetC == "") {
			return "";
		}
		if (expr:getKind() == "BINARY" && expr:binaryOp == ".") {
			local String is leftTarget: self:tryGenerateTargetOnly(expr: expr:leftExpr);
			if (leftTarget == targetC) {
				local String is rhsC: self:wrapToString(expr: expr:rightExpr, exprC: self:generateExpression(expr: expr:rightExpr));
				if (rhsC:contains(needle: targetC)) {
					return "";
				}
				return "spec_str_append(" . targetC . ", " . rhsC . ")";
			}
			local String is innerChain: self:tryGenerateAppendChain(expr: expr:leftExpr, targetC: targetC);
			if (innerChain != "") {
				local String is rhsC: self:wrapToString(expr: expr:rightExpr, exprC: self:generateExpression(expr: expr:rightExpr));
				if (rhsC:contains(needle: targetC)) {
					return "";
				}
				return "spec_str_append(" . innerChain . ", " . rhsC . ")";
			}
		}
		return "";
	}

	## Generates C code for a statement node.
	##
	## @param stmt: [Statement] AST node.
	## @return: C statement code block.
	replace local Function of String is generateStatement(Statement is stmt){
		local String is kind: stmt:getKind();

		when (kind) {
			is "VAR_DECL": {
				self:localVars:set(key: stmt:varName, value: self:formatVarTypeString(t: stmt:varType));
				local String is vTypeName: stmt:varType:getName();
				local String is cType: self:cTypeFor(typeName: vTypeName);
				local String is varName: self:cIdent(name: stmt:varName);
				if (stmt:hasInit) {
					local String is initC: self:generateExpression(expr: stmt:initExpr);
					if (cType:length() > 0 && cType:charAt(index: cType:length() - 1) == "*" && cType != "const char*" && cType != "SpecArray*" && cType != "SpecMap*") {
						initC: "(" . cType . ")(" . initC . ")";
					}
					if (cType == "const char*") {
						initC: "spec_str_clone_if_buffered(" . initC . ")";
					}
					return "    " . cType . " " . varName . " = " . initC . ";\n";
				}
				if (vTypeName == "String" || vTypeName == "string") {
					return "    " . cType . " " . varName . " = \"\";\n";
				}
				if (vTypeName == "Array") {
					return "    " . cType . " " . varName . " = spec_array_new();\n";
				}
				if (vTypeName == "Map") {
					return "    " . cType . " " . varName . " = spec_map_new();\n";
				}
				return "    " . cType . " " . varName . " = 0;\n";
			}
			is "ASSIGN": {
				if (stmt:assignTarget:getKind() == "INDEX") {
					local String is containerC: self:generateExpression(expr: stmt:assignTarget:leftExpr);
					local String is idxC: self:generateExpression(expr: stmt:assignTarget:rightExpr);
					local String is valC: self:generateExpression(expr: stmt:assignValue);
					local String is containerType: self:inferTargetType(expr: stmt:assignTarget:leftExpr);
					if (containerType:startsWith(prefix: "Map:") || containerType == "Map") {
						if (self:isStringExpr(expr: stmt:assignValue)) {
							return "    spec_map_set(" . containerC . ", " . idxC . ", " . valC . ");\n";
						}
						return "    spec_map_set_any(" . containerC . ", " . idxC . ", (void*)(intptr_t)(" . valC . "));\n";
					}
					return "    spec_array_set(" . containerC . ", " . idxC . ", (void*)(intptr_t)(" . valC . "));\n";
				}
				local String is targetC: self:generateExpression(expr: stmt:assignTarget);
				local String is appendC: self:tryGenerateAppendChain(expr: stmt:assignValue, targetC: targetC);
				if (appendC != "") {
					return "    " . targetC . " = " . appendC . ";\n";
				}
				local String is valC: self:generateExpression(expr: stmt:assignValue);
				local String is lhsType: self:inferTargetType(expr: stmt:assignTarget);
				local Class is curCls: self:findClass(name: self:currentClassName);
				if (curCls:getTypeParams():indexOf(search: lhsType, default: -1) >= 0) {
					valC: "(void*)(intptr_t)(" . valC . ")";
				} else if (lhsType == "String" || lhsType == "string") {
					valC: "spec_str_clone_if_buffered(" . valC . ")";
				}
				return "    " . targetC . " = " . valC . ";\n";
			}
			is "IF": {
				local String is condC: self:generateExpression(expr: stmt:ifCondition);
				local String is out: "    if (" . condC . ") {\n";
				stmt:thenBranch:each(action: local Function(Statement is s){
					out: out . "    " . self:generateStatement(stmt: s);
				});
				if (stmt:hasElse) {
					out: out . "    } else {\n";
					stmt:elseBranch:each(action: local Function(Statement is s){
						out: out . "    " . self:generateStatement(stmt: s);
					});
				}
				out: out . "    }\n";
				return out;
			}
			is "RETURN": {
				if (self:inlineReturnLabel != "") {
					if (stmt:hasReturnExpr && self:inlineReturnVar != "") {
						local String is retC: self:generateExpression(expr: stmt:returnExpr);
						return "    " . self:inlineReturnVar . " = " . retC . "; goto " . self:inlineReturnLabel . ";\n";
					}
					return "    goto " . self:inlineReturnLabel . ";\n";
				}
				if (stmt:hasReturnExpr) {
					local String is retC: self:generateExpression(expr: stmt:returnExpr);
					local Class is curCls: self:findClass(name: self:currentClassName);
					if (curCls:getTypeParams():indexOf(search: self:currentMethodReturnType, default: -1) >= 0) {
						retC: "(void*)(intptr_t)(" . retC . ")";
					}
					return "    return " . retC . ";\n";
				}
				return "    return;\n";
			}
			is "WHEN": {
				local String is subjC: self:generateExpression(expr: stmt:whenSubject);
				local String is out: "";
				local Boolean is first: true;
				stmt:whenArms:each(action: local Function(WhenArm is arm){
					local String is bindsC: "";
					if (arm:isElse) {
						out: out . "    } else {\n";
					} else {
						local String is condOr: "";
						arm:conditions:each(action: local Function(Expression is c){
							local String is cmp: self:generateWhenCondition(subjExpr: stmt:whenSubject, subjC: subjC, c: c);
							if (condOr == "") {
								condOr: cmp;
							} else {
								condOr: condOr . " || " . cmp;
							}
						});
						bindsC: self:generateWhenBindings(subjC: subjC, arm: arm);
						if (first) {
							out: out . "    if (" . condOr . ") {\n";
							first: false;
						} else {
							out: out . "    } else if (" . condOr . ") {\n";
						}
						out: out . bindsC;
					}
					arm:body:each(action: local Function(Statement is s){
						out: out . "    " . self:generateStatement(stmt: s);
					});
				});
				out: out . "    }\n";
				return out;
			}
			is "EXPR": {
				local String is exprC: self:generateExpression(expr: stmt:exprStmt);
				return "    " . exprC . ";\n";
			}
			is "CLASS": {
				return "";
			}
			else: {
				return "";
			}
		}
	}

	## Generates C code for a method definition.
	##
	## @param classDef: Enclosing [Class] definition.
	## @param method: Method [Member] descriptor.
	## @return: C method implementation string.
	replace local Function of String is generateMethod(Class is classDef, Member is method){
		self:inMethod: true;
		self:currentMethodReturnType: self:formatTypeString(t: method:getType());
		local String is retType: self:resolveReturnType(t: method:getType());
		if (retType == "void") {
			if (method:getName() == "evaluate" || method:getName() == "iteration") {
				retType: "bool";
			}
		}

		self:localVars: Map:init();
		method:getParameters():each(action: local Function(Parameter is p){
			self:localVars:set(key: p:getName(), value: self:formatVarTypeString(t: p:getType()));
		});

		local String is out: retType . " " . classDef:getName() . "_" . method:getName() . "(" . classDef:getName() . "* self";
		local String is callArgs: "";
		method:getParameters():each(action: local Function(Parameter is p){
			out: out . ", " . self:cTypeFor(typeName: p:getType():getName()) . " " . self:cIdent(name: p:getName());
			callArgs: callArgs . ", " . self:cIdent(name: p:getName());
		});
		out: out . ") {\n";

		if (method:getName() != "init") {
			local Int is paramCount: method:getParameters():length();
			self:programClasses:each(action: local Function(Class is subCls){
				if (subCls:getName() != classDef:getName() && self:isSubclassOf(subName: subCls:getName(), baseName: classDef:getName())) {
					local String is implCls: self:findMethodImplementingClass(className: subCls:getName(), methodName: method:getName(), paramCount: paramCount);
					if (implCls != "" && implCls != classDef:getName()) {
						out: out . "    if (self && self->_type_name && strcmp(self->_type_name, \"" . subCls:getName() . "\") == 0) {\n";
						if (retType == "void") {
							out: out . "        " . implCls . "_" . method:getName() . "((" . implCls . "*)self" . callArgs . ");\n        return;\n";
						} else {
							out: out . "        return " . implCls . "_" . method:getName() . "((" . implCls . "*)self" . callArgs . ");\n";
						}
						out: out . "    }\n";
					}
				}
			});
		}

		method:getBody():each(action: local Function(Statement is stmt){
			out: out . self:generateStatement(stmt: stmt);
		});

		if (method:getBody():length() == 0 && retType != "void") {
			if (retType == "const char*") {
				out: out . "    return \"\";\n";
			} else {
				out: out . "    return 0;\n";
			}
		}

		out: out . "}\n\n";
		self:inMethod: false;
		return out;
	}

	## Generates the C `main` function entry point.
	##
	## @param entryClass: Application entry point class name.
	## @return: C main function text.
	replace local Function of String is generateMain(String is entryClass){
		local String is m: "/* Application Entry Point */\n";
		m: m . "int main(int argc, char** argv) {\n";
		m: m . "    srand((unsigned int)time(NULL));\n";
		m: m . "    SpecMap* args = spec_map_new();\n";
		m: m . "    for (int i = 1; i < argc; i++) {\n";
		m: m . "        if (strncmp(argv[i], \"--\", 2) == 0) {\n";
		m: m . "            const char* key = argv[i] + 2;\n";
		m: m . "            const char* val = \"true\";\n";
		m: m . "            if (i + 1 < argc && argv[i + 1][0] != '-') {\n";
		m: m . "                val = argv[++i];\n";
		m: m . "            }\n";
		m: m . "            spec_map_set(args, key, val);\n";
		m: m . "        } else if (argv[i][0] == '-' && argv[i][1] != '\\0') {\n";
		m: m . "            const char* key = argv[i] + 1;\n";
		m: m . "            const char* val = \"true\";\n";
		m: m . "            if (i + 1 < argc && argv[i + 1][0] != '-') {\n";
		m: m . "                val = argv[++i];\n";
		m: m . "            }\n";
		m: m . "            spec_map_set(args, key, val);\n";
		m: m . "        }\n";
		m: m . "    }\n";
		m: m . "    " . entryClass . "* app = " . entryClass . "_new();\n";
		m: m . "    " . entryClass . "_init(app, args);\n";
		m: m . "    spec_drain_async_tasks();\n";
		m: m . "    return 0;\n";
		m: m . "}\n";
		return m;
	}

	replace local Function is collectClassesFromStatement(Statement is stmt, Array of Class is acc){
		when (stmt:getKind()) {
			is "CLASS": {
				self:collectClasses(c: stmt:nestedClass, acc: acc);
			}
			is "IF": {
				stmt:thenBranch:each(action: local Function(Statement is s){
					self:collectClassesFromStatement(stmt: s, acc: acc);
				});
				if (stmt:hasElse) {
					stmt:elseBranch:each(action: local Function(Statement is s){
						self:collectClassesFromStatement(stmt: s, acc: acc);
					});
				}
			}
			is "WHEN": {
				stmt:whenArms:each(action: local Function(WhenArm is arm){
					arm:body:each(action: local Function(Statement is s){
						self:collectClassesFromStatement(stmt: s, acc: acc);
					});
				});
			}
			else: {}
		}
	}

	replace local Function is collectClasses(Class is c, Array of Class is acc){
		acc:add(item: c);
		c:getMembers():each(action: local Function(Member is m){
			when (m:getMemberKind()) {
				is CLASS: {
					self:collectClasses(c: m:getNestedClass(), acc: acc);
				}
				is METHOD: {
					m:getBody():each(action: local Function(Statement is s){
						self:collectClassesFromStatement(stmt: s, acc: acc);
					});
				}
				else: {}
			}
		});
	}

	## Translates a complete parsed program AST into a standalone C11 translation unit.
	##
	## @param program: Parsed [ProgramNode] AST.
	## @param entryClass: Application entry point class name.
	## @return: Complete C11 source code string.
	replace local Function of String is generateProgram(ProgramNode is program, String is entryClass){
		local Array of Class is flattenedClasses: [];
		program:getClasses():each(action: local Function(Class is c){
			self:collectClasses(c: c, acc: flattenedClasses);
		});
		self:programClasses: flattenedClasses;

		self:allClassNames: Map:init();
		self:allEnumNames: Map:init();
		self:allEnumVariants: Map:init();
		self:allStringBackedEnums: Map:init();
		self:allTaggedEnums: Map:init();
		flattenedClasses:each(action: local Function(Class is c){
			self:allClassNames:set(key: c:getName(), value: "true");
			if (c:getBaseClass() == "Enum") {
				self:allEnumNames:set(key: c:getName(), value: "true");
				c:getMembers():each(action: local Function(Member is m){
					self:allEnumVariants:set(key: m:getName(), value: c:getName());
					if (m:getParameters():length() > 0) {
						self:allTaggedEnums:set(key: c:getName(), value: "true");
					}
					if (m:getType():getName() == "String" || m:getType():getName() == "string") {
						self:allStringBackedEnums:set(key: c:getName(), value: "true");
					}
				});
			}
		});

		self:declGen:setEnumNames(names: self:allEnumNames);
		self:declGen:setTaggedEnums(names: self:allTaggedEnums);
		self:builtins:setEnumNames(names: self:allEnumNames);

		local String is enums: self:declGen:generateEnums(classes: flattenedClasses);
		local String is decls: self:declGen:generateForwardDeclarations(classes: flattenedClasses);
		local String is structs: self:declGen:generateStructs(classes: flattenedClasses);
		local String is ctors: self:generateConstructors(classes: flattenedClasses);

		local String is methods: "";
		flattenedClasses:each(action: local Function(Class is c){
			if (!self:isBuiltinClass(name: c:getName())) {
				self:currentClassName: c:getName();
				self:fieldTypes: Map:init();
				local Array of Member is allFields: [];
				self:declGen:collectStructFields(c: c, allClasses: flattenedClasses, acc: allFields);
				allFields:each(action: local Function(Member is m){
					self:fieldTypes:set(key: m:getName(), value: self:formatVarTypeString(t: m:getType()));
				});

				local Boolean is hasInit: false;
				c:getMembers():each(action: local Function(Member is m){
					when (m:getMemberKind()) {
						is METHOD: {
							if (m:getName() == "init") { hasInit: true; }
							methods: methods . self:generateMethod(classDef: c, method: m);
						}
						else: {}
					}
				});
				if (!hasInit && c:getBaseClass() != "Enum") {
					methods: methods . "void " . c:getName() . "_init(" . c:getName() . "* self) {\n    /* default initializer */\n}\n\n";
				}
			}
		});

		local String is mainFn: self:generateMain(entryClass: entryClass);

		local String is cSource: "";
		cSource: cSource . self:generatePrelude();
		cSource: cSource . enums;
		cSource: cSource . decls;
		cSource: cSource . structs;
		cSource: cSource . self:helperFunctions;
		cSource: cSource . ctors;
		cSource: cSource . methods;
		cSource: cSource . mainFn;
		return cSource;
	}

}
