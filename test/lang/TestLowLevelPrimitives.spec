#! Unit tests for native low-level scalar primitives:
#! Int8, Int16, Int32, Int128, ISize, UInt128, USize, Float32, Rune, RawPtr.

Class of SpecUnitTest is TestLowLevelPrimitives{
	replace [[String]] is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Mem()]
	];

	Function is testSignedNarrowInts(){
		local Int8 is a: 120 as Int8;
		local Int8 is b: 10 as Int8;
		local Int8 is wrapped: a + b;
		# 120 + 10 = 130 -> -126 in signed 8-bit two's complement
		Assert:areEqualInt(-126, wrapped as Int);
		Assert:isTrue(wrapped < (0 as Int8));

		local Int8 is neg: -16 as Int8;
		# Arithmetic right shift preserves sign bit
		Assert:areEqualInt(-4, (neg >> 2) as Int);
		local Int8 is c8: 127 as Int8;
		c8++;
		Assert:areEqualInt(-128, c8 as Int);

		local Int16 is s16: 32767 as Int16;
		local Int16 is s16w: s16 + (1 as Int16);
		Assert:areEqualInt(-32768, s16w as Int);

		local Int32 is s32: 2147483647 as Int32;
		local Int32 is s32w: s32 + (1 as Int32);
		Assert:areEqualInt(-2147483648, s32w as Int);
		Assert:areEqualInt(-1073741824, (s32w / (2 as Int32)) as Int);
	}

	Function is test128BitIntegers(){
		local UInt128 is one: 1 as UInt128;
		local UInt128 is big: one << 100;
		local UInt128 is back: big >> 100;
		Assert:areEqualInt(1, back as Int);
		Assert:isTrue(big > one);

		# Verify high bits above 64 survive arithmetic
		local UInt128 is hi: (1 as UInt128) << 70;
		local UInt128 is lo: 42 as UInt128;
		local UInt128 is sum: hi + lo;
		Assert:areEqualInt(42, (sum - hi) as Int);
		Assert:areEqualInt(1, (sum >> 70) as Int);

		# Signed 128-bit negative arithmetic and comparison
		local Int128 is neg128: -(1 as Int128);
		local Int128 is shiftedNeg: neg128 << 80;
		Assert:isTrue(shiftedNeg < (0 as Int128));
		Assert:areEqualInt(-1, (shiftedNeg >> 80) as Int);
	}

	Function is testISizeUSizeAndRune(){
		local ISize is isz: -42 as ISize;
		Assert:areEqualInt(-42, isz as Int);
		Assert:isTrue(isz < (0 as ISize));

		local USize is usz: -1 as USize;
		Assert:isTrue(usz > (1 as USize));
		Assert:areEqualInt(1, (usz >> 63) as Int);

		# Unicode scalar value (e.g. U+1F600 = 128512)
		local Rune is r: 128512 as Rune;
		Assert:areEqualInt(128512, r as Int);
		Assert:isTrue(r > (65 as Rune));
	}

	Function is testFloat32(){
		local Float32 is x: 1.5 as Float32;
		local Float32 is y: 2.25 as Float32;
		local Float32 is s: x + y;
		Assert:isTrue(s == (3.75 as Float32));
		Assert:isTrue(s > x);
		local Float32 is negS: -s;
		Assert:isTrue(negS < (0.0 as Float32));
		# Widen Float32 -> Float
		local Float is wide: s as Float;
		Assert:isTrue(wide == 3.75);
		# Float32 -> Int truncation
		Assert:areEqualInt(3, s as Int);
	}

	Function is testRawPtr(){
		local Int is addr: Mem:alloc(bytes: 16);
		local RawPtr is p: addr as RawPtr;
		local Int is roundTrip: p as Int;
		Assert:areEqualInt(addr, roundTrip);
		local RawPtr is p2: addr as RawPtr;
		Assert:isTrue(p == p2);
		Mem:free(ptr: addr);
	}
}
