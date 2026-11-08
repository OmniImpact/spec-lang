#! Package base:compiler:ast
#! One statement node.
##
## Spec has no sum types, so a node carries the fields of every kind; the
## fields below are grouped by [StatementKind] and only the group for the
## node's kind is meaningful.
##
## AST nodes are transparent data records: fields are public because the
## compiler passes read and write them directly.

Class is Statement{
	namespace: ['base', 'compiler', 'ast'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', StatementKind],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ast', WhenArm],
		['base', 'compiler', 'ast', ClassInfo]
	];

	## Node category for enum dispatch.
	StatementKind is kind: StatementKind:EXPR;

	## One-based source line where the statement starts.
	Int is line: 0;

	## VAR_DECL: declaration modifiers (e.g. local, contained).
	Array of String is modifiers: [];
	## VAR_DECL: declared type and variable name.
	Type is varType;
	String is varName: '';
	## VAR_DECL: initializer expression and its presence flag.
	Expression is initExpr;
	Boolean is hasInit: false;

	## ASSIGN: assignment target and value.
	Expression is assignTarget;
	Expression is assignValue;

	## IF: condition, branches, and else presence.

	## RETURN: the returned expression and its presence flag.
	Expression is returnExpr;
	Boolean is hasReturnExpr: false;

	## CLASS: a nested class declaration.
	ClassInfo is nestedClass;

	## EXPR: an expression evaluated for effect.
	Expression is exprStmt;

	## WHEN: the subject and arms.
	Expression is whenSubject;
	Array of WhenArm is whenArms: [];

	## FORWARD: merge-forward delegation arguments.
	Array of NamedArg is forwardArgs: [];

	## Initializes a statement node with its kind.
	##
	## @param kind: Node category.
	replace Function is init(StatementKind is kind){
		self:kind: kind;
	}

	## Configures this node as an assignment.
	##
	## @param target: Assignment target expression.
	## @param value: Assigned value expression.
	Function is assign(Expression is target, Expression is value){
		self:kind: StatementKind:ASSIGN;
		self:assignTarget: target;
		self:assignValue: value;
	}

	## Configures this node as a `when` statement.
	##
	## @param subject: Subject being matched.
	## @param arms: The branches.
	Function is whenStmt(Expression is subject, Array of WhenArm is arms){
		self:kind: StatementKind:WHEN;
		self:whenSubject: subject;
		self:whenArms: arms;
	}

	## Sets the one-based source line.
	##
	## @param line: Source line number.
	Function is setLine(Int is line){
		self:line: line;
	}
}
