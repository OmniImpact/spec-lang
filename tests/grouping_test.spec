#! Package examples:regression
#! Tracks load-time class grouping (partial classes) via the `group` pseudo-field.

## Grouping: fragments merge into one class at load time.
##
## Guarded behavior:
## - `group: [Name]` fragments merge into the target class; fragments do not
##   exist as types after loading.
## - A group with no primary file is created from the union of fragments.
## - Same-name opt-in partials (class X with group: [X]) merge across
##   duplicate declarations instead of being silently dropped.
## - All three checks print "[PASS]"; any "[FAIL]" is a regression.
##
## ClassInfo Calc never appears as a declaration: it is created from the union
## of CalcArithmetic and CalcText below.
Class is CalcArithmetic{

	replace Array of String is group: [Calc];

	Function of Int is add(Int is a, Int is b){
		return a + b;
	}
}

Class is CalcText{

	replace Array of String is group: [Calc];

	Function of String is shout(String is msg){
		return msg . '!';
	}
}

## Same-name opt-in partial: the two Accumulator declarations merge.
Class is Accumulator{

	replace Array of String is group: [Accumulator];

	local Int is total: 0;

	replace Function is init(Int is start){
		self:total: start;
	}
}

Class is Accumulator{

	replace Array of String is group: [Accumulator];

	Function is bump(Int is by){
		self:total: self:total + by;
	}
}

Class is GroupingTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
	];

	replace Function is init(Map of String to String is args){
		output:line('=== Regression: ClassInfo Grouping ===');

		# Case 1: no-primary group - Calc exists only as a merged union.
		local Calc is calc: Calc:init();
		local Int is sum: calc:add(a: 2, b: 40);
		if (sum == 42) {
			output:line('[PASS] no-primary group: Calc.add(2, 40) = 42');
		} else {
			output:line('[FAIL] no-primary group: expected 42, got ' . sum);
		}

		# Case 2: second fragment's members are reachable on the merged class.
		local String is shouted: calc:shout(msg: 'grouped');
		if (shouted == 'grouped!') {
			output:line('[PASS] merged fragments: Calc.shout works');
		} else {
			output:line('[FAIL] merged fragments: expected \'grouped!\', got ' . shouted);
		}

		# Case 3: same-name opt-in partial merge (field from part 1, method from part 2).
		local Accumulator is acc: Accumulator:init(start: 100);
		acc:bump(by: 1);
		if (acc:total == 101) {
			output:line('[PASS] same-name partial: Accumulator total = 101');
		} else {
			output:line('[FAIL] same-name partial: expected 101, got ' . acc:total);
		}

		output:line('=== End ClassInfo Grouping Regression ===');
	}

}
