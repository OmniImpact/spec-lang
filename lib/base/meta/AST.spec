#! Package base:meta
#! Concrete Abstract Syntax Tree models for code generation, desugaring, and tooling.

## Represents a named argument pair in method calls (e.g. `index: 0`).
class NamedArg{

	replace local Array of String is using: [
		base:meta:AST
	];

	local String is name: "";
	local Expression is value;

	replace local Function is init(String is name, Expression is value){
		self:name: name;
		self:value: value;
	}

	replace local Function of String is getName(){
		return self:name;
	}

	replace local Function of Expression is getValue(){
		return self:value;
	}

}

## Represents an expression node in the Spec syntax tree.
class Expression{

	replace local Array of String is using: [
		base:struct:Array,
		base:reflect:Type,
		base:meta:AST
	];

	local String is kind: "";
	local Type is inferredType;
	local String is stringValue: "";
	local Int is intValue: 0;
	local Float is floatValue: 0.0;
	local Boolean is boolValue: false;
	local Array of String is pathSegments: [];
	local Array of Expression is arrayItems: [];
	local Expression is methodTarget;
	local String is methodName: "";
	local Array of NamedArg is methodArgs: [];
	local String is binaryOp: "";
	local Expression is leftExpr;
	local Expression is rightExpr;
	local String is unaryOp: "";
	local Expression is unaryExpr;

	replace local Function is init(String is kind){
		self:kind: kind;
	}

	replace local Function is makeString(String is val){
		self:kind: "STRING";
		self:stringValue: val;
	}

	replace local Function is makeNumber(Int is val){
		self:kind: "NUMBER";
		self:intValue: val;
	}

	replace local Function is makeFloat(Float is val){
		self:kind: "FLOAT";
		self:floatValue: val;
	}

	replace local Function is makeBool(Boolean is val){
		self:kind: "BOOL";
		self:boolValue: val;
	}

	replace local Function is makeIdent(String is name){
		self:kind: "IDENT";
		self:stringValue: name;
	}

	replace local Function is makePath(Array of String is segments){
		self:kind: "PATH";
		self:pathSegments: segments;
	}

	replace local Function is makeArray(Array of Expression is items){
		self:kind: "ARRAY";
		self:arrayItems: items;
	}

	replace local Function is makeCall(Expression is target, String is method, Array of NamedArg is args){
		self:kind: "CALL";
		self:methodTarget: target;
		self:methodName: method;
		self:methodArgs: args;
	}

	replace local Function is makeBinary(String is op, Expression is left, Expression is right){
		self:kind: "BINARY";
		self:binaryOp: op;
		self:leftExpr: left;
		self:rightExpr: right;
	}

	replace local Function is makeUnary(String is op, Expression is expr){
		self:kind: "UNARY";
		self:unaryOp: op;
		self:unaryExpr: expr;
	}

	replace local Function of String is getKind(){
		return self:kind;
	}

	replace local Function is setInferredType(Type is t){
		self:inferredType: t;
	}

	replace local Function of Type is getInferredType(){
		return self:inferredType;
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
	local Array of String is modifiers: [];
	local Type is varType;
	local String is varName: "";
	local Expression is initExpr;
	local Boolean is hasInit: false;
	local Expression is assignTarget;
	local Expression is assignValue;
	local Expression is ifCondition;
	local Array of Statement is thenBranch: [];
	local Array of Statement is elseBranch: [];
	local Boolean is hasElse: false;
	local Expression is returnExpr;
	local Boolean is hasReturnExpr: false;
	local Class is nestedClass;
	local Expression is exprStmt;

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

	replace local Function of String is getKind(){
		return self:kind;
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

}
