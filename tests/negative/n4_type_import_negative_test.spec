#! N4: prefix call on a type-imported class, non-init member (E5).

Class is N4TypeImport {
	replace Array of Array of String is using: [
		['base', 'math', Math]
	];

	replace Function is init(Map of String to String is args) {
		Output:line((Math:abs(-1) as String));
	}
}
