#! SpecUnit sweep (from overloads_test.spec): signature overloads —
#! arity-distinct and type-distinct overloads resolve, init overloads
#! construct, and bare calls reach the unique provider.

Class of SpecUnitTest is TestOverloads{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		# IV.6 strictness: the plain form grants construction; the as-form
		# grants the bare function calls (twice).
		['ovl', 'lib', Over],
		['ovl', 'lib', as Over()]
	];

	Function is testTwiceIntOverload(){
		local Int is i1: Over:twice(21);
		Assert:areEqualInt(42, i1);
	}

	Function is testTwiceStringOverload(){
		local String is s1: Over:twice('ab');
		Assert:areEqualString('abab', s1);
	}

	Function is testSumArityOverloads(){
		local Int is s2: Over:sum(5);
		local Int is s3: Over:sum(2, 3);
		Assert:areEqualInt(5, s2);
		Assert:areEqualInt(5, s3);
	}

	Function is testInitOverloads(){
		local Over is a: Over:init();
		local Over is b: Over:init(start: 9);
		Assert:areEqualInt(0, a:seedValue());
		Assert:areEqualInt(9, b:seedValue());
	}

	Function is testBareUniqueProvider(){
		# The bare call reaches the unique provider through the as-form.
		local Int is b1: twice(4);
		Assert:areEqualInt(8, b1);
	}
}
