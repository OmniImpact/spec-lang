#! specunit: negative
#! expect: Undefined function 'nope' on class 'N2UndefinedBare'

#! N2: bare call with zero providers — the old behavior silently invented
#! CurrentClass_method and died in gcc (E9).

Class is N2UndefinedBare {
	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args) {
		Output:line((nope() as String));
	}
}
