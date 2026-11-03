#! Package base:meta
#! Concrete Abstract Syntax Tree models for code generation, desugaring, and tooling.

## Represents a named argument pair in method calls (e.g. `index: 0`).
class NamedArg{

	replace local Array of String is using: [
		base:meta:AST
	];

	local String is name: "";
	local Expression is value;

	## Initializes a named argument pair.
	##
	## @param name: Argument key identifier (empty string if positional).
	## @param value: Argument [Expression] node.
	replace local Function is init(String is name, Expression is value){
		self:name: name;
		self:value: value;
	}

	## Returns the argument name.
	##
	## @return: Argument key string.
	replace local Function of String is getName(){
		return self:name;
	}

	## Returns the argument value expression.
	##
	## @return: [Expression] instance.
	replace local Function of Expression is getValue(){
		return self:value;
	}

}

## Represents an expression node in the Spec syntax tree.
class Expression{

	replace local Array of String is using: [
		base:struct:Array,
		base:reflect:Type,
		base:reflect:Parameter,
		base:meta:AST
	];

	local String is kind: "";
	local Type is inferredType;
	local String is resolvedType: "";
	local Int is line: 0;
	local String is stringValue: "";
	local Int is intValue: 0;
	local Float is floatValue: 0.0;
	local Boolean is boolValue: false;
	local Array of String is pathSegments;
	local Array of Expression is arrayItems;
	local Array of Expression is mapKeys;
	local Array of Expression is mapValues;
	local Expression is methodTarget;
	local String is methodName: "";
	local Array of NamedArg is methodArgs;
	local String is binaryOp: "";
	local Expression is leftExpr;
	local Expression is rightExpr;
	local String is unaryOp: "";
	local Expression is unaryExpr;
	local Expression is condExpr;
	local Expression is thenExpr;
	local Expression is elseExpr;
	local Expression is whenSubject;
	local Array of WhenArm is whenArms;
	local Type is anonReturnType;
	local Array of Parameter is anonParams;
	local Array of Statement is anonBody;

	## Initializes an expression node with the given kind tag.
	##
	## @param kind: Expression kind identifier (e.g. `"STRING"`, `"CALL"`, `"BINARY"`).
	replace local Function is init(String is kind){
		self:kind: kind;
	}

	## Configures this node as a string literal expression.
	##
	## @param val: String literal value.
	replace local Function is makeString(String is val){
		self:kind: "STRING";
		self:stringValue: val;
	}

	## Configures this node as an integer literal expression.
	##
	## @param val: Integer literal value.
	replace local Function is makeNumber(Int is val){
		self:kind: "NUMBER";
		self:intValue: val;
	}

	## Configures this node as a floating-point literal expression.
	##
	## @param val: Float literal value.
	replace local Function is makeFloat(Float is val){
		self:kind: "FLOAT";
		self:floatValue: val;
	}

	## Configures this node as a boolean literal expression.
	##
	## @param val: Boolean literal value.
	replace local Function is makeBool(Boolean is val){
		self:kind: "BOOL";
		self:boolValue: val;
	}

	## Configures this node as an identifier reference expression.
	##
	## @param name: Identifier name.
	replace local Function is makeIdent(String is name){
		self:kind: "IDENT";
		self:stringValue: name;
	}

	## Configures this node as a colon-delimited path expression.
	##
	## @param segments: Array of path segment identifiers.
	replace local Function is makePath(Array of String is segments){
		self:kind: "PATH";
		self:pathSegments: segments;
	}

	## Configures this node as an array literal expression.
	##
	## @param items: Array of element [Expression] nodes.
	replace local Function is makeArray(Array of Expression is items){
		self:kind: "ARRAY";
		self:arrayItems: items;
	}

	## Configures this node as a map literal expression.
	##
	## @param keys: Array of key [Expression] nodes.
	## @param values: Array of value [Expression] nodes.
	replace local Function is makeMap(Array of Expression is keys, Array of Expression is values){
		self:kind: "MAP";
		self:mapKeys: keys;
		self:mapValues: values;
	}

	## Configures this node as a method or function call expression.
	##
	## @param target: Receiver target [Expression].
	## @param method: Method name string.
	## @param args: Array of [NamedArg] call arguments.
	replace local Function is makeCall(Expression is target, String is method, Array of NamedArg is args){
		self:kind: "CALL";
		self:methodTarget: target;
		self:methodName: method;
		self:methodArgs: args;
	}

	## Configures this node as a binary operator expression.
	##
	## @param op: Binary operator symbol.
	## @param left: Left-hand operand [Expression].
	## @param right: Right-hand operand [Expression].
	replace local Function is makeBinary(String is op, Expression is left, Expression is right){
		self:kind: "BINARY";
		self:binaryOp: op;
		self:leftExpr: left;
		self:rightExpr: right;
	}

	## Configures this node as a unary operator expression.
	##
	## @param op: Unary operator symbol.
	## @param expr: Inner operand [Expression].
	replace local Function is makeUnary(String is op, Expression is expr){
		self:kind: "UNARY";
		self:unaryOp: op;
		self:unaryExpr: expr;
	}

	## Configures this node as an inline ternary `if`/`else` expression.
	##
	## @param condition: Boolean condition [Expression].
	## @param thenExpr: True-branch [Expression].
	## @param elseExpr: False-branch [Expression].
	replace local Function is makeIfElse(Expression is condition, Expression is thenExpr, Expression is elseExpr){
		self:kind: "IF_ELSE";
		self:condExpr: condition;
		self:thenExpr: thenExpr;
		self:elseExpr: elseExpr;
	}

	## Configures this node as a `when` pattern matching expression.
	##
	## @param subject: Subject [Expression] being matched.
	## @param arms: Array of [WhenArm] branches.
	replace local Function is makeWhen(Expression is subject, Array of WhenArm is arms){
		self:kind: "WHEN";
		self:whenSubject: subject;
		self:whenArms: arms;
	}

	## Configures this node as an anonymous function (closure) expression.
	##
	## @param returnType: Return [Type] descriptor.
	## @param params: Array of formal [Parameter] descriptors.
	## @param body: Array of implementation [Statement] nodes.
	replace local Function is makeAnonymousFunction(Type is returnType, Array of Parameter is params, Array of Statement is body){
		self:kind: "ANON_FN";
		self:anonReturnType: returnType;
		self:anonParams: params;
		self:anonBody: body;
	}

	## Returns the expression kind tag.
	##
	## @return: Kind tag string.
	replace local Function of String is getKind(){
		return self:kind;
	}

	## Sets the inferred [Type] descriptor for this expression.
	##
	## @param t: Inferred [Type].
	replace local Function is setInferredType(Type is t){
		self:inferredType: t;
	}

	## Returns the inferred [Type] descriptor for this expression.
	##
	## @return: Inferred [Type] instance.
	replace local Function of Type is getInferredType(){
		return self:inferredType;
	}

	## Sets the resolved type name string populated during semantic analysis.
	##
	## @param t: Resolved type name string.
	replace local Function is setResolvedType(String is t){
		self:resolvedType: t;
	}

	## Returns the resolved type name string populated during semantic analysis.
	##
	## @return: Resolved type name string.
	replace local Function of String is getResolvedType(){
		return self:resolvedType;
	}

	## Sets the one-based source line number for this expression.
	##
	## @param line: One-based line coordinate.
	replace local Function is setLine(Int is line){
		self:line: line;
	}

	## Returns the one-based source line number for this expression.
	##
	## @return: Source line coordinate.
	replace local Function of Int is getLine(){
		return self:line;
	}

}

## Represents a statement node in the Spec syntax tree.
class Statement{

	replace local Array of String is using: [
		base:struct:Array,
		base:reflect:Type,
		base:reflect:Class,
		base:meta:AST
	];

	local String is kind: "";
	local Int is line: 0;
	local Array of String is modifiers;
	local Type is varType;
	local String is varName: "";
	local Expression is initExpr;
	local Boolean is hasInit: false;
	local Expression is assignTarget;
	local Expression is assignValue;
	local Expression is ifCondition;
	local Array of Statement is thenBranch;
	local Array of Statement is elseBranch;
	local Boolean is hasElse: false;
	local Expression is returnExpr;
	local Boolean is hasReturnExpr: false;
	local Class is nestedClass;
	local Expression is exprStmt;
	local Expression is whenSubject;
	local Array of WhenArm is whenArms;

	replace local Function is init(String is kind){
		self:kind: kind;
	}

	replace local Function is varDecl(Array of String is modifiers, Type is varType, String is name, Expression is initExpr, Boolean is hasInit){
		self:kind: "VAR_DECL";
		self:modifiers: modifiers;
		self:varType: varType;
		self:varName: name;
		self:initExpr: initExpr;
		self:hasInit: hasInit;
	}

	replace local Function is assign(Expression is target, Expression is value){
		self:kind: "ASSIGN";
		self:assignTarget: target;
		self:assignValue: value;
	}

	replace local Function is ifStmt(Expression is condition, Array of Statement is thenBranch, Array of Statement is elseBranch, Boolean is hasElse){
		self:kind: "IF";
		self:ifCondition: condition;
		self:thenBranch: thenBranch;
		self:elseBranch: elseBranch;
		self:hasElse: hasElse;
	}

	replace local Function is returnStmt(Expression is expr, Boolean is hasExpr){
		self:kind: "RETURN";
		self:returnExpr: expr;
		self:hasReturnExpr: hasExpr;
	}

	replace local Function is classStmt(Class is nestedClass){
		self:kind: "CLASS";
		self:nestedClass: nestedClass;
	}

	replace local Function is expression(Expression is expr){
		self:kind: "EXPR";
		self:exprStmt: expr;
	}

	replace local Function is whenStmt(Expression is subject, Array of WhenArm is arms){
		self:kind: "WHEN";
		self:whenSubject: subject;
		self:whenArms: arms;
	}

	replace local Function of String is getKind(){
		return self:kind;
	}

	replace local Function is setLine(Int is line){
		self:line: line;
	}

	replace local Function of Int is getLine(){
		return self:line;
	}

}

## Represents the root program node containing all parsed [base:reflect:Class] definitions.
class ProgramNode{

	replace local Array of String is using: [
		base:struct:Array,
		base:reflect:Class
	];

	local Array of Class is classes: [];

	replace local Function is init(Array of Class is classes){
		self:classes: classes;
	}

	replace local Function of Array of Class is getClasses(){
		return self:classes;
	}

	replace local Function is addClass(Class is c){
		self:classes:add(item: c);
	}

	replace local Function is setClasses(Array of Class is classes){
		self:classes: classes;
	}

}

## Represents a pattern matching branch in a `when` statement or expression.
class WhenArm{

	replace local Array of String is using: [
		base:struct:Array,
		base:meta:AST
	];

	local Array of Expression is conditions: [];
	local Boolean is isElse: false;
	local Array of Statement is body: [];
	local Expression is valueExpr;
	local Boolean is hasValueExpr: false;

	replace local Function is init(){
	}

	replace local Function is arm(Array of Expression is conditions, Array of Statement is body){
		self:conditions: conditions;
		self:isElse: false;
		self:body: body;
	}

	replace local Function is elseArm(Array of Statement is body){
		self:isElse: true;
		self:body: body;
	}

	replace local Function is exprArm(Array of Expression is conditions, Expression is value){
		self:conditions: conditions;
		self:isElse: false;
		self:valueExpr: value;
		self:hasValueExpr: true;
	}

	replace local Function is elseExprArm(Expression is value){
		self:isElse: true;
		self:valueExpr: value;
		self:hasValueExpr: true;
	}

}
