#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, Linter, and TypeChecker.

## Represents a compile-time static type error detected by [TypeChecker].
class TypeError{

	## Line number coordinate where the error occurred (0 if general).
	local Int is line: 0;

	## Explanatory diagnostic message describing the type mismatch.
	local String is message: "";

	## Initializes a type error descriptor.
	replace local Function is init(Int is line, String is message){
		self:line: line;
		self:message: message;
	}

	## Returns the line coordinate.
	replace local Function of Int is getLine(){
		return self:line;
	}

	## Returns the diagnostic message.
	replace local Function of String is getMessage(){
		return self:message;
	}

	## Formats the type error for display.
	replace local Function of String is toString(){
		local String is loc: if (self:line > 0) "Line " . self:line . ": " else "";
		return "  [TypeError] " . loc . self:message;
	}

}

## Semantic analysis and static type checker for Spec programs.
class TypeChecker{

	replace local Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:reflect:Type,
		base:reflect:Class,
		base:reflect:Member,
		base:reflect:Parameter,
		base:meta:*
	];

	## Registered classes environment mapping class name -> "true".
	local Map of String to String is registeredClasses: Map:init();

	## Registry of all enum type names defined in the program.
	local Map of String to String is allEnumNames: Map:init();

	## Registry of all enum variant names to their parent enum name.
	local Map of String to String is allEnumVariants: Map:init();

	## Registry of all string-backed enum names.
	local Map of String to String is allStringBackedEnums: Map:init();

	## Symbol table for local variables in the current scope: name -> Type name.
	local Map of String to String is localVars: Map:init();

	## Field types in the current class: name -> Type name.
	local Map of String to String is fieldTypes: Map:init();

	## Currently analyzed class name.
	local String is currentClassName: "";

	## Source file path of the currently analyzed class.
	local String is currentSourceFile: "";

	## Currently analyzed method return type name.
	local String is currentMethodReturnType: "";

	## Accumulated list of type errors.
	local Array of TypeError is errors: [];

	## All class definitions in program (including nested classes) for hierarchy resolution.
	local Array of Class is programClasses: [];

	replace local Function is init(){
		self:programClasses: [];
		self:registeredClasses: Map:init();
		self:allEnumNames: Map:init();
		self:allEnumVariants: Map:init();
		self:allStringBackedEnums: Map:init();
		self:localVars: Map:init();
		self:fieldTypes: Map:init();
		self:currentSourceFile: "";
	}

	## Records a type error with line coordinates.
	##
	## @param line: Source line number.
	## @param msg: Diagnostic error message.
	replace local Function is addError(Int is line, String is msg){
		local String is fullMsg: if (self:currentSourceFile != "") "[" . self:currentSourceFile . "] " . msg else msg;
		self:errors:add(item: TypeError:init(line: line, message: fullMsg));
	}

	## Formats a [Type] descriptor for a variable or field (preserving "Function:RetType").
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

	replace local Function of Member is lookupEnumVariant(String is enumName, String is variantName){
		local Class is cls: self:findClass(name: enumName);
		local FieldSearchLoop is fl: FieldSearchLoop:init(members: cls:getMembers(), fieldName: variantName);
		While:run(loop: fl);
		if (fl:found) {
			return fl:res;
		}
		return Member:init(kind: "UNKNOWN");
	}

	replace local Function is bindWhenPatternVars(WhenArm is arm){
		arm:conditions:each(action: local Function(Expression is c){
			if (c:getKind() == "CALL" && self:allEnumVariants:has(key: c:methodName)) {
				local String is enumName: self:allEnumVariants:getString(key: c:methodName, default: "");
				local Member is vMem: self:lookupEnumVariant(enumName: enumName, variantName: c:methodName);
				local Int is idx: 0;
				c:methodArgs:each(action: local Function(NamedArg is arg){
					if (idx < vMem:getParameters():length()) {
						local Expression is av: arg:getValue();
						if (av:getKind() == "IDENT") {
							local Parameter is pDef: vMem:getParameters():get(index: idx);
							self:localVars:set(key: av:stringValue, value: self:formatVarTypeString(t: pDef:getType()));
						}
					}
					idx: idx + 1;
				});
				c:setResolvedType(t: enumName);
			} else {
				self:inferExpressionType(expr: c);
			}
		});
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

	class SearchLoop extends Loop{
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

	## Finds a class definition by name across the program.
	##
	## @param name: Target class name.
	## @return: Matching [Class] descriptor.
	replace local Function of Class is findClass(String is name){
		local SearchLoop is s: SearchLoop:init(list: self:programClasses, target: name);
		While:run(loop: s);
		if (s:found) {
			return s:res;
		}
		return Class:init(name: "", baseClass: "", members: []);
	}

	## Checks if `subName` inherits from or implements `baseName`.
	replace local Function of Boolean is isSubclassOf(String is subName, String is baseName){
		if (subName == "" || baseName == "") {
			return false;
		}
		if (subName == baseName) {
			return true;
		}
		local Class is subCls: self:findClass(name: subName);
		if (subCls:getName() == "") {
			return false;
		}
		local Boolean is matched: false;
		subCls:getBaseClasses():each(action: local Function(String is pName){
			if (pName == baseName || self:isSubclassOf(subName: pName, baseName: baseName)) {
				matched: true;
			}
		});
		return matched;
	}

	## Determines whether a source type is assignable to a target type.
	##
	## @param target: Target type name.
	## @param source: Source type name.
	## @return: `true` if compatible, `false` otherwise.
	replace local Function of Boolean is isAssignable(String is target, String is source){
		if (target == source || target == "Any" || source == "Any" || target == "" || source == "") {
			return true;
		}
		if ((target == "Float" || target == "float") && (source == "Float" || source == "float" || source == "Int" || source == "int")) {
			return true;
		}
		if ((target == "Int" || target == "int") && (source == "Int" || source == "int" || source == "Float" || source == "float")) {
			return true;
		}
		if ((target == "Boolean" || target == "bool") && (source == "Boolean" || source == "bool")) {
			return true;
		}
		if ((target == "String" || target == "string") && (source == "String" || source == "string")) {
			return true;
		}
		if (target:startsWith(prefix: "Array") && source:startsWith(prefix: "Array")) {
			return true;
		}
		if (target:startsWith(prefix: "Map") && source:startsWith(prefix: "Map")) {
			return true;
		}
		if (target:startsWith(prefix: "Function") && source:startsWith(prefix: "Function")) {
			return true;
		}
		local Array of String is tParts: target:split(delimiter: ":");
		local Array of String is sParts: source:split(delimiter: ":");
		if (tParts:length() > 0 && sParts:length() > 0) {
			local String is tBase: tParts:get(index: 0);
			local String is sBase: sParts:get(index: 0);
			if (tBase == sBase) {
				return true;
			}
			if (self:isSubclassOf(subName: sBase, baseName: tBase)) {
				return true;
			}
		}
		local Class is curCls: self:findClass(name: self:currentClassName);
		if (curCls:getTypeParams():indexOf(search: target, default: -1) >= 0 || curCls:getTypeParams():indexOf(search: source, default: -1) >= 0) {
			return true;
		}
		if (self:isSubclassOf(subName: source, baseName: target)) {
			return true;
		}
		return false;
	}

	class FieldSearchLoop extends Loop{
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

	## Looks up a field's static type string on a class and its ancestors.
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
		local FieldSearchLoop is fl: FieldSearchLoop:init(members: cls:getMembers(), fieldName: fieldName);
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

	class MethodSearchLoop extends Loop{
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

	## Looks up a method's return type string on a class and its ancestors.
	replace local Function of String is lookupMethodReturnType(String is className, String is methodName){
		if (className == "" || className == "Any") {
			return "";
		}
		local Array of String is parts: className:split(delimiter: ":");
		local String is baseClassName: parts:get(index: 0);
		local Array of String is typeArgs: parts:slice(start: 1, end: parts:length());
		if (methodName == "init" && self:registeredClasses:has(key: baseClassName) && !self:allEnumNames:has(key: baseClassName)) {
			return className;
		}
		local Class is cls: self:findClass(name: baseClassName);
		if (cls:getName() == "") {
			return "";
		}
		local MethodSearchLoop is ml: MethodSearchLoop:init(members: cls:getMembers(), methodName: methodName);
		While:run(loop: ml);
		if (ml:found) {
			local Member is foundM: ml:res;
			local String is rawT: self:formatTypeString(t: foundM:getType());
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

	class PathResolveLoop extends Loop{
		local TypeChecker is tc;
		local Array of String is segs;
		local Int is idx: 1;
		local String is currType: "";

		replace local Function is init(TypeChecker is tc, Array of String is segs, String is rootType){
			self:tc: tc;
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
			if (self:tc:allEnumNames:has(key: self:currType)) {
				return true;
			}
			self:currType: self:tc:lookupFieldType(className: self:currType, fieldName: seg);
			return true;
		}
	}

	## Infers and resolves the resulting type of an expression node, annotating `expr:resolvedType`.
	##
	## @param expr: [Expression] AST node.
	## @return: Resolved type name string.
	replace local Function of String is inferExpressionType(Expression is expr){
		local String is kind: expr:getKind();
		local String is res: "Any";

		when (kind) {
			is "STRING": {
				res: "String";
			}
			is "NUMBER": {
				res: "Int";
			}
			is "FLOAT": {
				res: "Float";
			}
			is "BOOL": {
				res: "Boolean";
			}
			is "IDENT": {
				local String is name: expr:stringValue;
				if (name == "self") {
					res: self:currentClassName;
				} else if (name == "true" || name == "false") {
					res: "Boolean";
				} else if (self:localVars:has(key: name)) {
					res: self:localVars:getString(key: name, default: "Any");
				} else if (self:fieldTypes:has(key: name)) {
					res: self:fieldTypes:getString(key: name, default: "Any");
				} else if (self:allEnumVariants:has(key: name)) {
					res: self:allEnumVariants:getString(key: name, default: "Any");
				} else if (self:registeredClasses:has(key: name)) {
					res: name;
				} else if (name == "File" || name == "Process" || name == "Math" || name == "math" || name == "Map" || name == "Array" || name == "While" || name == "Input" || name == "LoopControl" || name == "output") {
					res: name;
				}
			}
			is "PATH": {
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
					} else if (self:allEnumNames:has(key: root)) {
						rootType: root;
					} else if (self:registeredClasses:has(key: root)) {
						rootType: root;
					}
					local PathResolveLoop is pLoop: PathResolveLoop:init(tc: self, segs: segs, rootType: rootType);
					While:run(loop: pLoop);
					if (pLoop:currType != "") {
						res: pLoop:currType;
					}
				}
			}
			is "BINARY": {
				local String is leftT: self:inferExpressionType(expr: expr:leftExpr);
				local String is rightT: self:inferExpressionType(expr: expr:rightExpr);
				local String is op: expr:binaryOp;
				when (op) {
					is ".": {
						res: "String";
					}
					is "==", "!=", "is", "<", "<=", ">", ">=": {
						res: "Boolean";
					}
					is "&&", "||": {
						res: "Boolean";
					}
					is "+", "-", "*", "/", "%": {
						res: if (leftT == "Float" || rightT == "Float") "Float" else "Int";
					}
					else: {
						res: "Int";
					}
				}
			}
			is "UNARY": {
				local String is innerT: self:inferExpressionType(expr: expr:unaryExpr);
				if (expr:unaryOp == "!") {
					res: "Boolean";
				} else {
					res: innerT;
				}
			}
			is "ARRAY": {
				local String is firstElemType: "";
				expr:arrayItems:each(action: local Function(Expression is item){
					local String is itemT: self:inferExpressionType(expr: item);
					if (firstElemType == "" && itemT != "" && itemT != "Any") {
						firstElemType: itemT;
					}
				});
				if (firstElemType != "") {
					res: "Array:" . firstElemType;
				} else {
					res: "Array";
				}
			}
			is "MAP": {
				local String is firstKeyType: "";
				local String is firstValType: "";
				expr:mapKeys:each(action: local Function(Expression is k){
					local String is kt: self:inferExpressionType(expr: k);
					if (firstKeyType == "" && kt != "" && kt != "Any") {
						firstKeyType: kt;
					}
				});
				expr:mapValues:each(action: local Function(Expression is v){
					local String is vt: self:inferExpressionType(expr: v);
					if (firstValType == "" && vt != "" && vt != "Any") {
						firstValType: vt;
					}
				});
				if (firstKeyType != "" && firstValType != "") {
					res: "Map:" . firstKeyType . ":" . firstValType;
				} else {
					res: "Map";
				}
			}
			is "INDEX": {
				local String is leftT: self:inferExpressionType(expr: expr:leftExpr);
				self:inferExpressionType(expr: expr:rightExpr);
				if (leftT:startsWith(prefix: "Array:") && leftT:length() > 6) {
					res: leftT:substring(start: 6, end: leftT:length());
				} else if (leftT:startsWith(prefix: "Map:") && leftT:length() > 4) {
					local String is afterMap: leftT:substring(start: 4, end: leftT:length());
					local Int is colonIdx: afterMap:indexOf(needle: ":", default: -1);
					if (colonIdx >= 0 && colonIdx + 1 < afterMap:length()) {
						res: afterMap:substring(start: colonIdx + 1, end: afterMap:length());
					} else {
						res: "String";
					}
				} else if (leftT == "Map") {
					res: "String";
				} else {
					res: "Any";
				}
			}
			is "IF_ELSE": {
				self:inferExpressionType(expr: expr:condExpr);
				local String is thenT: self:inferExpressionType(expr: expr:thenExpr);
				local String is elseT: self:inferExpressionType(expr: expr:elseExpr);
				res: if (thenT != "" && thenT != "Any") thenT else elseT;
			}
			is "WHEN": {
				self:inferExpressionType(expr: expr:whenSubject);
				local String is armType: "Any";
				expr:whenArms:each(action: local Function(WhenArm is arm){
					self:bindWhenPatternVars(arm: arm);
					if (arm:hasValueExpr) {
						local String is vt: self:inferExpressionType(expr: arm:valueExpr);
						if (armType == "Any" && vt != "" && vt != "Any") {
							armType: vt;
						}
					}
					arm:body:each(action: local Function(Statement is s){
						self:checkStatement(stmt: s);
					});
				});
				res: armType;
			}
			is "ANON_FN": {
				local Map of String to String is savedVars: Map:init();
				local Array of String is existingKeys: self:localVars:keys();
				existingKeys:each(action: local Function(String is k){
					savedVars:set(key: k, value: self:localVars:getString(key: k, default: ""));
				});
				local String is savedRet: self:currentMethodReturnType;

				self:currentMethodReturnType: self:resolveReturnType(t: expr:anonReturnType);
				expr:anonParams:each(action: local Function(Parameter is p){
					self:localVars:set(key: p:getName(), value: self:formatVarTypeString(t: p:getType()));
				});
				expr:anonBody:each(action: local Function(Statement is s){
					self:checkStatement(stmt: s);
				});

				self:localVars: savedVars;
				self:currentMethodReturnType: savedRet;
				local String is anonRetName: expr:anonReturnType:getName();
				if (anonRetName != "" && anonRetName != "void" && anonRetName != "Void") {
					res: "Function:" . self:formatTypeString(t: expr:anonReturnType);
				} else {
					res: "Function";
				}
			}
			is "CALL": {
				local String is targetType: self:inferExpressionType(expr: expr:methodTarget);
				local String is method: expr:methodName;
				if (targetType:startsWith(prefix: "Array:") && targetType:length() > 6) {
					local String is elemTypeName: targetType:substring(start: 6, end: targetType:length());
					if (method == "fold" && expr:methodArgs:length() >= 2) {
						local NamedArg is a0: expr:methodArgs:get(index: 0);
						local String is initType: self:inferExpressionType(expr: a0:getValue());
						local NamedArg is a1: expr:methodArgs:get(index: 1);
						local Expression is av: a1:getValue();
						if (av:getKind() == "ANON_FN") {
							if (av:anonParams:length() >= 1) {
								local Parameter is p0: av:anonParams:get(index: 0);
								if (p0:getType():getName() == "Any" || p0:getType():getName() == "") {
									p0:setType(t: Type:init(name: initType));
								}
							}
							if (av:anonParams:length() >= 2) {
								local Parameter is p1: av:anonParams:get(index: 1);
								if (p1:getType():getName() == "Any" || p1:getType():getName() == "") {
									p1:setType(t: Type:init(name: elemTypeName));
								}
							}
						}
					} else {
						expr:methodArgs:each(action: local Function(NamedArg is arg){
							local Expression is av: arg:getValue();
							if (av:getKind() == "ANON_FN") {
								av:anonParams:each(action: local Function(Parameter is p){
									if (p:getType():getName() == "Any" || p:getType():getName() == "") {
										p:setType(t: Type:init(name: elemTypeName));
									}
								});
							}
						});
					}
				} else if (targetType:startsWith(prefix: "Map:") && method == "each") {
					local String is afterMap: targetType:substring(start: 4, end: targetType:length());
					local Int is colonIdx: afterMap:indexOf(needle: ":", default: -1);
					local String is valTypeName: "String";
					if (colonIdx >= 0 && colonIdx + 1 < afterMap:length()) {
						valTypeName: afterMap:substring(start: colonIdx + 1, end: afterMap:length());
					}
					expr:methodArgs:each(action: local Function(NamedArg is arg){
						local Expression is av: arg:getValue();
						if (av:getKind() == "ANON_FN") {
							if (av:anonParams:length() >= 1) {
								local Parameter is p0: av:anonParams:get(index: 0);
								if (p0:getType():getName() == "Any" || p0:getType():getName() == "") {
									p0:setType(t: Type:init(name: "String"));
								}
							}
							if (av:anonParams:length() >= 2) {
								local Parameter is p1: av:anonParams:get(index: 1);
								if (p1:getType():getName() == "Any" || p1:getType():getName() == "") {
									p1:setType(t: Type:init(name: valTypeName));
								}
							}
						}
					});
				}
				expr:methodArgs:each(action: local Function(NamedArg is arg){
					self:inferExpressionType(expr: arg:getValue());
				});

				if (targetType == "self" || targetType == "") {
					targetType: self:currentClassName;
				}

				local String is fnVarT: "";
				if (expr:methodTarget:getKind() == "IDENT" && expr:methodTarget:stringValue == "self") {
					fnVarT: self:localVars:getString(key: method, default: self:fieldTypes:getString(key: method, default: ""));
				}
				if (fnVarT:startsWith(prefix: "Function")) {
					if (fnVarT:startsWith(prefix: "Function:") && fnVarT:length() > 9) {
						res: fnVarT:substring(start: 9, end: fnVarT:length());
					} else {
						res: "Any";
					}
				} else if (self:allEnumVariants:has(key: method) && (self:allEnumNames:has(key: targetType) || targetType == self:currentClassName)) {
					res: self:allEnumVariants:getString(key: method, default: "Any");
				} else if (method == "init" && self:registeredClasses:has(key: targetType) && !self:allEnumNames:has(key: targetType)) {
					res: targetType;
				} else if (targetType:startsWith(prefix: "Array") && (method == "get" || method == "pop" || method == "removeAt")) {
					if (targetType:startsWith(prefix: "Array:") && targetType:length() > 6) {
						res: targetType:substring(start: 6, end: targetType:length());
					} else {
						res: "Any";
					}
				} else if (targetType:startsWith(prefix: "Array") && (method == "filter" || method == "slice")) {
					res: targetType;
				} else if (targetType:startsWith(prefix: "Array") && method == "map") {
					local String is mappedElem: "Any";
					if (expr:methodArgs:length() > 0) {
						local NamedArg is a0: expr:methodArgs:get(index: 0);
						local Expression is fnExpr: a0:getValue();
						if (fnExpr:getKind() == "ANON_FN") {
							local String is fnRet: fnExpr:anonReturnType:getName();
							if (fnRet != "" && fnRet != "Void" && fnRet != "void" && fnRet != "Any") {
								mappedElem: self:formatTypeString(t: fnExpr:anonReturnType);
							}
						}
					}
					res: if (mappedElem != "Any") "Array:" . mappedElem else "Array";
				} else if (targetType:startsWith(prefix: "Array") && method == "fold") {
					if (expr:methodArgs:length() > 0) {
						local NamedArg is a0: expr:methodArgs:get(index: 0);
						res: a0:getValue():getResolvedType();
					} else {
						res: "Any";
					}
				} else if (targetType:startsWith(prefix: "Map:") && method == "get") {
					local String is afterMap: targetType:substring(start: 4, end: targetType:length());
					local Int is colonIdx: afterMap:indexOf(needle: ":", default: -1);
					if (colonIdx >= 0 && colonIdx + 1 < afterMap:length()) {
						res: afterMap:substring(start: colonIdx + 1, end: afterMap:length());
					} else {
						res: "Any";
					}
				} else if (self:allEnumNames:has(key: targetType)) {
					when (method) {
						is "name": { res: "String"; }
						is "ordinal": { res: "Int"; }
						is "values": { res: "Array:" . targetType; }
						is "value": {
							res: if (self:allStringBackedEnums:has(key: targetType)) "String" else "Int";
						}
						else: { res: "Any"; }
					}
				} else {
					local String is classRet: self:lookupMethodReturnType(className: targetType, methodName: method);
					if (classRet != "" && classRet != "void" && classRet != "Void" && classRet != "Any") {
						res: classRet;
					} else {
						when (method) {
							is "length", "ordinal", "indexOf", "count", "countLeading", "execute", "getInt", "getPid": {
								res: "Int";
							}
							is "isEmpty", "has", "any", "startsWith", "endsWith", "contains", "isDigit", "isAlpha", "isWhitespace", "exists", "write", "getBool", "remove": {
								res: "Boolean";
							}
							is "charAt", "substring", "getString", "toString", "name", "read", "trim", "replaceAll", "join": {
								res: "String";
							}
							is "value": {
								res: "Int";
							}
							is "round", "floor", "ceil", "ceiling", "random", "getFloat": {
								res: "Float";
							}
							is "lines", "keys", "split": {
								res: "Array:String";
							}
							is "filter", "slice", "values": {
								res: "Array";
							}
							else: {
								res: "Any";
							}
						}
					}
				}
			}
			else: {
				res: "Any";
			}
		}

		expr:setResolvedType(t: res);
		return res;
	}

	## Validates type safety of a statement node.
	##
	## @param stmt: [Statement] AST node.
	replace local Function is checkStatement(Statement is stmt){
		local String is kind: stmt:getKind();

		when (kind) {
			is "VAR_DECL": {
				local String is varName: stmt:varName;
				local String is declaredType: stmt:varType:getName();
				local String is fullType: self:formatVarTypeString(t: stmt:varType);
				self:localVars:set(key: varName, value: fullType);

				if (stmt:hasInit) {
					local String is initType: self:inferExpressionType(expr: stmt:initExpr);
					if (!self:isAssignable(target: declaredType, source: initType)) {
						local String is msg: "Type mismatch in variable declaration for '" . varName . "': cannot assign '" . initType . "' to '" . declaredType . "'.";
						self:addError(line: stmt:getLine(), msg: msg);
					}
				}
			}
			is "ASSIGN": {
				local String is targetType: self:inferExpressionType(expr: stmt:assignTarget);
				local String is valType: self:inferExpressionType(expr: stmt:assignValue);
				if (!self:isAssignable(target: targetType, source: valType)) {
					local String is msg: "Type mismatch in assignment: cannot assign '" . valType . "' to '" . targetType . "'.";
					self:addError(line: stmt:getLine(), msg: msg);
				}
			}
			is "IF": {
				local String is condType: self:inferExpressionType(expr: stmt:ifCondition);
				if (condType != "Boolean" && condType != "bool" && condType != "Any") {
					local String is msg: "Condition in 'if' must be Boolean, found '" . condType . "'.";
					self:addError(line: stmt:getLine(), msg: msg);
				}
				stmt:thenBranch:each(action: local Function(Statement is s){
					self:checkStatement(stmt: s);
				});
				if (stmt:hasElse) {
					stmt:elseBranch:each(action: local Function(Statement is s){
						self:checkStatement(stmt: s);
					});
				}
			}
			is "WHEN": {
				self:inferExpressionType(expr: stmt:whenSubject);
				stmt:whenArms:each(action: local Function(WhenArm is arm){
					self:bindWhenPatternVars(arm: arm);
					if (arm:hasValueExpr) {
						self:inferExpressionType(expr: arm:valueExpr);
					}
					arm:body:each(action: local Function(Statement is s){
						self:checkStatement(stmt: s);
					});
				});
			}
			is "RETURN": {
				if (stmt:hasReturnExpr) {
					local String is retType: self:inferExpressionType(expr: stmt:returnExpr);
					if (!self:isAssignable(target: self:currentMethodReturnType, source: retType)) {
						local String is msg: "Method declared return type '" . self:currentMethodReturnType . "', but returned '" . retType . "'.";
						self:addError(line: stmt:getLine(), msg: msg);
					}
				} else {
					if (self:currentMethodReturnType != "void" && self:currentMethodReturnType != "Void" && self:currentMethodReturnType != "" && self:currentMethodReturnType != "Any") {
						local String is msg: "Method expects return value of type '" . self:currentMethodReturnType . "', but found empty return.";
						self:addError(line: stmt:getLine(), msg: msg);
					}
				}
			}
			is "EXPR": {
				self:inferExpressionType(expr: stmt:exprStmt);
			}
			is "CLASS": {
				local String is savedClass: self:currentClassName;
				local String is savedRet: self:currentMethodReturnType;
				local Map of String to String is savedVars: Map:init();
				local Array of String is vKeys: self:localVars:keys();
				vKeys:each(action: local Function(String is k){
					savedVars:set(key: k, value: self:localVars:getString(key: k, default: ""));
				});
				local Map of String to String is savedFields: Map:init();
				local Array of String is fKeys: self:fieldTypes:keys();
				fKeys:each(action: local Function(String is k){
					savedFields:set(key: k, value: self:fieldTypes:getString(key: k, default: ""));
				});

				self:checkClass(classDef: stmt:nestedClass);

				self:currentClassName: savedClass;
				self:currentMethodReturnType: savedRet;
				self:localVars: savedVars;
				self:fieldTypes: savedFields;
			}
			else: {}
		}
	}

	## Resolves the concrete return type of a method signature.
	##
	## @param t: Declared [Type] descriptor.
	## @return: Return type name string.
	replace local Function of String is resolveReturnType(Type is t){
		return self:formatTypeString(t: t);
	}

	## Validates a method member definition.
	##
	## @param method: Method [Member] descriptor.
	replace local Function is checkMethod(Member is method){
		method:getParameters():each(action: local Function(Parameter is p){
			if (p:getType():getName() == "SELF_FIELD") {
				local String is ft: self:fieldTypes:getString(key: p:getName(), default: "Any");
				p:setType(t: Type:init(name: ft));
			}
		});
		self:currentMethodReturnType: self:resolveReturnType(t: method:getType());
		if (self:currentMethodReturnType == "" || self:currentMethodReturnType == "void") {
			if (method:getName() == "evaluate" || method:getName() == "iteration") {
				self:currentMethodReturnType: "Boolean";
				method:memberType: Type:init(name: "Boolean");
			}
		}
		self:localVars: Map:init();

		method:getParameters():each(action: local Function(Parameter is p){
			self:localVars:set(key: p:getName(), value: self:formatVarTypeString(t: p:getType()));
		});

		method:getBody():each(action: local Function(Statement is stmt){
			self:checkStatement(stmt: stmt);
		});
	}

	class MemberImplementLoop extends Loop{
		local Array of Member is members;
		local Member is target;
		local Int is idx: 0;
		local Boolean is implemented: false;

		replace local Function is init(Array of Member is members, Member is target){
			self:members: members;
			self:target: target;
			self:idx: 0;
			self:implemented: false;
		}

		replace local Function of Boolean is evaluate(){
			return !self:implemented && self:idx < self:members:length();
		}

		replace local Function of Boolean is iteration(LoopControl is c){
			local Member is subM: self:members:get(index: self:idx);
			self:idx: self:idx + 1;
			if (subM:getName() == self:target:getName()) {
				if (subM:getKind() == "METHOD" && subM:getBody():length() > 0) {
					self:implemented: true;
					return false;
				}
				if (subM:getKind() == "FIELD" && subM:getHasInit()) {
					self:implemented: true;
					return false;
				}
			}
			return true;
		}
	}

	## Validates inheritance, interface contracts, and override signatures.
	##
	## @param classDef: [Class] definition to inspect.
	replace local Function is checkInheritance(Class is classDef){
		self:currentSourceFile: classDef:getSourceFile();
		local Boolean is hasInit: false;
		classDef:getMembers():each(action: local Function(Member is m){
			if (m:getName() == "init") {
				hasInit: true;
			}
		});

		# Built-in lifecycle methods strictly require replace
		classDef:getMembers():each(action: local Function(Member is m){
			when (m:getName()) {
				is "init", "evaluate", "iteration", "using", "toString": {
					local Array of String is mods: m:getModifiers();
					if (mods:indexOf(search: "replace", default: -1) < 0) {
						local String is msg: "Built-in lifecycle method '" . m:getName() . "' in class '" . classDef:getName() . "' requires 'replace' modifier.";
						self:addError(line: m:getLine(), msg: msg);
					}
				}
				else: {}
			}
		});

		classDef:getBaseClasses():each(action: local Function(String is baseName){
			local Class is parent: self:findClass(name: baseName);
			if (parent:getName() == baseName) {
				# 1. Enforce abstract member implementation on concrete classes with init
				if (hasInit) {
					parent:getMembers():each(action: local Function(Member is parentM){
						local Boolean is isAbstract: (parentM:getKind() == "FIELD" && !parentM:getHasInit()) ||
							(parentM:getKind() == "METHOD" && parentM:getBody():length() == 0);
						if (isAbstract) {
							local MemberImplementLoop is chk: MemberImplementLoop:init(members: classDef:getMembers(), target: parentM);
							While:run(loop: chk);
							if (!chk:implemented) {
								local String is msg: "Class '" . classDef:getName() . "' does not implement abstract member '" . parentM:getName() . "' required by parent '" . baseName . "'.";
								self:addError(line: classDef:getLine(), msg: msg);
							}
						}
					});
				}

				# 2. Strict replace check & Method signature matching on overrides
				classDef:getMembers():each(action: local Function(Member is subM){
					parent:getMembers():each(action: local Function(Member is parentM){
						if (subM:getName() == parentM:getName()) {
							local Array of String is subMods: subM:getModifiers();
							if (subMods:indexOf(search: "replace", default: -1) < 0) {
								local String is msg: "Member '" . subM:getName() . "' in class '" . classDef:getName() . "' overrides ancestor member from '" . baseName . "', but is missing 'replace' modifier.";
								self:addError(line: subM:getLine(), msg: msg);
							}

							if (subM:getKind() == "METHOD" && parentM:getKind() == "METHOD") {
								if (subM:getParameters():length() != parentM:getParameters():length()) {
									local String is msg: "Method '" . subM:getName() . "' in class '" . classDef:getName() . "' parameter count mismatch with ancestor in '" . baseName . "'.";
									self:addError(line: subM:getLine(), msg: msg);
								} else {
									local Int is pIdx: 0;
									subM:getParameters():each(action: local Function(Parameter is subP){
										local Parameter is parentP: parentM:getParameters():get(index: pIdx);
										if (subP:getType():getName() == "Any" || subP:getType():getName() == "") {
											subP:setType(t: parentP:getType());
										}
										pIdx: pIdx + 1;
									});
								}
								local String is subRet: self:resolveReturnType(t: subM:getType());
								local String is parentRet: self:resolveReturnType(t: parentM:getType());
								if (subM:getType():getName() == "" || subM:getType():getName() == "void") {
									subM:memberType: parentM:getType();
								} else if (!self:isAssignable(target: subRet, source: parentRet)) {
									local String is msg: "Method '" . subM:getName() . "' in class '" . classDef:getName() . "' return type '" . subRet . "' does not match ancestor return type '" . parentRet . "'.";
									self:addError(line: subM:getLine(), msg: msg);
								}
							}
						}
					});
				});
			}
		});
	}

	## Populates `self:fieldTypes` for a class including inherited fields.
	replace local Function is collectClassFieldTypes(Class is classDef){
		classDef:getBaseClasses():each(action: local Function(String is baseName){
			local Class is parent: self:findClass(name: baseName);
			if (parent:getName() != "") {
				self:collectClassFieldTypes(classDef: parent);
			}
		});
		classDef:getMembers():each(action: local Function(Member is m){
			if (m:getKind() == "FIELD") {
				self:fieldTypes:set(key: m:getName(), value: self:formatVarTypeString(t: m:getType()));
			}
		});
	}

	## Validates all members of a class definition.
	##
	## @param classDef: [Class] definition.
	replace local Function is checkClass(Class is classDef){
		self:currentClassName: classDef:getName();
		self:currentSourceFile: classDef:getSourceFile();
		self:fieldTypes: Map:init();
		self:collectClassFieldTypes(classDef: classDef);

		classDef:getMembers():each(action: local Function(Member is m){
			when (m:getMemberKind()) {
				is FIELD: {
					local String is declaredType: m:getType():getName();
					if (m:hasInit) {
						local String is initType: self:inferExpressionType(expr: m:initExpr);
						if (!self:isAssignable(target: declaredType, source: initType)) {
							local String is msg: "Type mismatch in field '" . classDef:getName() . ":" . m:getName() . "': cannot assign '" . initType . "' to '" . declaredType . "'.";
							self:addError(line: m:getLine(), msg: msg);
						}
					}
				}
				else: {}
			}
		});

		classDef:getMembers():each(action: local Function(Member is m){
			when (m:getMemberKind()) {
				is METHOD: {
					self:checkMethod(method: m);
				}
				is CLASS: {
					local String is savedClass: self:currentClassName;
					local Map of String to String is savedFields: Map:init();
					local Array of String is fKeys: self:fieldTypes:keys();
					fKeys:each(action: local Function(String is k){
						savedFields:set(key: k, value: self:fieldTypes:getString(key: k, default: ""));
					});

					self:checkClass(classDef: m:getNestedClass());

					self:currentClassName: savedClass;
					self:fieldTypes: savedFields;
				}
				else: {}
			}
		});
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

	## Performs semantic type checking across all classes in the parsed program.
	##
	## @param program: Parsed [ProgramNode] AST.
	## @return: [Array] of [TypeError] diagnostics.
	replace local Function of Array of TypeError is checkProgram(ProgramNode is program){
		self:errors: [];
		local Array of Class is flattened: [];
		program:getClasses():each(action: local Function(Class is c){
			self:collectClasses(c: c, acc: flattened);
		});
		self:programClasses: flattened;

		self:registeredClasses: Map:init();
		self:allEnumNames: Map:init();
		self:allEnumVariants: Map:init();
		self:allStringBackedEnums: Map:init();

		flattened:each(action: local Function(Class is c){
			self:registeredClasses:set(key: c:getName(), value: c:getName());
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

		# Pass 1: Inheritance contract validation & return/parameter type propagation
		flattened:each(action: local Function(Class is c){
			self:checkInheritance(classDef: c);
		});

		# Pass 2: Full expression type inference & AST annotation
		program:getClasses():each(action: local Function(Class is c){
			self:checkClass(classDef: c);
		});

		return self:errors;
	}

}
