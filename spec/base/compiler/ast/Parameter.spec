#! Package base:compiler:ast
#! One formal parameter: a name, a type, and an optional default value.

Class is Parameter{
	replace [String] is namespace: ['base', 'compiler', 'ast'];

	replace [[String]] is using: [
		['base', 'compiler', 'ast', Type]
,
		['base', 'compiler', 'ast', Expression]
	];

	## Parameter identifier.
	String is name: '';

	## Parameter type descriptor.
	Type is paramType: Type:init(name: '');

	## Default value expression (declaration-side defaults).
	Expression is defaultExpr: Expression:Unknown;

	## True when a default value is present.
	Boolean is hasDefault: false;

	## True when declared with `*name` to capture remaining positional or named args.
	Boolean is isVariadic: false;

	## Initializes a parameter.
	##
	## @param name: Parameter identifier.
	## @param paramType: Parameter type descriptor.
	replace Function is init(String is name, Type is paramType){
		:name: name;
		:paramType: paramType;
	}

	## Attaches a default value expression.
	##
	## @param expr: The default value.
	Function is setDefault(Expression is expr){
		:defaultExpr: expr;
		:hasDefault: true;
	}
}
