#! Package base:compiler:ast
#! One statement node, modeled as a sum type.
##
## Statements are represented as an enhanced enum (sum type): each variant
## carries only the payload fields relevant to its kind, while shared product
## members (like source line and category) are defined once on the base class.

Enum is Statement {
	namespace: ['base', 'compiler', 'ast'],

	using: [
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', StatementKind],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ast', ClassInfo]
	],

	VarDecl(Array of String is modifiers, Type is varType, String is varName, Expression is initExpr, Boolean is hasInit),
	Assign(Expression is assignTarget, Expression is assignValue),
	Return(Expression is returnExpr, Boolean is hasReturnExpr),
	ClassDecl(ClassInfo is nestedClass),
	Expr(Expression is exprStmt),
	Forward(Array of NamedArg is forwardArgs),

	## Node category for enum dispatch and backwards compatibility.
	StatementKind is kind: StatementKind:EXPR;

	## One-based source line where the statement starts.
	Int is line: 0;

	## Sets the one-based source line.
	##
	## @param line: Source line number.
	Function of Statement is setLine(Int is line){
		self:line: line;
		return self;
	}
}
