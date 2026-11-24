#! Package base:math
#! Contiguous unboxed Float vector accelerated by portable 4-wide LLVM SIMD with scalar fallback.

Class is Vector{
	replace [String] is namespace: ['base', 'math'];

	merge [[String]] is using: [
		['base', 'sys', [as Cpu(), as Mem(), as Simd()]]
	];

	local Int is data: 0;
	local Int is len: 0;

	replace Function is init(Int is length: 0, Float is initial: 0.0){
		local Int is n: if({ length < 0 }, { 0 }, { length });
		len: n;
		if({ n > 0 }, {
			data: alloc(bytes: n * 8);
			fill(value: initial);
		});
	}

	Function is destroy(){
		if({ data != 0 }, {
			free(ptr: data);
			data: 0;
			len: 0;
		});
	}

	Function of Int is length(){ len }

	Function of Int is dataAddr(){ data }

	Function of Float is get(Int is index){
		if({ index < 0 || index >= len || data == 0 }, { return 0.0; });
		return loadF64(ptr: data, byteOffset: index * 8);
	}

	Function is set(Int is index, Float is value){
		if({ index < 0 || index >= len || data == 0 }, { return; });
		storeF64(ptr: data, byteOffset: index * 8, val: value);
	}

	## Fills all elements with [value] using 4-wide SIMD when available.
	Function is fill(Float is value){
		if({ len <= 0 || data == 0 }, { return; });
		local Int is i: 0;
		if({ hasSimd() }, {
			while({ i + 4 <= len }, {
				fill4(dst: data + i * 8, val: value);
				i: i + 4;
			});
		});
		while({ i < len }, {
			storeF64(ptr: data, byteOffset: i * 8, val: value);
			i: i + 1;
		});
	}

	## Computes `out[i] = this[i] + other[i]`.
	Function is add(Vector is other, Vector is out){
		local Int is n: len;
		if({ other:length() < n }, { n: other:length(); });
		if({ out:length() < n }, { n: out:length(); });
		local Int is aPtr: data;
		local Int is bPtr: other:dataAddr();
		local Int is dPtr: out:dataAddr();
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

	## Computes `out[i] = this[i] - other[i]`.
	Function is sub(Vector is other, Vector is out){
		local Int is n: len;
		if({ other:length() < n }, { n: other:length(); });
		if({ out:length() < n }, { n: out:length(); });
		local Int is aPtr: data;
		local Int is bPtr: other:dataAddr();
		local Int is dPtr: out:dataAddr();
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

	## Computes `out[i] = this[i] * other[i]`.
	Function is mul(Vector is other, Vector is out){
		local Int is n: len;
		if({ other:length() < n }, { n: other:length(); });
		if({ out:length() < n }, { n: out:length(); });
		local Int is aPtr: data;
		local Int is bPtr: other:dataAddr();
		local Int is dPtr: out:dataAddr();
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

	## Computes `out[i] = this[i] * factor`.
	Function is scale(Float is factor, Vector is out){
		local Int is n: len;
		if({ out:length() < n }, { n: out:length(); });
		local Int is aPtr: data;
		local Int is dPtr: out:dataAddr();
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

	## Computes `out[i] = this[i] * b[i] + c[i]`.
	Function is fma(Vector is b, Vector is c, Vector is out){
		local Int is n: len;
		if({ b:length() < n }, { n: b:length(); });
		if({ c:length() < n }, { n: c:length(); });
		if({ out:length() < n }, { n: out:length(); });
		local Int is aPtr: data;
		local Int is bPtr: b:dataAddr();
		local Int is cPtr: c:dataAddr();
		local Int is dPtr: out:dataAddr();
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

	## Computes the dot product `sum(this[i] * other[i])`.
	Function of Float is dot(Vector is other){
		local Int is n: len;
		if({ other:length() < n }, { n: other:length(); });
		local Int is aPtr: data;
		local Int is bPtr: other:dataAddr();
		local Float is sum: 0.0;
		local Int is i: 0;
		if({ hasSimd() }, {
			while({ i + 4 <= n }, {
				local Int is off: i * 8;
				sum: sum + dot4(a: aPtr + off, b: bPtr + off);
				i: i + 4;
			});
		});
		while({ i < n }, {
			local Int is off2: i * 8;
			sum: sum + loadF64(ptr: aPtr, byteOffset: off2) * loadF64(ptr: bPtr, byteOffset: off2);
			i: i + 1;
		});
		return sum;
	}

	## Clamps all elements to `[lo, hi]` into [out].
	Function is clamp(Float is lo, Float is hi, Vector is out){
		local Int is n: len;
		if({ out:length() < n }, { n: out:length(); });
		local Int is aPtr: data;
		local Int is dPtr: out:dataAddr();
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
}
