#! SpecUnit sweep (from numeric_bases_test.spec): numeric base
#! literals (0x / 0b / 0o), underscore separators in every base,
#! Int:toBase formatting with zero padding, String:parseInt with base
#! and prefix auto-detection, fallible defaults, round trips, and
#! negative values in both directions.

Class of SpecUnitTest is TestNumericBases{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	## Case 1: prefix literals normalize to correct decimal values
	## (no C octal footgun: a bare leading zero stays decimal).
	Function is testBaseLiterals(){
		local Int is hex: 0xFF;
		local Int is bin: 0b1010;
		local Int is oct: 0o755;
		local Int is decLeadingZero: 015;
		Assert:areEqualInt(255, hex);
		Assert:areEqualInt(10, bin);
		Assert:areEqualInt(493, oct);
		Assert:areEqualInt(15, decLeadingZero);
	}

	## Case 2: separators work in every base.
	Function is testSeparators(){
		local Int is million: 1_000_000;
		local Int is spaced: 0xFF_EC;
		local Int is bitSplit: 0b1010_0011;
		Assert:areEqualInt(1000000, million);
		Assert:areEqualInt(65516, spaced);
		Assert:areEqualInt(163, bitSplit);
	}

	## Case 3: toBase formats with optional zero padding.
	Function is testToBasePadding(){
		local String is hexOut: 65516:toBase(base: 16);
		local String is padded: 10:toBase(base: 2, digits: 8);
		Assert:areEqualString('ffec', hexOut);
		Assert:areEqualString('00001010', padded);
	}

	## Case 4: parseInt with base and prefix auto-detection.
	Function is testParseIntPrefixes(){
		local Int is parsed: '1F90':parseInt(base: 16, default: -1);
		local Int is prefixed: '0b1010':parseInt(default: -1);
		local Int is octal: '0o755':parseInt(default: -1);
		Assert:areEqualInt(8080, parsed);
		Assert:areEqualInt(10, prefixed);
		Assert:areEqualInt(493, octal);
	}

	## Case 5: fallible parse returns default; separators tolerated.
	Function is testParseIntDefaults(){
		local Int is bad: '0xGG':parseInt(base: 16, default: -1);
		local Int is sep: '1_000':parseInt(default: -1);
		Assert:areEqualInt(-1, bad);
		Assert:areEqualInt(1000, sep);
	}

	## Case 6: round trip through hex.
	Function is testRoundTrip(){
		local Int is original: 4919;
		local Int is roundTrip: original:toBase(base: 16):parseInt(base: 16, default: -1);
		Assert:areEqualInt(4919, roundTrip);
	}

	## Case 7: negative values survive both directions.
	Function is testNegatives(){
		local Int is neg: -42;
		local String is negHex: neg:toBase(base: 16);
		local Int is negBack: negHex:parseInt(base: 16, default: -1);
		Assert:areEqualString('-2a', negHex);
		Assert:areEqualInt(-42, negBack);
	}
}
