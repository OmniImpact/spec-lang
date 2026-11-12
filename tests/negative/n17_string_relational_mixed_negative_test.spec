#! specunit: negative
#! expect: requires two String operands

#! N17: relational ordering between String and non-String is rejected
#! (hardening, D5).

Class is N17StringRelationalMixed {
	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args) {
		local String is s: 'm';
		local Int is n: 5;
		Output:line((s >= n) as String);
	}
}
