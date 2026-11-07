Class is HelloWorld{

	# Scope, Type, "is" binds identifier, ":" is assignment/access, lines end in ;
	local String is greeting: 'Hello';

	# Imports: "using" is a native ClassInfo array property overridden using "replace"
	replace Array of Array of String is using: [
		['base', 'struct', Map],
		['base', 'io'],
	];

	# Entrypoint init method using the Function type
	replace Function is init(Map of String to String is args){

		# Local variable declaration matching "<Type> is <name>: <value>;"
		local String is name: args:getString(key:'name', default:'User');

		# in io: package
		output:line(greeting.' '.name);
	}

}
