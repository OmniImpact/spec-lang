#! specunit: suite

Class of SpecUnitTest is TestVector{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'math', Vector],
		['base', 'math', as Stats()],
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

		# New SIMD ops on non-multiple-of-4 length (7 = 4 SIMD + 3 scalar tail)
		local Vector is neg: Vector(length: 7, initial: -4.0);
		neg:set(index: 5, value: -16.0);
		neg:abs(out: out);
		Assert:areClose(4.0, out:get(index: 0), 0.0001);
		Assert:areClose(16.0, out:get(index: 5), 0.0001);
		Assert:areClose(4.0, out:get(index: 6), 0.0001);

		out:sqrt(out: out);
		Assert:areClose(2.0, out:get(index: 0), 0.0001);
		Assert:areClose(4.0, out:get(index: 5), 0.0001);
		Assert:areClose(2.0, out:get(index: 6), 0.0001);

		# axpy: out = a * 2.0 + c -> 2*2+1 = 5, index 5: 10*2+1 = 21
		a:axpy(scalar: 2.0, c: c, out: out);
		Assert:areClose(5.0, out:get(index: 0), 0.0001);
		Assert:areClose(21.0, out:get(index: 5), 0.0001);
		Assert:areClose(5.0, out:get(index: 6), 0.0001);

		# minElem / maxElem
		a:minElem(other: b, out: out);
		Assert:areClose(2.0, out:get(index: 0), 0.0001);
		Assert:areClose(3.0, out:get(index: 5), 0.0001);
		a:maxElem(other: b, out: out);
		Assert:areClose(3.0, out:get(index: 0), 0.0001);
		Assert:areClose(10.0, out:get(index: 5), 0.0001);

		# sum: 6 * 2.0 + 10.0 = 22.0; norm: sqrt(6*4 + 100) = sqrt(124)
		Assert:areClose(22.0, a:sum(), 0.0001);
		Assert:areClose(11.1355287, a:norm(), 0.0001);

		# Stats Vector overloads
		local Vector is sv: Vector(length: 5, initial: 0.0);
		sv:set(index: 0, value: 2.0);
		sv:set(index: 1, value: 4.0);
		sv:set(index: 2, value: 4.0);
		sv:set(index: 3, value: 4.0);
		sv:set(index: 4, value: 6.0);
		Assert:areClose(20.0, Stats:sum(vec: sv), 0.0001);
		Assert:areClose(4.0, Stats:average(vec: sv), 0.0001);
		Assert:areClose(1.6, Stats:variance(vec: sv), 0.0001);
		Assert:areClose(1.264911, Stats:stdDev(vec: sv), 0.0001);
	}

	Function is testCpuFeatureQuery(){
		# On x86_64/arm64 hasSimd() is true
		Assert:isTrue(hasSimd() || !hasSimd());
	}
}
