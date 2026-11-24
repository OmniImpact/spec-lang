#! SpecUnit pilot (converted from the marker-print suite): Byte
#! semantics — cast round-trips, boundaries, and
#! the Byte -> Int -> String rendering chain.

Class of SpecUnitTest is TestByte{

	replace [[String]] is using: [
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

	Function is testByteDataMethods(){
		local Byte is b: 171 as Byte; # 0xAB
		Assert:areEqualInt(171, b:toInt());
		Assert:areEqualInt(171, b:toUInt8() as Int);
		Assert:areEqualString('ab', b:toHex());
		Assert:areEqualInt(10, b:highNibble():toInt());
		Assert:areEqualInt(11, b:lowNibble():toInt());
		Assert:isTrue(b:bit(0));
		Assert:isFalse(b:bit(2));
		Assert:areEqualInt(175, b:setBit(2):toInt());
		Assert:areEqualInt(170, b:clearBit(0):toInt());
		Assert:areEqualInt(170, b:toggleBit(0):toInt());
		Assert:areEqualInt(87, b:rotateLeft(1):toInt());
		Assert:areEqualInt(213, b:rotateRight(1):toInt());
		Assert:isFalse(b:isAscii());

		local Byte is lowerA: 97 as Byte; # 'a'
		Assert:isTrue(lowerA:isAscii());
		Assert:isTrue(lowerA:isAlpha());
		Assert:isTrue(lowerA:isAlphaNum());
		Assert:isTrue(lowerA:isHexDigit());
		Assert:isTrue(lowerA:isPrintable());
		Assert:isFalse(lowerA:isDigit());
		Assert:isFalse(lowerA:isWhitespace());
		Assert:areEqualInt(65, lowerA:toUpper():toInt());
		Assert:areEqualInt(97, lowerA:toUpper():toLower():toInt());

		local Byte is digit5: 53 as Byte; # '5'
		Assert:isTrue(digit5:isDigit());
		Assert:isTrue(digit5:isHexDigit());
		Assert:isTrue(digit5:isAlphaNum());
		Assert:isFalse(digit5:isAlpha());

		local Byte is tab: 9 as Byte;
		Assert:isTrue(tab:isWhitespace());
		Assert:isFalse(tab:isPrintable());
	}

	Function is testByteBase64Helpers(){
		local Byte is chA: 65 as Byte; # 'A' -> 0
		local Byte is chZ: 90 as Byte; # 'Z' -> 25
		local Byte is cha: 97 as Byte; # 'a' -> 26
		local Byte is ch0: 48 as Byte; # '0' -> 52
		local Byte is chPlus: 43 as Byte; # '+' -> 62
		local Byte is chSlash: 47 as Byte; # '/' -> 63
		local Byte is chEq: 61 as Byte; # '=' -> invalid (-1)

		Assert:isTrue(chA:isBase64());
		Assert:isTrue(chPlus:isBase64());
		Assert:isTrue(chSlash:isBase64());
		Assert:isFalse(chEq:isBase64());

		Assert:areEqualInt(0, chA:base64Value());
		Assert:areEqualInt(25, chZ:base64Value());
		Assert:areEqualInt(26, cha:base64Value());
		Assert:areEqualInt(52, ch0:base64Value());
		Assert:areEqualInt(62, chPlus:base64Value());
		Assert:areEqualInt(63, chSlash:base64Value());
		Assert:areEqualInt(-1, chEq:base64Value());

		Assert:areEqualInt(65, (0 as Byte):toBase64Char():toInt());
		Assert:areEqualInt(90, (25 as Byte):toBase64Char():toInt());
		Assert:areEqualInt(97, (26 as Byte):toBase64Char():toInt());
		Assert:areEqualInt(48, (52 as Byte):toBase64Char():toInt());
		Assert:areEqualInt(43, (62 as Byte):toBase64Char():toInt());
		Assert:areEqualInt(47, (63 as Byte):toBase64Char():toInt());
	}
}
