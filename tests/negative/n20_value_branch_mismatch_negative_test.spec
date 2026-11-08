#! N20 (FUNCTIONS.md Part II): the two yields of a value-yielding branch
#! must unify. String and Int cannot both be the branch's value.

Class is N20ValueBranchMismatch{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		local String is x: Conditional:branch(check: { 1 > 0 }, then: { 'text' }, otherwise: { 42 });
		Output:line(x);
	}
}
