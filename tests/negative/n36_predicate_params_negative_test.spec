#! N36: predicate match arms and keys have no subject to bind, so a
#! parameterized closure is a pointed error instead of a silently empty arm.

Class is N36PredicateParams{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		local Int is n: 5;
		match(when: [
			{ n > 1 }: local Function(Int is x){ line('arm ran'); },
			else: { line('else'); }
		]);
	}
}
