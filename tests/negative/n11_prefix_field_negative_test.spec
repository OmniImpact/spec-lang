#! specunit: negative
#! expect: Fields are not reachable through the class-name prefix

#! N11: fields are not reachable through a class-name prefix — methods
#! only (§2.3).

Class is N11PrefixField {
	replace Array of Array of String is using: [
		['instimport', 'counter', as StatefulCounter(label: 'x')]
	];

	replace Function is init(Map of String to String is args) {
		Output:line((StatefulCounter:n as String));
	}
}
