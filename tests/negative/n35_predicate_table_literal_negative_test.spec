#! N35 (the predicate match landing): the predicate arm table is
#! compile-time only — a runtime map can neither preserve scan order
#! nor carry closure keys, so a non-literal predicate table is a
#! pointed error instead of silent garbage.

Class is N35PredicateTableLiteral{
	namespace: ['test'];

	replace Array of Array of String is using: [
		
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		local Map of Any to Any is table: [:];
		local String is tag: match(when: table); local Int is unused: tag:length();
	}
}
