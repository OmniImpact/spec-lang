#! Package base:compiler:ast
#! One formal parameter: a name, a type, and an optional default value.

Class is Parameter{
	namespace: ['base', 'compiler', 'ast'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', Type]
	];

	## Parameter identifier.
	String is name: '';

	## Parameter type descriptor.
	Type is paramType;

	## Default value expression (declaration-side defaults).
	Expression is defaultExpr;

	## True when a default value is present.
	Boolean is hasDefault: false;

	## Initializes a parameter.
	##
	## @param name: Parameter identifier.
	## @param paramType: Parameter type descriptor.
	replace Function is init(String is name, Type is paramType){
		self:name: name;
		self:paramType: paramType;
	}

	## Attaches a default value expression.
	##
	## @param expr: The default value.
	Function is setDefault(Expression is expr){
		self:defaultExpr: expr;
		self:hasDefault: true;
	}
}
