#! N3: bare call with two providers must qualify (§2.3).

Class is N3Collision {
	replace Array of Array of String is using: [
		['base', 'sys', as Output()],
		['base', 'math', as Math()]
	];

	Function of Int is round(){
		return 1;
	}

	replace Function is init(Map of String to String is args) {
		Output:line((round() as String));
	}
}
