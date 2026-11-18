#! SpecUnit pilot (converted from the marker-print suite): Byte
#! semantics — cast round-trips, boundaries, and
#! the Byte -> Int -> String rendering chain.

Class of SpecUnitTest is TestByte{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	Function is testSmallValueRoundTrip(){
		local Byte is b97: 97 as Byte;
		Assert:areEqualInt(97, b97 as Int);
	}

	Function is testMidRangeRoundTrip(){
		local Byte is b128: 128 as Byte;
		Assert:areEqualInt(128, b128 as Int);
	}

	Function is testBoundaries(){
		local Byte is b0: 0 as Byte;
		local Byte is b255: 255 as Byte;
		Assert:areEqualInt(0, b0 as Int);
		Assert:areEqualInt(255, b255 as Int);
	}

	Function is testComputedCast(){
		local Int is computed: 64 * 2;
		local Byte is bexpr: computed as Byte;
		Assert:areEqualInt(128, bexpr as Int);
	}

	Function is testWidenAndRenderChain(){
		local Byte is stored: 72 as Byte;
		local Int is widened: stored as Int;
		local String is rendered: widened as String;
		Assert:areEqualString('72', rendered);
	}

	Function is testByteAsByteIdentity(){
		local Byte is stored: 72 as Byte;
		local Byte is same: stored as Byte;
		Assert:areEqualInt(72, same as Int);
	}
}
