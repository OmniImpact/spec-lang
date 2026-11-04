#! Package examples:regression
#! Tracks numeric base literals and base conversion builtins.

## Base literals (0x / 0b / 0o), underscore separators, and conversion builtins.
##
## Guarded behavior:
## - Prefix literals normalize to correct decimal values (no C octal footgun:
##   a bare leading zero stays decimal).
## - Separators work in every base.
## - Int:toBase formats with optional zero padding; String:parseInt parses
##   with optional base and prefix auto-detection, returning default on
##   invalid input.
## - All checks print "[PASS]"; any "[FAIL]" is a regression.

Class is NumericBasesTest{

	replace Array of String is using: [
		base:struct:Array,
		base:io:Output
	];

	replace Function is init(Map of String to String is args){
		output:line("=== Regression: Numeric Bases ===");

		# Case 1: literal values.
		local Int is hex: 0xFF;
		local Int is bin: 0b1010;
		local Int is oct: 0o755;
		local Int is decLeadingZero: 015;
		if (hex == 255 && bin == 10 && oct == 493 && decLeadingZero == 15) {
			output:line("[PASS] literals: 0xFF=255, 0b1010=10, 0o755=493, 015=15 (decimal)");
		} else {
			output:line("[FAIL] literals: " . hex . ", " . bin . ", " . oct . ", " . decLeadingZero);
		}

		# Case 2: separators in all bases.
		local Int is million: 1_000_000;
		local Int is spaced: 0xFF_EC;
		local Int is bitSplit: 0b1010_0011;
		if (million == 1000000 && spaced == 65516 && bitSplit == 163) {
			output:line("[PASS] separators: 1_000_000, 0xFF_EC, 0b1010_0011");
		} else {
			output:line("[FAIL] separators: " . million . ", " . spaced . ", " . bitSplit);
		}

		# Case 3: toBase formatting with padding.
		local String is hexOut: 65516:toBase(base: 16);
		local String is padded: 10:toBase(base: 2, digits: 8);
		if (hexOut == "ffec" && padded == "00001010") {
			output:line("[PASS] toBase: 65516->ffec, 10->00001010 (padded)");
		} else {
			output:line("[FAIL] toBase: '" . hexOut . "', '" . padded . "'");
		}

		# Case 4: parseInt with base and prefix auto-detection.
		local Int is parsed: "1F90":parseInt(base: 16, default: -1);
		local Int is prefixed: "0b1010":parseInt(default: -1);
		local Int is octal: "0o755":parseInt(default: -1);
		if (parsed == 8080 && prefixed == 10 && octal == 493) {
			output:line("[PASS] parseInt: 1F90=8080, 0b1010=10, 0o755=493");
		} else {
			output:line("[FAIL] parseInt: " . parsed . ", " . prefixed . ", " . octal);
		}

		# Case 5: fallible parse returns default; separators tolerated.
		local Int is bad: "0xGG":parseInt(base: 16, default: -1);
		local Int is sep: "1_000":parseInt(default: -1);
		if (bad == -1 && sep == 1000) {
			output:line("[PASS] parseInt defaults: garbage->-1, 1_000=1000");
		} else {
			output:line("[FAIL] parseInt defaults: " . bad . ", " . sep);
		}

		# Case 6: round trip.
		local Int is original: 4919;
		local Int is roundTrip: original:toBase(base: 16):parseInt(base: 16, default: -1);
		if (roundTrip == original) {
			output:line("[PASS] round trip: 4919 -> hex -> 4919");
		} else {
			output:line("[FAIL] round trip: got " . roundTrip);
		}

		# Case 7: negative values survive both directions.
		local Int is neg: -42;
		local String is negHex: neg:toBase(base: 16);
		local Int is negBack: negHex:parseInt(base: 16, default: -1);
		if (negHex == "-2a" && negBack == -42) {
			output:line("[PASS] negatives: -42 -> -2a -> -42");
		} else {
			output:line("[FAIL] negatives: '" . negHex . "' -> " . negBack);
		}

		output:line("=== End Numeric Bases ===");
	}

}
