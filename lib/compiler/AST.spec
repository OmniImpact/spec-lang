class TypeNode{

	replace local Array of String is using: [
		base:struct:Array
	];

	local String is name: "";
	local Array of TypeNode is params: [];

	replace local Function is init(String is name){
		self:name: name;
		self:params: [];
	}

	replace local Function is withParams(String is name, Array of TypeNode is params){
		self:name: name;
		self:params: params;
	}

	replace local Function of String is getName(){
		return self:name;
	}

}

class NamedArg{

	local String is name: "";
	local Expression is value;

	replace local Function is init(String is name, Expression is value){
		self:name: name;
		self:value: value;
	}

}

class Parameter{

	local String is name: "";
	local TypeNode is paramType;

	replace local Function is init(String is name, TypeNode is paramType){
		self:name: name;
		self:paramType: paramType;
	}

}

class Expression{

	replace local Array of String is using: [
		base:struct:Array,
		compiler:AST
	];

	local String is kind: "";
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

}

class Statement{

	replace local Array of String is using: [
		base:struct:Array,
		compiler:AST
	];

	local String is kind: "";
	local Array of String is modifiers: [];
	local TypeNode is varType;
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
	local ClassDef is nestedClass;
	local Expression is exprStmt;

	replace local Function is init(String is kind){
		self:kind: kind;
	}

	replace local Function is varDecl(Array of String is modifiers, TypeNode is varType, String is name, Expression is initExpr, Boolean is hasInit){
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

	replace local Function is classStmt(ClassDef is classDef){
		self:kind: "CLASS";
		self:nestedClass: classDef;
	}

	replace local Function is expression(Expression is expr){
		self:kind: "EXPR";
		self:exprStmt: expr;
	}

	replace local Function of String is getKind(){
		return self:kind;
	}

}

class Member{

	replace local Array of String is using: [
		base:struct:Array,
		compiler:AST
	];

	local String is kind: "";
	local Array of String is modifiers: [];
	local TypeNode is memberType;
	local String is name: "";
	local Array of Parameter is params: [];
	local Array of Statement is body: [];
	local Expression is initExpr;
	local Boolean is hasInit: false;
	local ClassDef is nestedClass;

	replace local Function is init(String is kind){
		self:kind: kind;
	}

	replace local Function is method(Array of String is modifiers, TypeNode is retType, String is name, Array of Parameter is params, Array of Statement is body){
		self:kind: "METHOD";
		self:modifiers: modifiers;
		self:memberType: retType;
		self:name: name;
		self:params: params;
		self:body: body;
	}

	replace local Function is field(Array of String is modifiers, TypeNode is fieldType, String is name, Expression is initExpr, Boolean is hasInit){
		self:kind: "FIELD";
		self:modifiers: modifiers;
		self:memberType: fieldType;
		self:name: name;
		self:initExpr: initExpr;
		self:hasInit: hasInit;
	}

	replace local Function is classMember(ClassDef is classDef){
		self:kind: "CLASS";
		self:nestedClass: classDef;
	}

	replace local Function of String is getKind(){
		return self:kind;
	}

	replace local Function of String is getName(){
		return self:name;
	}

}

class ClassDef{

	replace local Array of String is using: [
		base:struct:Array,
		compiler:AST
	];

	local String is name: "";
	local String is baseClass: "";
	local Array of Member is members: [];

	replace local Function is init(String is name, String is baseClass, Array of Member is members){
		self:name: name;
		self:baseClass: baseClass;
		self:members: members;
	}

	replace local Function of String is getName(){
		return self:name;
	}

	replace local Function of String is getBaseClass(){
		return self:baseClass;
	}

	replace local Function of Array of Member is getMembers(){
		return self:members;
	}

}

class ProgramNode{

	replace local Array of String is using: [
		base:struct:Array,
		compiler:AST
	];

	local Array of ClassDef is classes: [];

	replace local Function is init(Array of ClassDef is classes){
		self:classes: classes;
	}

	replace local Function of Array of ClassDef is getClasses(){
		return self:classes;
	}

}
