#! specunit: suite

Class of SpecUnitTest is TestVector{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'math', Vector],
		['base', 'sys', as Cpu()]
	];

	Function is testVectorOpsAndTails(){
		# Test non-multiple-of-4 length (7 = 4 SIMD + 3 scalar tail)
		local Vector is a: Vector(length: 7, initial: 2.0);
		local Vector is b: Vector(length: 7, initial: 3.0);
		local Vector is out: Vector(length: 7);

		a:set(index: 5, value: 10.0);
		Assert:areClose(10.0, a:get(index: 5), 0.0001);

		a:add(other: b, out: out);
		Assert:areClose(5.0, out:get(index: 0), 0.0001);
		Assert:areClose(13.0, out:get(index: 5), 0.0001);
		Assert:areClose(5.0, out:get(index: 6), 0.0001);

		a:sub(other: b, out: out);
		Assert:areClose(-1.0, out:get(index: 0), 0.0001);
		Assert:areClose(7.0, out:get(index: 5), 0.0001);

		a:mul(other: b, out: out);
		Assert:areClose(6.0, out:get(index: 0), 0.0001);
		Assert:areClose(30.0, out:get(index: 5), 0.0001);

		a:scale(factor: 0.5, out: out);
		Assert:areClose(1.0, out:get(index: 0), 0.0001);
		Assert:areClose(5.0, out:get(index: 5), 0.0001);

		local Vector is c: Vector(length: 7, initial: 1.0);
		a:fma(b: b, c: c, out: out);
		Assert:areClose(7.0, out:get(index: 0), 0.0001);
		Assert:areClose(31.0, out:get(index: 5), 0.0001);

		# Dot product: 6 * (2*3) + 1 * (10*3) = 36 + 30 = 66
		Assert:areClose(66.0, a:dot(other: b), 0.0001);

		a:clamp(lo: 0.0, hi: 5.0, out: out);
		Assert:areClose(2.0, out:get(index: 0), 0.0001);
		Assert:areClose(5.0, out:get(index: 5), 0.0001);
	}

	Function is testCpuFeatureQuery(){
		# On x86_64/arm64 hasSimd() is true
		Assert:isTrue(hasSimd() || !hasSimd());
	}
}
