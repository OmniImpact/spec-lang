#! N15: mixing positional and named arguments is rejected (FUNCTIONS.md §I.3).

Class is N15Mixed {
	replace Array of Array of String is using: [
		['base', 'io', as Output()]
	];

	Function of Int is f(Int is a, Int is b){
		return a + b;
	}

	replace Function is init(Map of String to String is args){
		local Int is x: f(1, b: 2);
		Output:line((x as String));
	}
}
