#! SpecUnit sweep (from predicate_match_test.spec): the predicate arm
#! table — the subject-less match. The keys are closures, the first that
#! holds runs its arm, `else` is the fallback; lowers to the
#! zero-allocation else-if ladder. Covers the value form, the statement
#! form (no fallthrough), the else fallback, the no-else statement
#! table, the bare form through the merged as-import scope, and a
#! multi-statement key evaluated lazily in scope.

Class of SpecUnitTest is TestPredicateMatch{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	## Verifies the value form: the first matching key's yield is the
	## call's value, unified across the arms.
	Function is testValueForm(){
		local Int is score: 85;
		local String is grade: match(when: [
			{ score >= 90 }: { 'A' },
			{ score >= 80 }: { 'B' },
			{ score >= 70 }: { 'C' },
			else: { 'F' }
		]);
		Assert:areEqualString('B', grade);
	}

	## Verifies the statement form: the first matching key's body runs,
	## later keys are not evaluated.
	Function is testStatementForm(){
		local Int is hits: 0;
		match(when: [
			{ 1 < 1 }: { hits: hits + 100; },
			{ 2 > 1 }: { hits: hits + 1; },
			{ 3 > 1 }: { hits: hits + 10; }
		]);
		Assert:areEqualInt(1, hits);
	}

	## Verifies the else fallback.
	Function is testElseFallback(){
		local String is tag: match(when: [
			{ 1 < 1 }: { 'impossible' },
			else: { 'default' }
		]);
		Assert:areEqualString('default', tag);
	}

	## Verifies the no-else statement table: a non-matching table
	## simply runs nothing.
	Function is testNoElseFallthrough(){
		local Int is touched: 0;
		match(when: [
			{ 1 < 1 }: { touched: touched + 1; }
		]);
		Assert:areEqualInt(0, touched);
	}

	## Verifies the bare form: the predicate table served through the
	## merged as-import scope, no provider prefix.
	Function is testBareForm(){
		local Int is n: 42;
		local String is label: match(when: [
			{ n > 100 }: { 'huge' },
			{ n > 10 }:  { 'big' },
			else: { 'small' }
		]);
		Assert:areEqualString('big', label);
	}

	## Verifies a multi-statement key: its leading statements run only
	## after the earlier keys fail, in scope of its own condition.
	Function is testKeyPrefix(){
		local Int is n: 5;
		local Int is hits: 0;
		match(when: [
			{ n > 100 }: { hits: hits + 1; },
			{ local Int is t: n * 2; t > 8 }: { hits: hits + 10; },
			else: { hits: hits + 100; }
		]);
		Assert:areEqualInt(10, hits);
	}
}
