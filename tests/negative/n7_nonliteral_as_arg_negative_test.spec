#! N7: non-literal argument in the as-form (E1, parser).

Class is N7NonLiteral {
	local Int is seed: 3;

	replace Array of Array of String is using: [
		['base', 'math', as Math(seed)]
	];

	replace Function is init(Map of String to String is args) {}
}
