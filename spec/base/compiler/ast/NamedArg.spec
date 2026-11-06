#! Package base:compiler:ast
#! One call argument: a name (empty when positional) and its value.

Class is NamedArg{
	namespace: ['base', 'compiler', 'ast'];

	## Argument key; empty for positional arguments.
	String is name: '';

	## The argument's value expression.
	Expression is value;

	## Initializes a named argument pair.
	##
	## @param name: Argument key (empty when positional).
	## @param value: Argument value expression.
	replace Function is init(String is name, Expression is value){
		self:name: name;
		self:value: value;
	}
}
