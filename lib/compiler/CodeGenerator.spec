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
		self:helperFunctions: "";
		self:anonCounter: 0;
		self:inlineReturnVar: "";
		self:inlineReturnLabel: "";
	}

	replace local Function of String is cTypeFor(String is typeName){
		if (self:allEnumNames:has(key: typeName)) {
			return typeName;
		}
		return self:utils:cTypeFor(typeName: typeName);
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
		if (baseName == "Array" && t:getParams():length() > 0) {
			local Type is elemType: t:getParams():get(index: 0);
			return "Array:" . elemType:getName();
		}
		if (baseName == "Map" && t:getParams():length() >= 2) {
			local Type is kType: t:getParams():get(index: 0);
			local Type is vType: t:getParams():get(index: 1);
			return "Map:" . kType:getName() . ":" . vType:getName();
		}
		if (baseName == "Function") {
			if (t:getParams():length() > 0) {
				local Type is ret: t:getParams():get(index: 0);
				return self:formatTypeString(t: ret);
			}
			return "void";
		}
		return baseName;
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
		local Class is cls: self:findClass(name: className);
		if (cls:getName() == "") {
			return "";
		}
		local FieldMemberLoop is fl: FieldMemberLoop:init(members: cls:getMembers(), fieldName: fieldName);
		While:run(loop: fl);
		if (fl:found) {
			local Member is foundM: fl:res;
			return self:formatTypeString(t: foundM:getType());
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

	replace local Function of String is lookupMethodReturnType(String is className, String is methodName){
		if (className == "" || className == "Any") {
			return "";
		}
		if (methodName == "init" && self:allClassNames:has(key: className) && !self:allEnumNames:has(key: className)) {
			return className;
		}
		local Class is cls: self:findClass(name: className);
		if (cls:getName() == "") {
			return "";
		}
		local MethodMemberLoop is ml: MethodMemberLoop:init(members: cls:getMembers(), methodName: methodName);
		While:run(loop: ml);
		if (ml:found) {
			local Member is foundM: ml:res;
			return self:formatTypeString(t: foundM:getType());
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
		return "0";
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
						return root . "_" . self:cIdent(name: segs:get(index: 1));
					}
					local String is rootC: self:cIdent(name: root);
					if (!self:localVars:has(key: root) && self:fieldTypes:has(key: root)) {
						rootC: "self->" . rootC;
					}
					local PathChainLoop is pathLoop: PathChainLoop:init(segs: segs, rootC: rootC, utils: self:utils);
					While:run(loop: pathLoop);
					return pathLoop:res;
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
				if (targetType == "Array:String" || targetType == "Array of String") {
					return "((const char*)spec_array_get(" . targetC . ", (size_t)(" . indexC . ")))";
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

				# Class constructor invocation: ClassName:init(...)
				if (self:allClassNames:has(key: targetC) && !self:allEnumNames:has(key: targetC)) {
					local String is argsJoined: "";
					expr:methodArgs:each(action: local Function(NamedArg is arg){
						argsJoined: argsJoined . ", " . self:generateExpression(expr: arg:getValue());
					});
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
				if (objType:startsWith(prefix: "Array:")) {
					objType: "Array";
				}
				if (objType:startsWith(prefix: "Map:")) {
					objType: "Map";
				}
				local String is callStr: objType . "_" . expr:methodName . "(" . targetC;
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					callStr: callStr . ", " . self:generateExpression(expr: arg:getValue());
				});
				callStr: callStr . ")";
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
						local String is armVal: self:generateExpression(expr: arm:valueExpr);
						local String is condOr: "";
						arm:conditions:each(action: local Function(Expression is c){
							local String is cVal: self:generateExpression(expr: c);
							local String is cmp: "";
							if (self:isStringExpr(expr: expr:whenSubject)) {
								cmp: "spec_str_equals(" . subjC . ", " . cVal . ")";
							} else {
								cmp: "((" . subjC . ") == (" . cVal . "))";
							}
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
				local String is fnName: "_anon_fn_" . self:anonCounter;
				local String is retC: self:cTypeFor(typeName: expr:anonReturnType:getName());
				local String is paramsC: "";
				local Boolean is firstP: true;
				expr:anonParams:each(action: local Function(Parameter is p){
					self:localVars:set(key: p:getName(), value: self:formatTypeString(t: p:getType()));
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
				self:helperFunctions: self:helperFunctions . "static " . retC . " " . fnName . "(" . paramsC . ") {\n" . bodyC . "}\n\n";
				return fnName;
			}
			else: {
				return "0";
			}
		}
	}

	## Generates C code for a statement node.
	##
	## @param stmt: [Statement] AST node.
	## @return: C statement code block.
	replace local Function of String is generateStatement(Statement is stmt){
		local String is kind: stmt:getKind();

		when (kind) {
			is "VAR_DECL": {
				self:localVars:set(key: stmt:varName, value: self:formatTypeString(t: stmt:varType));
				local String is vTypeName: stmt:varType:getName();
				local String is cType: self:cTypeFor(typeName: vTypeName);
				local String is varName: self:cIdent(name: stmt:varName);
				if (stmt:hasInit) {
					local String is initC: self:generateExpression(expr: stmt:initExpr);
					if (cType:length() > 0 && cType:charAt(index: cType:length() - 1) == "*" && cType != "const char*" && cType != "SpecArray*" && cType != "SpecMap*") {
						initC: "(" . cType . ")(" . initC . ")";
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
				local String is targetC: self:generateExpression(expr: stmt:assignTarget);
				local String is valC: self:generateExpression(expr: stmt:assignValue);
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
					return "    return " . retC . ";\n";
				}
				return "    return;\n";
			}
			is "WHEN": {
				local String is subjC: self:generateExpression(expr: stmt:whenSubject);
				local String is out: "";
				local Boolean is first: true;
				stmt:whenArms:each(action: local Function(WhenArm is arm){
					if (arm:isElse) {
						out: out . "    } else {\n";
					} else {
						local String is condOr: "";
						arm:conditions:each(action: local Function(Expression is c){
							local String is cVal: self:generateExpression(expr: c);
							local String is cmp: "";
							if (self:isStringExpr(expr: stmt:whenSubject)) {
								cmp: "spec_str_equals(" . subjC . ", " . cVal . ")";
							} else {
								cmp: "((" . subjC . ") == (" . cVal . "))";
							}
							if (condOr == "") {
								condOr: cmp;
							} else {
								condOr: condOr . " || " . cmp;
							}
						});
						if (first) {
							out: out . "    if (" . condOr . ") {\n";
							first: false;
						} else {
							out: out . "    } else if (" . condOr . ") {\n";
						}
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
		local String is retType: self:resolveReturnType(t: method:getType());
		if (retType == "void") {
			if (method:getName() == "evaluate" || method:getName() == "iteration") {
				retType: "bool";
			}
		}

		self:localVars: Map:init();
		method:getParameters():each(action: local Function(Parameter is p){
			self:localVars:set(key: p:getName(), value: self:formatTypeString(t: p:getType()));
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
				if (self:isSubclassOf(subName: subCls:getName(), baseName: classDef:getName())) {
					local MethodMemberLoop is ml: MethodMemberLoop:init(members: subCls:getMembers(), methodName: method:getName());
					While:run(loop: ml);
					if (ml:found) {
						local Member is subM: ml:res;
						if (subM:getBody():length() > 0 && subM:getParameters():length() == paramCount) {
							out: out . "    if (self && self->_type_name && strcmp(self->_type_name, \"" . subCls:getName() . "\") == 0) {\n";
							if (retType == "void") {
								out: out . "        " . subCls:getName() . "_" . method:getName() . "((" . subCls:getName() . "*)self" . callArgs . ");\n        return;\n";
							} else {
								out: out . "        return " . subCls:getName() . "_" . method:getName() . "((" . subCls:getName() . "*)self" . callArgs . ");\n";
							}
							out: out . "    }\n";
						}
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
		flattenedClasses:each(action: local Function(Class is c){
			self:allClassNames:set(key: c:getName(), value: "true");
			if (c:getBaseClass() == "Enum") {
				self:allEnumNames:set(key: c:getName(), value: "true");
				c:getMembers():each(action: local Function(Member is m){
					self:allEnumVariants:set(key: m:getName(), value: c:getName());
					if (m:getType():getName() == "String" || m:getType():getName() == "string") {
						self:allStringBackedEnums:set(key: c:getName(), value: "true");
					}
				});
			}
		});

		self:declGen:setEnumNames(names: self:allEnumNames);
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
					self:fieldTypes:set(key: m:getName(), value: self:formatTypeString(t: m:getType()));
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
