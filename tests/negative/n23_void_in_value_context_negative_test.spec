#! N23 (FUNCTIONS.md Part IV V3): a void expression consumed as a value
#! explains itself, derived from the CALLEE'S DECLARATION — the function's
#! name, its void return, and the sibling overloads' parameter lists. No
#! per-class special cases: every callable gets the same note.

Class is N23VoidInValueContext{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', Output],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		# A: the 2-arg if in value context — no else, undefined result.
		local String is a: Conditional:if(check: { true }, then: { 'x' });
		Output:line(a);

		# B: the 4-arg if in value context — finally cannot yield.
		local String is b: Conditional:if(check: { true }, then: { 'x' }, else: { 'y' }, finally: {
			Output:line('cleanup');
		});
		Output:line(b);

		# C: any void call consumed as a value — the general note.
		local Int is c: Output:line('side effect');
		Output:line(c);
	}
}
