#! specunit: negative
#! expect: 'GTarget' is not imported by 'N18UnimportedType'

#! N18: a dependency's dependency is loaded but not yours — type positions
#! and construction require the import (§I.6, Option A).

Class is N18UnimportedType {
	replace Array of Array of String is using: [
		['n18', 'mid', GMid],
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args) {
		local GTarget is t: GTarget:init();
		Output:line((t:n as String));
	}
}
