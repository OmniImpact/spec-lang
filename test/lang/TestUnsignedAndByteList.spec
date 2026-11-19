#! Unit tests for UInt8/UInt16/UInt32/UInt64 primitives, List of Byte binary
#! helpers, while early break/continue via Function of Boolean, and OS CSPRNG.

Class of SpecUnitTest is TestUnsignedAndByteList{
	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', List],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Mem()]
	];

	Function is testUInt8ArithmeticAndWrap(){
		local UInt8 is a: 250 as UInt8;
		local UInt8 is b: 10 as UInt8;
		local UInt8 is sum: a + b;
		Assert:areEqualInt(4, sum as Int);

		local UInt8 is diff: (5 as UInt8) - (10 as UInt8);
		Assert:areEqualInt(251, diff as Int);

		local UInt8 is shifted: (240 as UInt8) >> (4 as UInt8);
		Assert:areEqualInt(15, shifted as Int);

		local UInt8 is inv: ~(0 as UInt8);
		Assert:areEqualInt(255, inv as Int);
	}

	Function is testUInt16AndUInt32(){
		local UInt16 is p: 65535 as UInt16;
		local UInt16 is pWrap: p + (2 as UInt16);
		Assert:areEqualInt(1, pWrap as Int);

		local UInt32 is hi: 4294967295 as UInt32;
		local UInt32 is hiPlus: hi + (1 as UInt32);
		Assert:areEqualInt(0, hiPlus as Int);

		local UInt32 is rsh: (2147483648 as UInt32) >> (31 as UInt32);
		Assert:areEqualInt(1, rsh as Int);

		local UInt32 is inv32: ~(0 as UInt32);
		Assert:areEqualInt(4294967295, inv32 as Int);
	}

	Function is testUInt64UnsignedShiftAndCompare(){
		local UInt64 is negSignedBits: -1 as UInt64;
		local UInt64 is one: 1 as UInt64;
		# Unsigned comparison: 0xFFFFFFFFFFFFFFFF > 1 (unlike signed -1 < 1)
		Assert:isTrue(negSignedBits > one);
		Assert:isFalse(negSignedBits < one);
		# Logical right shift by 63 yields 1 (not -1)
		local UInt64 is topBit: negSignedBits >> (63 as UInt64);
		Assert:areEqualInt(1, topBit as Int);
		# Unsigned division: 0xFFFFFFFFFFFFFFFF / 2 == 0x7FFFFFFFFFFFFFFF
		local UInt64 is half: negSignedBits / (2 as UInt64);
		Assert:areEqualInt(9223372036854775807, half as Int);
	}

	Function is testWhileEarlyBreakAndContinue(){
		local Int is sum: 0;
		local Int is i: 0;
		while({ i < 100 }, local Function of Boolean(){
			i: i + 1;
			if({ i == 3 }, {
				return true;
			});
			if({ i == 6 }, {
				return false;
			});
			sum: sum + i;
			return true;
		});
		# Added 1 + 2 + 4 + 5 = 12, broke at i == 6
		Assert:areEqualInt(6, i);
		Assert:areEqualInt(12, sum);
	}

	Function is testByteListBinaryHelpers(){
		local [Byte] is buf;
		buf:pushU16BE(4660);         # 0x1234
		buf:pushU32BE(305419896);    # 0x12345678
		buf:pushU32LE(305419896);    # 0x78563412
		Assert:areEqualInt(10, buf:length());
		Assert:areEqualInt(4660, buf:readU16BE(0));
		Assert:areEqualInt(305419896, buf:readU32BE(2));
		Assert:areEqualInt(305419896, buf:readU32LE(6));

		local [Byte] is sub: buf:slice(2, 6);
		Assert:areEqualInt(4, sub:length());
		Assert:areEqualInt(305419896, sub:readU32BE(0));

		local [Byte] is dst;
		dst:appendBytes(sub);
		dst:appendRange(buf, 0, 2);
		Assert:areEqualInt(6, dst:length());
		Assert:areEqualInt(305419896, dst:readU32BE(0));
		Assert:areEqualInt(4660, dst:readU16BE(4));
	}

	Function is testOsCsprngRandomBytes(){
		local Int is b1: Mem:alloc(bytes: 32);
		local Int is b2: Mem:alloc(bytes: 32);
		local Int is rc1: Mem:randomBytes(dstAddr: b1, len: 32);
		local Int is rc2: Mem:randomBytes(dstAddr: b2, len: 32);
		Assert:areEqualInt(0, rc1);
		Assert:areEqualInt(0, rc2);
		Assert:isTrue(Mem:cmp(a: b1, b: b2, bytes: 32) != 0);
		Mem:free(ptr: b1);
		Mem:free(ptr: b2);
	}
}
