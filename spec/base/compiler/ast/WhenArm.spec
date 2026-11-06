#! Package base:compiler:ast
#! One branch of a `when` matching: guard conditions plus a body that is
## either a statement list or a single value expression.

Class is WhenArm{
	namespace: ['base', 'compiler', 'ast'];

	## Guard conditions; any match selects this arm.
	Array of Expression is conditions: [];

	## True for the else arm (no conditions).
	Boolean is isElse: false;

	## Statement body (statement-form arms).
	Array of Statement is body: [];

	## Value expression (expression-form arms).
	Expression is valueExpr;

	## True when this arm carries a value expression.
	Boolean is hasValueExpr: false;

	replace Function is init(){
	}

	## Configures a guarded arm with a statement body.
	##
	## @param conditions: Guard expressions.
	## @param body: The arm's statements.
	Function is arm(Array of Expression is conditions, Array of Statement is body){
		self:conditions: conditions;
		self:isElse: false;
		self:body: body;
	}

	## Configures an else arm with a statement body.
	##
	## @param body: The arm's statements.
	Function is elseArm(Array of Statement is body){
		self:isElse: true;
		self:body: body;
	}

	## Configures a guarded arm with a value expression.
	##
	## @param conditions: Guard expressions.
	## @param value: The arm's value.
	Function is exprArm(Array of Expression is conditions, Expression is value){
		self:conditions: conditions;
		self:isElse: false;
		self:valueExpr: value;
		self:hasValueExpr: true;
	}

	## Configures the else arm with a value expression.
	##
	## @param value: The arm's value.
	Function is elseExprArm(Expression is value){
		self:isElse: true;
		self:valueExpr: value;
		self:hasValueExpr: true;
	}
}
