#! The predicate arm table: the subject-less match — the keys are
#! closures, the first that holds runs its arm, `else` is the
#! fallback. Lowers to the zero-allocation else-if ladder.

Class is PredicateMatchTest{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	## Verifies the value form: the first matching key's yield is the
	## call's value, unified across the arms.
	local Function is testValueForm(){
		local Int is score: 85;
		local String is grade: match(when: [
			{ score >= 90 }: { 'A' },
			{ score >= 80 }: { 'B' },
			{ score >= 70 }: { 'C' },
			else: { 'F' }
		]);
		Conditional:if(check: { grade == 'B' }, then: {
			Output:line('[PASS] predicate match: value form (first true wins)');
		}, else: {
			Output:line('[FAIL] predicate match value form: ' . grade);
		});
	}

	## Verifies the statement form: the first matching key's body runs,
	## later keys are not evaluated.
	local Function is testStatementForm(){
		local Int is hits: 0;
		match(when: [
			{ 1 < 1 }: { hits: hits + 100; },
			{ 2 > 1 }: { hits: hits + 1; },
			{ 3 > 1 }: { hits: hits + 10; }
		]);
		Conditional:if(check: { hits == 1 }, then: {
			Output:line('[PASS] predicate match: statement form (first-true-wins, no fallthrough)');
		}, else: {
			Output:line('[FAIL] predicate match statement form: hits=' . (hits as String));
		});
	}

	## Verifies the else fallback and the no-else statement table
	## (a non-matching table simply runs nothing).
	local Function is testElseAndFallthrough(){
		local String is tag: match(when: [
			{ 1 < 1 }: { 'impossible' },
			else: { 'default' }
		]);
		Conditional:if(check: { tag == 'default' }, then: {
			Output:line('[PASS] predicate match: else fallback');
		}, else: {
			Output:line('[FAIL] predicate match else: ' . tag);
		});
		local Int is touched: 0;
		match(when: [
			{ 1 < 1 }: { touched: touched + 1; }
		]);
		Conditional:if(check: { touched == 0 }, then: {
			Output:line('[PASS] predicate match: a no-else statement table falls through freely');
		}, else: {
			Output:line('[FAIL] predicate match fallthrough: touched=' . (touched as String));
		});
	}

	## Verifies the bare form: the predicate table served through the
	## merged as-import scope, no provider prefix.
	local Function is testBareForm(){
		local Int is n: 42;
		local String is label: match(when: [
			{ n > 100 }: { 'huge' },
			{ n > 10 }:  { 'big' },
			else: { 'small' }
		]);
		Conditional:if(check: { label == 'big' }, then: {
			Output:line('[PASS] predicate match: bare through the as-import');
		}, else: {
			Output:line('[FAIL] predicate match bare form: ' . label);
		});
	}

	## Verifies a multi-statement key: its leading statements run only
	## after the earlier keys fail, in scope of its own condition.
	local Function is testKeyPrefix(){
		local Int is n: 5;
		local Int is hits: 0;
		match(when: [
			{ n > 100 }: { hits: hits + 1; },
			{ local Int is t: n * 2; t > 8 }: { hits: hits + 10; },
			else: { hits: hits + 100; }
		]);
		Conditional:if(check: { hits == 10 }, then: {
			Output:line('[PASS] predicate match: multi-statement key evaluates lazily in scope');
		}, else: {
			Output:line('[FAIL] predicate match key prefix: hits=' . (hits as String));
		});
	}

	## Entry point.
	##
	## @param args: Unused CLI arguments map.
	replace Function is init(Map of String to String is args){
		Output:line('=== Predicate Match Test ===');
		self:testValueForm();
		self:testStatementForm();
		self:testElseAndFallthrough();
		self:testBareForm();
		self:testKeyPrefix();
		Output:line('=== done ===');
	}
}
