#! specunit: negative
#! expect: instance-imports 'Math' more than once

#! N5: duplicate as-import bindings (E3).

Class is N5DuplicateAs {
	replace Array of Array of String is using: [
		['base', 'math', as Math()],
		['base', 'math', as Math()]
	];
	replace Function is init(Map of String to String is args) {}
}
