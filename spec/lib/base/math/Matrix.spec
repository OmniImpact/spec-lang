#! Package base:math
#! Contiguous row-major unboxed Float matrix accelerated by portable 4-wide LLVM SIMD with scalar fallback.

Class is Matrix{
	replace [String] is namespace: ['base', 'math'];

	merge [[String]] is using: [
		['base', 'math', as Math()],
		['base', 'math', Vector],
		['base', 'struct', Array],
		['base', 'sys', [as Cpu(), as Mem(), as Simd()]]
	];

	local Int is rowsCount: 0;
	local Int is colsCount: 0;
	local Int is data: 0;
	local Int is len: 0;

	replace Function is init(Int is rows: 0, Int is cols: 0, Float is initial: 0.0){
		local Int is r: if({ rows < 0 }, { 0 }, { rows });
		local Int is c: if({ cols < 0 }, { 0 }, { cols });
		:rowsCount: r;
		:colsCount: c;
		:len: r * c;
		if({ :len > 0 }, {
			:data: alloc(bytes: :len * 8);
			:fill(value: initial);
		});
	}

	Function is destroy(){
		if({ :data != 0 }, {
			free(ptr: :data);
			:data: 0;
			:len: 0;
			:rowsCount: 0;
			:colsCount: 0;
		});
	}

	## Creates a [rows] x [cols] zero-initialized matrix.
	held Function of Matrix is zeros(Int is rows, Int is cols){
		return Matrix(rows: rows, cols: cols, initial: 0.0);
	}

	## Sets this matrix to the identity matrix (1.0 on main diagonal, 0.0 elsewhere).
	Function is setIdentity(){
		:fill(value: 0.0);
		local Int is n: if({ :rowsCount < :colsCount }, { :rowsCount }, { :colsCount });
		local Int is i: 0;
		while({ i < n }, {
			:set(row: i, col: i, value: 1.0);
			i: i + 1;
		});
	}

	## Populates this matrix row-major from [values].
	Function is setFromArray(Array of Float is values){
		local Int is n: :len;
		if({ values:length() < n }, { n: values:length(); });
		local Int is i: 0;
		while({ i < n }, {
			storeF64(ptr: :data, byteOffset: i * 8, val: values:get(index: i, default: 0.0));
			i: i + 1;
		});
	}

	## Creates a [size] x [size] identity matrix.
	held Function of Matrix is identity(Int is size){
		local Matrix is m: Matrix(rows: size, cols: size, initial: 0.0);
		m:setIdentity();
		return m;
	}

	## Creates a [rows] x [cols] matrix populated row-major from [values].
	held Function of Matrix is fromArray(Int is rows, Int is cols, Array of Float is values){
		local Matrix is m: Matrix(rows: rows, cols: cols, initial: 0.0);
		m:setFromArray(values: values);
		return m;
	}

	Function of Int is rows(){ :rowsCount }

	Function of Int is cols(){ :colsCount }

	Function of Int is length(){ :len }

	Function of Int is dataAddr(){ :data }

	Function of Float is get(Int is row, Int is col, Float is default: 0.0){
		if({ row < 0 || row >= :rowsCount || col < 0 || col >= :colsCount || :data == 0 }, {
			return default;
		});
		return loadF64(ptr: :data, byteOffset: (row * :colsCount + col) * 8);
	}

	Function is set(Int is row, Int is col, Float is value){
		if({ row < 0 || row >= :rowsCount || col < 0 || col >= :colsCount || :data == 0 }, {
			return;
		});
		storeF64(ptr: :data, byteOffset: (row * :colsCount + col) * 8, val: value);
	}

	## Returns an independent copy of this matrix.
	Function of Matrix is copy(){
		local Matrix is out: Matrix(rows: :rowsCount, cols: :colsCount);
		if({ :len > 0 && :data != 0 && out:dataAddr() != 0 }, {
			:scale(factor: 1.0, out: out);
		});
		return out;
	}

	## Fills all elements with [value] using 4-wide SIMD when available.
	Function is fill(Float is value){
		if({ :len <= 0 || :data == 0 }, { return; });
		local Int is i: 0;
		if({ hasSimd() }, {
			while({ i + 4 <= :len }, {
				fill4(dst: :data + i * 8, val: value);
				i: i + 4;
			});
		});
		while({ i < :len }, {
			storeF64(ptr: :data, byteOffset: i * 8, val: value);
			i: i + 1;
		});
	}

	local Function of Int is minLen3(Matrix is other, Matrix is out){
		local Int is n: :len;
		if({ other:length() < n }, { n: other:length(); });
		if({ out:length() < n }, { n: out:length(); });
		return n;
	}

	local Function of Int is minLen2(Matrix is out){
		local Int is n: :len;
		if({ out:length() < n }, { n: out:length(); });
		return n;
	}

	## Computes `out = this + other` elementwise.
	Function is add(Matrix is other, Matrix is out){
		local Int is n: :minLen3(other: other, out: out);
		local Int is aPtr: :data;
		local Int is bPtr: other:dataAddr();
		local Int is dPtr: out:dataAddr();
		if({ n <= 0 || aPtr == 0 || bPtr == 0 || dPtr == 0 }, { return; });
		local Int is i: 0;
		if({ hasSimd() }, {
			while({ i + 4 <= n }, {
				local Int is off: i * 8;
				add4(dst: dPtr + off, a: aPtr + off, b: bPtr + off);
				i: i + 4;
			});
		});
		while({ i < n }, {
			local Int is off2: i * 8;
			storeF64(ptr: dPtr, byteOffset: off2, val: loadF64(ptr: aPtr, byteOffset: off2) + loadF64(ptr: bPtr, byteOffset: off2));
			i: i + 1;
		});
	}

	## Computes `out = this - other` elementwise.
	Function is sub(Matrix is other, Matrix is out){
		local Int is n: :minLen3(other: other, out: out);
		local Int is aPtr: :data;
		local Int is bPtr: other:dataAddr();
		local Int is dPtr: out:dataAddr();
		if({ n <= 0 || aPtr == 0 || bPtr == 0 || dPtr == 0 }, { return; });
		local Int is i: 0;
		if({ hasSimd() }, {
			while({ i + 4 <= n }, {
				local Int is off: i * 8;
				sub4(dst: dPtr + off, a: aPtr + off, b: bPtr + off);
				i: i + 4;
			});
		});
		while({ i < n }, {
			local Int is off2: i * 8;
			storeF64(ptr: dPtr, byteOffset: off2, val: loadF64(ptr: aPtr, byteOffset: off2) - loadF64(ptr: bPtr, byteOffset: off2));
			i: i + 1;
		});
	}

	## Computes `out = this * other` elementwise (Hadamard product).
	Function is hadamardMul(Matrix is other, Matrix is out){
		local Int is n: :minLen3(other: other, out: out);
		local Int is aPtr: :data;
		local Int is bPtr: other:dataAddr();
		local Int is dPtr: out:dataAddr();
		if({ n <= 0 || aPtr == 0 || bPtr == 0 || dPtr == 0 }, { return; });
		local Int is i: 0;
		if({ hasSimd() }, {
			while({ i + 4 <= n }, {
				local Int is off: i * 8;
				mul4(dst: dPtr + off, a: aPtr + off, b: bPtr + off);
				i: i + 4;
			});
		});
		while({ i < n }, {
			local Int is off2: i * 8;
			storeF64(ptr: dPtr, byteOffset: off2, val: loadF64(ptr: aPtr, byteOffset: off2) * loadF64(ptr: bPtr, byteOffset: off2));
			i: i + 1;
		});
	}

	## Computes `out = this * factor` elementwise.
	Function is scale(Float is factor, Matrix is out){
		local Int is n: :minLen2(out: out);
		local Int is aPtr: :data;
		local Int is dPtr: out:dataAddr();
		if({ n <= 0 || aPtr == 0 || dPtr == 0 }, { return; });
		local Int is i: 0;
		if({ hasSimd() }, {
			while({ i + 4 <= n }, {
				local Int is off: i * 8;
				scale4(dst: dPtr + off, a: aPtr + off, scalar: factor);
				i: i + 4;
			});
		});
		while({ i < n }, {
			local Int is off2: i * 8;
			storeF64(ptr: dPtr, byteOffset: off2, val: loadF64(ptr: aPtr, byteOffset: off2) * factor);
			i: i + 1;
		});
	}

	## Computes `out = this * b + c` elementwise.
	Function is fma(Matrix is b, Matrix is c, Matrix is out){
		local Int is n: :minLen3(other: b, out: out);
		if({ c:length() < n }, { n: c:length(); });
		local Int is aPtr: :data;
		local Int is bPtr: b:dataAddr();
		local Int is cPtr: c:dataAddr();
		local Int is dPtr: out:dataAddr();
		if({ n <= 0 || aPtr == 0 || bPtr == 0 || cPtr == 0 || dPtr == 0 }, { return; });
		local Int is i: 0;
		if({ hasSimd() }, {
			while({ i + 4 <= n }, {
				local Int is off: i * 8;
				fma4(dst: dPtr + off, a: aPtr + off, b: bPtr + off, c: cPtr + off);
				i: i + 4;
			});
		});
		while({ i < n }, {
			local Int is off2: i * 8;
			storeF64(ptr: dPtr, byteOffset: off2, val: loadF64(ptr: aPtr, byteOffset: off2) * loadF64(ptr: bPtr, byteOffset: off2) + loadF64(ptr: cPtr, byteOffset: off2));
			i: i + 1;
		});
	}

	## Clamps all elements to `[lo, hi]` into [out].
	Function is clamp(Float is lo, Float is hi, Matrix is out){
		local Int is n: :minLen2(out: out);
		local Int is aPtr: :data;
		local Int is dPtr: out:dataAddr();
		if({ n <= 0 || aPtr == 0 || dPtr == 0 }, { return; });
		local Int is i: 0;
		if({ hasSimd() }, {
			while({ i + 4 <= n }, {
				local Int is off: i * 8;
				clamp4(dst: dPtr + off, a: aPtr + off, lo: lo, hi: hi);
				i: i + 4;
			});
		});
		while({ i < n }, {
			local Int is off2: i * 8;
			local Float is v: loadF64(ptr: aPtr, byteOffset: off2);
			if({ v < lo }, { v: lo; });
			if({ v > hi }, { v: hi; });
			storeF64(ptr: dPtr, byteOffset: off2, val: v);
			i: i + 1;
		});
	}

	## Computes `out[i] = sqrt(this[i])` elementwise using hardware SIMD `sqrt`.
	Function is sqrt(Matrix is out){
		local Int is n: :minLen2(out: out);
		local Int is aPtr: :data;
		local Int is dPtr: out:dataAddr();
		if({ n <= 0 || aPtr == 0 || dPtr == 0 }, { return; });
		local Int is i: 0;
		if({ hasSimd() }, {
			while({ i + 4 <= n }, {
				local Int is off: i * 8;
				sqrt4(dst: dPtr + off, a: aPtr + off);
				i: i + 4;
			});
		});
		while({ i < n }, {
			local Int is off2: i * 8;
			storeF64(ptr: dPtr, byteOffset: off2, val: Math:sqrt(value: loadF64(ptr: aPtr, byteOffset: off2)));
			i: i + 1;
		});
	}

	## Computes `out[i] = abs(this[i])` elementwise using hardware SIMD `fabs`.
	Function is abs(Matrix is out){
		local Int is n: :minLen2(out: out);
		local Int is aPtr: :data;
		local Int is dPtr: out:dataAddr();
		if({ n <= 0 || aPtr == 0 || dPtr == 0 }, { return; });
		local Int is i: 0;
		if({ hasSimd() }, {
			while({ i + 4 <= n }, {
				local Int is off: i * 8;
				abs4(dst: dPtr + off, a: aPtr + off);
				i: i + 4;
			});
		});
		while({ i < n }, {
			local Int is off2: i * 8;
			local Float is v: loadF64(ptr: aPtr, byteOffset: off2);
			if({ v < 0.0 }, { v: 0.0 - v; });
			storeF64(ptr: dPtr, byteOffset: off2, val: v);
			i: i + 1;
		});
	}

	## Computes `out[i] = min(this[i], other[i])` elementwise.
	Function is minElem(Matrix is other, Matrix is out){
		local Int is n: :minLen3(other: other, out: out);
		local Int is aPtr: :data;
		local Int is bPtr: other:dataAddr();
		local Int is dPtr: out:dataAddr();
		if({ n <= 0 || aPtr == 0 || bPtr == 0 || dPtr == 0 }, { return; });
		local Int is i: 0;
		if({ hasSimd() }, {
			while({ i + 4 <= n }, {
				local Int is off: i * 8;
				min4(dst: dPtr + off, a: aPtr + off, b: bPtr + off);
				i: i + 4;
			});
		});
		while({ i < n }, {
			local Int is off2: i * 8;
			local Float is va: loadF64(ptr: aPtr, byteOffset: off2);
			local Float is vb: loadF64(ptr: bPtr, byteOffset: off2);
			storeF64(ptr: dPtr, byteOffset: off2, val: if({ va < vb }, { va }, { vb }));
			i: i + 1;
		});
	}

	## Computes `out[i] = max(this[i], other[i])` elementwise.
	Function is maxElem(Matrix is other, Matrix is out){
		local Int is n: :minLen3(other: other, out: out);
		local Int is aPtr: :data;
		local Int is bPtr: other:dataAddr();
		local Int is dPtr: out:dataAddr();
		if({ n <= 0 || aPtr == 0 || bPtr == 0 || dPtr == 0 }, { return; });
		local Int is i: 0;
		if({ hasSimd() }, {
			while({ i + 4 <= n }, {
				local Int is off: i * 8;
				max4(dst: dPtr + off, a: aPtr + off, b: bPtr + off);
				i: i + 4;
			});
		});
		while({ i < n }, {
			local Int is off2: i * 8;
			local Float is va: loadF64(ptr: aPtr, byteOffset: off2);
			local Float is vb: loadF64(ptr: bPtr, byteOffset: off2);
			storeF64(ptr: dPtr, byteOffset: off2, val: if({ va > vb }, { va }, { vb }));
			i: i + 1;
		});
	}

	## Returns the sum of all elements using 4-wide SIMD horizontal sum.
	Function of Float is sum(){
		if({ :len <= 0 || :data == 0 }, { return 0.0; });
		local Float is acc: 0.0;
		local Int is i: 0;
		if({ hasSimd() }, {
			while({ i + 4 <= :len }, {
				acc: acc + sum4(a: :data + i * 8);
				i: i + 4;
			});
		});
		while({ i < :len }, {
			acc: acc + loadF64(ptr: :data, byteOffset: i * 8);
			i: i + 1;
		});
		return acc;
	}

	## Returns the sum of elements in row [row].
	Function of Float is rowSum(Int is row){
		if({ row < 0 || row >= :rowsCount || :data == 0 }, { return 0.0; });
		local Int is rowBase: :data + row * :colsCount * 8;
		local Float is acc: 0.0;
		local Int is j: 0;
		if({ hasSimd() }, {
			while({ j + 4 <= :colsCount }, {
				acc: acc + sum4(a: rowBase + j * 8);
				j: j + 4;
			});
		});
		while({ j < :colsCount }, {
			acc: acc + loadF64(ptr: rowBase, byteOffset: j * 8);
			j: j + 1;
		});
		return acc;
	}

	## Returns the sum of elements in column [col].
	Function of Float is colSum(Int is col){
		if({ col < 0 || col >= :colsCount || :data == 0 }, { return 0.0; });
		local Float is acc: 0.0;
		local Int is i: 0;
		while({ i < :rowsCount }, {
			acc: acc + loadF64(ptr: :data, byteOffset: (i * :colsCount + col) * 8);
			i: i + 1;
		});
		return acc;
	}

	## Returns the Frobenius inner product `sum(this[i] * other[i])`.
	Function of Float is dot(Matrix is other){
		local Int is n: :len;
		if({ other:length() < n }, { n: other:length(); });
		local Int is aPtr: :data;
		local Int is bPtr: other:dataAddr();
		if({ n <= 0 || aPtr == 0 || bPtr == 0 }, { return 0.0; });
		local Float is acc: 0.0;
		local Int is i: 0;
		if({ hasSimd() }, {
			while({ i + 4 <= n }, {
				local Int is off: i * 8;
				acc: acc + dot4(a: aPtr + off, b: bPtr + off);
				i: i + 4;
			});
		});
		while({ i < n }, {
			local Int is off2: i * 8;
			acc: acc + loadF64(ptr: aPtr, byteOffset: off2) * loadF64(ptr: bPtr, byteOffset: off2);
			i: i + 1;
		});
		return acc;
	}

	## Returns the Frobenius norm `sqrt(sum(a_ij^2))`.
	Function of Float is frobeniusNorm(){
		return Math:sqrt(value: :dot(other: :));
	}

	## Returns the trace (sum of main diagonal elements).
	Function of Float is trace(){
		local Int is n: if({ :rowsCount < :colsCount }, { :rowsCount }, { :colsCount });
		local Float is acc: 0.0;
		local Int is i: 0;
		while({ i < n }, {
			acc: acc + loadF64(ptr: :data, byteOffset: (i * :colsCount + i) * 8);
			i: i + 1;
		});
		return acc;
	}

	## Computes matrix-vector product `out = this * vec` using 4-wide SIMD `dot4`.
	Function is mulVec(Vector is vec, Vector is out){
		local Int is r: :rowsCount;
		local Int is c: :colsCount;
		if({ vec:length() < c }, { c: vec:length(); });
		if({ out:length() < r }, { r: out:length(); });
		local Int is aPtr: :data;
		local Int is vPtr: vec:dataAddr();
		local Int is oPtr: out:dataAddr();
		if({ r <= 0 || c <= 0 || aPtr == 0 || vPtr == 0 || oPtr == 0 }, { return; });
		local Boolean is simdOn: hasSimd();
		local Int is i: 0;
		while({ i < r }, {
			local Int is rowBase: aPtr + i * :colsCount * 8;
			local Float is acc: 0.0;
			local Int is j: 0;
			if({ simdOn }, {
				while({ j + 4 <= c }, {
					local Int is off: j * 8;
					acc: acc + dot4(a: rowBase + off, b: vPtr + off);
					j: j + 4;
				});
			});
			while({ j < c }, {
				local Int is off2: j * 8;
				acc: acc + loadF64(ptr: rowBase, byteOffset: off2) * loadF64(ptr: vPtr, byteOffset: off2);
				j: j + 1;
			});
			storeF64(ptr: oPtr, byteOffset: i * 8, val: acc);
			i: i + 1;
		});
	}

	## Computes `out = this * other` using cache-blocked `ikj` + SIMD `axpy4`.
	Function is mul(Matrix is other, Matrix is out){
		local Int is m: :rowsCount;
		local Int is kDim: :colsCount;
		local Int is n: other:cols();
		if({ other:rows() != kDim || out:rows() != m || out:cols() != n }, { return; });
		local Int is aPtr: :data;
		local Int is bPtr: other:dataAddr();
		local Int is cPtr: out:dataAddr();
		if({ m <= 0 || kDim <= 0 || n <= 0 || aPtr == 0 || bPtr == 0 || cPtr == 0 }, { return; });
		out:fill(value: 0.0);
		local Boolean is simdOn: hasSimd();
		local Int is tile: 32;
		local Int is ii: 0;
		while({ ii < m }, {
			local Int is iEnd: ii + tile;
			if({ iEnd > m }, { iEnd: m; });
			local Int is kk: 0;
			while({ kk < kDim }, {
				local Int is kEnd: kk + tile;
				if({ kEnd > kDim }, { kEnd: kDim; });
				local Int is jj: 0;
				while({ jj < n }, {
					local Int is jEnd: jj + tile;
					if({ jEnd > n }, { jEnd: n; });
					local Int is i: ii;
					while({ i < iEnd }, {
						local Int is aRowOff: i * kDim;
						local Int is cRowPtr: cPtr + i * n * 8;
						local Int is k: kk;
						while({ k < kEnd }, {
							local Float is aik: loadF64(ptr: aPtr, byteOffset: (aRowOff + k) * 8);
							if({ aik != 0.0 }, {
								local Int is bRowPtr: bPtr + k * n * 8;
								local Int is j: jj;
								if({ simdOn }, {
									while({ j + 4 <= jEnd }, {
										local Int is jOff: j * 8;
										axpy4(dst: cRowPtr + jOff, a: bRowPtr + jOff, scalar: aik, c: cRowPtr + jOff);
										j: j + 4;
									});
								});
								while({ j < jEnd }, {
									local Int is jOff2: j * 8;
									storeF64(ptr: cRowPtr, byteOffset: jOff2, val: loadF64(ptr: cRowPtr, byteOffset: jOff2) + aik * loadF64(ptr: bRowPtr, byteOffset: jOff2));
									j: j + 1;
								});
							});
							k: k + 1;
						});
						i: i + 1;
					});
					jj: jj + tile;
				});
				kk: kk + tile;
			});
			ii: ii + tile;
		});
	}

	## Computes cache-blocked `out = transpose(this)`.
	Function is transpose(Matrix is out){
		if({ out:rows() != :colsCount || out:cols() != :rowsCount }, { return; });
		local Int is aPtr: :data;
		local Int is dPtr: out:dataAddr();
		if({ :rowsCount <= 0 || :colsCount <= 0 || aPtr == 0 || dPtr == 0 }, { return; });
		local Int is tile: 16;
		local Int is ii: 0;
		while({ ii < :rowsCount }, {
			local Int is iEnd: ii + tile;
			if({ iEnd > :rowsCount }, { iEnd: :rowsCount; });
			local Int is jj: 0;
			while({ jj < :colsCount }, {
				local Int is jEnd: jj + tile;
				if({ jEnd > :colsCount }, { jEnd: :colsCount; });
				local Int is i: ii;
				while({ i < iEnd }, {
					local Int is j: jj;
					while({ j < jEnd }, {
						local Float is v: loadF64(ptr: aPtr, byteOffset: (i * :colsCount + j) * 8);
						storeF64(ptr: dPtr, byteOffset: (j * :rowsCount + i) * 8, val: v);
						j: j + 1;
					});
					i: i + 1;
				});
				jj: jj + tile;
			});
			ii: ii + tile;
		});
	}

	## Returns `true` if dimensions match and every element differs by at most [tol].
	Function of Boolean is equals(Matrix is other, Float is tol: 0.000000001){
		if({ :rowsCount != other:rows() || :colsCount != other:cols() }, { return false; });
		local Int is i: 0;
		local Int is bPtr: other:dataAddr();
		while({ i < :len }, {
			local Int is off: i * 8;
			local Float is diff: loadF64(ptr: :data, byteOffset: off) - loadF64(ptr: bPtr, byteOffset: off);
			if({ diff < 0.0 }, { diff: 0.0 - diff; });
			if({ diff > tol }, { return false; });
			i: i + 1;
		});
		return true;
	}
}
