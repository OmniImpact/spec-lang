#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, Linter, and TypeChecker.

## Represents a compile-time static type error detected by [TypeChecker].
class TypeError{

	## Line number coordinate where the error occurred (0 if general).
	local Int is line: 0;

	## Explanatory diagnostic message describing the type mismatch.
	local String is message: "";

	## Initializes a type error descriptor.
	##
	## @param line: One-based source line.
	## @param message: Type mismatch error description.
	replace local Function is init(self:line, self:message){
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
		base:reflect:Type,
		base:reflect:Class,
		base:reflect:Member,
		base:reflect:Parameter,
		base:meta:*
	];

	## Registered classes environment mapping class name -> Class.
	local Map of String to String is registeredClasses: Map:init();

	## Symbol table for local variables in the current scope: name -> Type name.
	local Map of String to String is localVars: Map:init();

	## Field types in the current class: name -> Type name.
	local Map of String to String is fieldTypes: Map:init();

	## Currently analyzed class name.
	local String is currentClassName: "";

	## Currently analyzed method return type name.
	local String is currentMethodReturnType: "";

	## Accumulated list of type errors.
	local Array of TypeError is errors: [];

	replace local Function is init(){
	}

	## Records a type error with line coordinates.
	##
	## @param line: Source line number.
	## @param msg: Diagnostic error message.
	replace local Function is addError(Int is line, String is msg){
		self:errors:add(item: TypeError:init(line: line, message: msg));
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
		if ((target == "Int" || target == "int") && (source == "Int" || source == "int")) {
			return true;
		}
		if ((target == "Float" || target == "float") && (source == "Float" || source == "float")) {
			return true;
		}
		if ((target == "Boolean" || target == "bool") && (source == "Boolean" || source == "bool")) {
			return true;
		}
		if ((target == "String" || target == "string") && (source == "String" || source == "string")) {
			return true;
		}
		return false;
	}

	## Infers and resolves the resulting type of an expression node.
	##
	## @param expr: [Expression] AST node.
	## @return: Resolved type name string.
	replace local Function of String is inferExpressionType(Expression is expr){
		local String is kind: expr:getKind();

		when (kind) {
			is "STRING": {
				return "String";
			}
			is "NUMBER": {
				return "Int";
			}
			is "FLOAT": {
				return "Float";
			}
			is "BOOL": {
				return "Boolean";
			}
			is "IDENT": {
				local String is name: expr:stringValue;
				if (name == "self") {
					return self:currentClassName;
				}
				if (name == "true" || name == "false") {
					return "Boolean";
				}
				if (self:localVars:has(key: name)) {
					return self:localVars:getString(key: name, default: "Any");
				}
				if (self:fieldTypes:has(key: name)) {
					return self:fieldTypes:getString(key: name, default: "Any");
				}
				return "Any";
			}
			is "BINARY": {
				local String is op: expr:binaryOp;
				when (op) {
					is ".": {
						return "String";
					}
					is "==", "!=", "is", "<", "<=", ">", ">=": {
						return "Boolean";
					}
					is "&&", "||": {
						return "Boolean";
					}
					is "+", "-", "*", "/", "%": {
						local String is leftT: self:inferExpressionType(expr: expr:leftExpr);
						local String is rightT: self:inferExpressionType(expr: expr:rightExpr);
						return if (leftT == "Float" || rightT == "Float") "Float" else "Int";
					}
					else: {
						return "Int";
					}
				}
			}
			is "UNARY": {
				if (expr:unaryOp == "!") {
					return "Boolean";
				}
				return self:inferExpressionType(expr: expr:unaryExpr);
			}
			is "ARRAY": {
				return "Array";
			}
			is "CALL": {
				local String is method: expr:methodName;
				when (method) {
					is "length", "ordinal", "indexOf", "count", "countLeading": {
						return "Int";
					}
					is "isEmpty", "has", "any", "startsWith", "isDigit", "isAlpha", "isWhitespace", "exists": {
						return "Boolean";
					}
					is "charAt", "substring", "getString", "toString", "name", "read", "trim", "value": {
						return "String";
					}
					is "round", "floor", "ceil", "random": {
						return "Float";
					}
					is "lines", "filter", "slice", "values", "keys": {
						return "Array";
					}
					else: {
						return "Any";
					}
				}
			}
			else: {
				return "Any";
			}
		}
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
				self:localVars:set(key: varName, value: declaredType);

				if (stmt:hasInit) {
					local String is initType: self:inferExpressionType(expr: stmt:initExpr);
					if (!self:isAssignable(target: declaredType, source: initType)) {
						local String is msg: "Type mismatch in variable declaration for '" . varName . "': cannot assign '" . initType . "' to '" . declaredType . "'.";
						self:addError(line: 0, msg: msg);
					}
				}
			}
			is "ASSIGN": {
				local String is targetType: self:inferExpressionType(expr: stmt:assignTarget);
				local String is valType: self:inferExpressionType(expr: stmt:assignValue);
				if (!self:isAssignable(target: targetType, source: valType)) {
					local String is msg: "Type mismatch in assignment: cannot assign '" . valType . "' to '" . targetType . "'.";
					self:addError(line: 0, msg: msg);
				}
			}
			is "IF": {
				local String is condType: self:inferExpressionType(expr: stmt:ifCondition);
				if (condType != "Boolean" && condType != "bool" && condType != "Any") {
					local String is msg: "Condition in 'if' must be Boolean, found '" . condType . "'.";
					self:addError(line: 0, msg: msg);
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
			is "RETURN": {
				if (stmt:hasReturnExpr) {
					local String is retType: self:inferExpressionType(expr: stmt:returnExpr);
					if (!self:isAssignable(target: self:currentMethodReturnType, source: retType)) {
						local String is msg: "Method declared return type '" . self:currentMethodReturnType . "', but returned '" . retType . "'.";
						self:addError(line: 0, msg: msg);
					}
				} else {
					if (self:currentMethodReturnType != "void" && self:currentMethodReturnType != "" && self:currentMethodReturnType != "Any") {
						local String is msg: "Method expects return value of type '" . self:currentMethodReturnType . "', but found empty return.";
						self:addError(line: 0, msg: msg);
					}
				}
			}
			is "EXPR": {
				self:inferExpressionType(expr: stmt:exprStmt);
			}
			else: {}
		}
	}

	## Resolves the concrete return type of a method signature.
	##
	## @param t: Declared [Type] descriptor.
	## @return: Return type name string.
	replace local Function of String is resolveReturnType(Type is t){
		if (t:getName() == "Function") {
			if (t:getParams():length() > 0) {
				local Type is ret: t:getParams():get(index: 0);
				return ret:getName();
			}
			return "void";
		}
		return t:getName();
	}

	## Validates a method member definition.
	##
	## @param method: Method [Member] descriptor.
	replace local Function is checkMethod(Member is method){
		self:currentMethodReturnType: self:resolveReturnType(t: method:getType());
		self:localVars: Map:init();

		method:getParameters():each(action: local Function(Parameter is p){
			self:localVars:set(key: p:getName(), value: p:getType():getName());
		});

		method:getBody():each(action: local Function(Statement is stmt){
			self:checkStatement(stmt: stmt);
		});
	}

	## Validates all members of a class definition.
	##
	## @param classDef: [Class] definition.
	replace local Function is checkClass(Class is classDef){
		self:currentClassName: classDef:getName();
		self:fieldTypes: Map:init();

		classDef:getMembers():each(action: local Function(Member is m){
			when (m:getMemberKind()) {
				is FIELD: {
					local String is declaredType: m:getType():getName();
					self:fieldTypes:set(key: m:getName(), value: declaredType);
					if (m:hasInit) {
						local String is initType: self:inferExpressionType(expr: m:initExpr);
						if (!self:isAssignable(target: declaredType, source: initType)) {
							local String is msg: "Type mismatch in field '" . m:getName() . "': cannot assign '" . initType . "' to '" . declaredType . "'.";
							self:addError(line: 0, msg: msg);
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
					self:checkClass(classDef: m:getNestedClass());
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
		self:registeredClasses: Map:init();

		program:getClasses():each(action: local Function(Class is c){
			self:registeredClasses:set(key: c:getName(), value: c:getName());
		});

		program:getClasses():each(action: local Function(Class is c){
			self:checkClass(classDef: c);
		});

		return self:errors;
	}

}
