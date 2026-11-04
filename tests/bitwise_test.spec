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

	replace Array of String is using: [
		base:io:Output
	];

	replace Function is init(Map of String to String is args){
		output:line("=== Regression: Bitwise Operators ===");

		# Case 1: basic operators.
		local Int is a: 0b1100 & 0b1010;
		local Int is o: 0b1100 | 0b1010;
		local Int is x: 0b1100 ^ 0b1010;
		if (a == 8 && o == 14 && x == 6) {
			output:line("[PASS] basics: 1100&1010=8, |14, ^6");
		} else {
			output:line("[FAIL] basics: " . a . ", " . o . ", " . x);
		}

		# Case 2: shifts and complement.
		local Int is l: 1 << 6;
		local Int is r: 640 >> 4;
		local Int is c: ~5;
		if (l == 64 && r == 40 && c == -6) {
			output:line("[PASS] shifts/complement: 1<<6=64, 640>>4=40, ~5=-6");
		} else {
			output:line("[FAIL] shifts/complement: " . l . ", " . r . ", " . c);
		}

		# Case 3: precedence — additive binds tighter than shift.
		local Int is shiftAdd: 1 << 2 + 1;
		if (shiftAdd == 8) {
			output:line("[PASS] precedence: 1 << 2 + 1 = 8 (shift looser than +)");
		} else {
			output:line("[FAIL] precedence shift: expected 8, got " . shiftAdd);
		}

		# Case 4: precedence — & tighter than ^ tighter than |:
		# 1 | 2 ^ 3 & 2 = 1 | (2 ^ (3 & 2)) = 1 | 0 = 1.
		local Int is mix: 1 | 2 ^ 3 & 2;
		if (mix == 1) {
			output:line("[PASS] precedence: 1 | 2 ^ 3 & 2 = 1");
		} else {
			output:line("[FAIL] precedence mix: expected 1, got " . mix);
		}

		# Case 5: bitmask composition with literals.
		local Int is flags: 0b0000_0100 | 0b0000_0011;
		local Int is cleared: flags & ~(0b0000_0011);
		if (flags == 7 && cleared == 4) {
			output:line("[PASS] masks: set=7, clear low bits=4");
		} else {
			output:line("[FAIL] masks: " . flags . ", " . cleared);
		}

		# Case 6: bitwise results concatenate as Int.
		local Int is masked: 5 & 3;
		local String is msg: "mask=" . masked;
		if (msg == "mask=1") {
			output:line("[PASS] concat: mask=1");
		} else {
			output:line("[FAIL] concat: '" . msg . "'");
		}

		output:line("=== End Bitwise Operators ===");
	}

}
