#! Package examples:regression
#! Tracks bitwise operators and their precedence.

## Bitwise operators: & | ^ << >> ~ with C precedence.
##
## Guarded behavior:
## - All six operators compute correct values on Int operands.
## - Precedence matches C: shift binds looser than +, & tighter than ^,
##   ^ tighter than |, all tighter than && / ||.
## - Bitwise results render correctly in concatenations.
## - All checks print "[PASS]"; any "[FAIL]" is a regression.

Class is BitwiseTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Regression: Bitwise Operators ===');

		# Case 1: basic operators.
		local Int is a: 0b1100 & 0b1010;
		local Int is o: 0b1100 | 0b1010;
		local Int is x: 0b1100 ^ 0b1010;
		Conditional:if(check: { a == 8 && o == 14 && x == 6 }, then: {
			Output:line('[PASS] basics: 1100&1010=8, |14, ^6');
		}, else: {
			Output:line('[FAIL] basics: ' . a . ', ' . o . ', ' . x);
		});

		# Case 2: shifts and complement.
		local Int is l: 1 << 6;
		local Int is r: 640 >> 4;
		local Int is c: ~5;
		Conditional:if(check: { l == 64 && r == 40 && c == -6 }, then: {
			Output:line('[PASS] shifts/complement: 1<<6=64, 640>>4=40, ~5=-6');
		}, else: {
			Output:line('[FAIL] shifts/complement: ' . l . ', ' . r . ', ' . c);
		});

		# Case 3: precedence — additive binds tighter than shift.
		local Int is shiftAdd: 1 << 2 + 1;
		Conditional:if(check: { shiftAdd == 8 }, then: {
			Output:line('[PASS] precedence: 1 << 2 + 1 = 8 (shift looser than +)');
		}, else: {
			Output:line('[FAIL] precedence shift: expected 8, got ' . shiftAdd);
		});

		# Case 4: precedence — & tighter than ^ tighter than |:
		# 1 | 2 ^ 3 & 2 = 1 | (2 ^ (3 & 2)) = 1 | 0 = 1.
		local Int is mix: 1 | 2 ^ 3 & 2;
		Conditional:if(check: { mix == 1 }, then: {
			Output:line('[PASS] precedence: 1 | 2 ^ 3 & 2 = 1');
		}, else: {
			Output:line('[FAIL] precedence mix: expected 1, got ' . mix);
		});

		# Case 5: bitmask composition with literals.
		local Int is flags: 0b0000_0100 | 0b0000_0011;
		local Int is cleared: flags & ~(0b0000_0011);
		Conditional:if(check: { flags == 7 && cleared == 4 }, then: {
			Output:line('[PASS] masks: set=7, clear low bits=4');
		}, else: {
			Output:line('[FAIL] masks: ' . flags . ', ' . cleared);
		});

		# Case 6: bitwise results concatenate as Int.
		local Int is masked: 5 & 3;
		local String is msg: 'mask=' . masked;
		Conditional:if(check: { msg == 'mask=1' }, then: {
			Output:line('[PASS] concat: mask=1');
		}, else: {
			Output:line('[FAIL] concat: \'' . msg . '\'');
		});

		Output:line('=== End Bitwise Operators ===');
	}

}
