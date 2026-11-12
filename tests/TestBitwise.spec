#! SpecUnit sweep (from bitwise_test.spec): bitwise operators and their
#! precedence — & | ^ << >> ~ with C precedence, mask composition, and
#! bitwise results in concatenations.

Class of SpecUnitTest is TestBitwise{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	Function is testBasics(){
		local Int is a: 0b1100 & 0b1010;
		local Int is o: 0b1100 | 0b1010;
		local Int is x: 0b1100 ^ 0b1010;
		Assert:areEqualInt(8, a);
		Assert:areEqualInt(14, o);
		Assert:areEqualInt(6, x);
	}

	Function is testShiftsAndComplement(){
		local Int is l: 1 << 6;
		local Int is r: 640 >> 4;
		local Int is c: ~5;
		Assert:areEqualInt(64, l);
		Assert:areEqualInt(40, r);
		Assert:areEqualInt(-6, c);
	}

	Function is testPrecedenceShift(){
		local Int is shiftAdd: 1 << 2 + 1;
		Assert:areEqualInt(8, shiftAdd);
	}

	Function is testPrecedenceMix(){
		local Int is mix: 1 | 2 ^ 3 & 2;
		Assert:areEqualInt(1, mix);
	}

	Function is testMaskComposition(){
		local Int is flags: 0b0000_0100 | 0b0000_0011;
		local Int is cleared: flags & ~(0b0000_0011);
		Assert:areEqualInt(7, flags);
		Assert:areEqualInt(4, cleared);
	}

	Function is testConcatenation(){
		local Int is masked: 5 & 3;
		local String is msg: 'mask=' . masked;
		Assert:areEqualString('mask=1', msg);
	}
}
