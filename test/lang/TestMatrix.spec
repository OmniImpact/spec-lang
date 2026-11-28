#! specunit: suite

Class of SpecUnitTest is TestMatrix{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'math', Matrix],
		['base', 'math', Vector],
		['base', 'struct', Array]
	];

	Function is testElementwiseAndNewSimdIntrinsics(){
		# 3 x 5 = 15 elements (3 * 4 SIMD + 3 scalar tail)
		local Matrix is a: Matrix(rows: 3, cols: 5, initial: 4.0);
		local Matrix is b: Matrix(rows: 3, cols: 5, initial: 9.0);
		local Matrix is out: Matrix(rows: 3, cols: 5);

		a:set(row: 2, col: 4, value: -16.0);
		Assert:areClose(-16.0, a:get(row: 2, col: 4), 0.0001);

		a:abs(out: out);
		Assert:areClose(4.0, out:get(row: 0, col: 0), 0.0001);
		Assert:areClose(16.0, out:get(row: 2, col: 4), 0.0001);

		out:sqrt(out: out);
		Assert:areClose(2.0, out:get(row: 0, col: 0), 0.0001);
		Assert:areClose(4.0, out:get(row: 2, col: 4), 0.0001);

		a:minElem(other: b, out: out);
		Assert:areClose(4.0, out:get(row: 0, col: 0), 0.0001);
		Assert:areClose(-16.0, out:get(row: 2, col: 4), 0.0001);

		a:maxElem(other: b, out: out);
		Assert:areClose(9.0, out:get(row: 0, col: 0), 0.0001);
		Assert:areClose(9.0, out:get(row: 2, col: 4), 0.0001);

		# sum() via sum4 + tail: 14 * 4.0 + (-16.0) = 40.0
		Assert:areClose(40.0, a:sum(), 0.0001);
		Assert:areClose(20.0, a:rowSum(row: 0), 0.0001);
		Assert:areClose(0.0, a:rowSum(row: 2), 0.0001);
		Assert:areClose(12.0, a:colSum(col: 0), 0.0001);
		Assert:areClose(-8.0, a:colSum(col: 4), 0.0001);

		a:add(other: b, out: out);
		Assert:areClose(13.0, out:get(row: 0, col: 0), 0.0001);
		Assert:areClose(-7.0, out:get(row: 2, col: 4), 0.0001);

		a:sub(other: b, out: out);
		Assert:areClose(-5.0, out:get(row: 0, col: 0), 0.0001);
		Assert:areClose(-25.0, out:get(row: 2, col: 4), 0.0001);

		a:hadamardMul(other: b, out: out);
		Assert:areClose(36.0, out:get(row: 0, col: 0), 0.0001);
		Assert:areClose(-144.0, out:get(row: 2, col: 4), 0.0001);

		a:scale(factor: 0.5, out: out);
		Assert:areClose(2.0, out:get(row: 0, col: 0), 0.0001);
		Assert:areClose(-8.0, out:get(row: 2, col: 4), 0.0001);
	}

	Function is testMulVecAndMatMulAndTranspose(){
		# A (2x5) * B (5x3) -> C (2x3)
		local Matrix is a: Matrix:fromArray(rows: 2, cols: 5, values: Array([
			1.0, 2.0, 3.0, 4.0, 5.0,
			6.0, 7.0, 8.0, 9.0, 10.0
		]));
		local Matrix is b: Matrix:fromArray(rows: 5, cols: 3, values: Array([
			1.0, 0.0, 2.0,
			0.0, 1.0, 1.0,
			1.0, 1.0, 0.0,
			2.0, 0.0, 1.0,
			0.0, 2.0, 1.0
		]));
		local Matrix is c: Matrix:zeros(rows: 2, cols: 3);
		a:mul(other: b, out: c);

		# Row 0: [1+3+8, 2+3+10, 2+2+4+5] = [12, 15, 13]
		Assert:areClose(12.0, c:get(row: 0, col: 0), 0.0001);
		Assert:areClose(15.0, c:get(row: 0, col: 1), 0.0001);
		Assert:areClose(13.0, c:get(row: 0, col: 2), 0.0001);
		# Row 1: [6+8+18, 7+8+20, 12+7+9+10] = [32, 35, 38]
		Assert:areClose(32.0, c:get(row: 1, col: 0), 0.0001);
		Assert:areClose(35.0, c:get(row: 1, col: 1), 0.0001);
		Assert:areClose(38.0, c:get(row: 1, col: 2), 0.0001);

		# Matrix * Vector
		local Vector is v: Vector(length: 5, initial: 1.0);
		local Vector is vOut: Vector(length: 2);
		a:mulVec(vec: v, out: vOut);
		Assert:areClose(15.0, vOut:get(index: 0), 0.0001);
		Assert:areClose(40.0, vOut:get(index: 1), 0.0001);

		# Transpose
		local Matrix is at: Matrix:zeros(rows: 5, cols: 2);
		a:transpose(out: at);
		Assert:areClose(1.0, at:get(row: 0, col: 0), 0.0001);
		Assert:areClose(6.0, at:get(row: 0, col: 1), 0.0001);
		Assert:areClose(5.0, at:get(row: 4, col: 0), 0.0001);
		Assert:areClose(10.0, at:get(row: 4, col: 1), 0.0001);
	}

	Function is testTiledMatMulAndIdentity(){
		# 37 x 37 (crosses 32x32 tile boundary and 4-wide SIMD + tail)
		local Int is n: 37;
		local Matrix is id: Matrix:identity(size: n);
		Assert:areClose(37.0, id:trace(), 0.0001);

		local Matrix is m: Matrix(rows: n, cols: n);
		local Int is i: 0;
		while({ i < n }, {
			local Int is j: 0;
			while({ j < n }, {
				m:set(row: i, col: j, value: ((i * 7 + j) % 11) as Float);
				j: j + 1;
			});
			i: i + 1;
		});
		local Matrix is out: Matrix(rows: n, cols: n);
		m:mul(other: id, out: out);
		Assert:isTrue(m:equals(other: out));
	}
}
