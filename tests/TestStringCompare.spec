#! SpecUnit sweep (from string_compare_test.spec): D5 hardening —
#! relational operators on String compare lexicographically through
#! the floor, never by pointer: ordering, reflexivity, prefix
#! ordering, and the false 'aa' > 'ab' case.

Class of SpecUnitTest is TestStringCompare{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	## Lexicographic ordering in both directions.
	Function is testLexicographicOrdering(){
		local String is a: 'apple';
		local String is b: 'banana';
		Assert:isTrue(a < b && b > a);
	}

	## Reflexivity of <= and >=.
	Function is testReflexivity(){
		local String is a: 'apple';
		Assert:isTrue(a <= a && a >= a);
	}

	## Prefix ordering: apple < applf.
	Function is testPrefixOrdering(){
		local String is a: 'apple';
		local String is a2: 'applf';
		Assert:isTrue(a < a2 && a2 > a);
	}

	## 'aa' > 'ab' is false.
	Function is testNotGreaterThan(){
		Assert:isFalse('aa' > 'ab');
	}
}
