#! N19: a scoped region on a Conditional whose parameters are already
#! bound has no open scope slot — the remainder would silently become
#! the else branch (FUNCTIONS.md §as).

Class is N19AsFilledBranch {
	replace Array of Array of String is using: [
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args) {
		as: Conditional:branch(check: true, then: {
			Output:line('then');
		});
		Output:line('cleanup');
	}
}
