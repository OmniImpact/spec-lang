#! Package base:mold
#! 4x4 column-major matrix for 3D transforms and Vulkan push constants.
#! Backed by a contiguous 16-f64 buffer with 4-wide SIMD column multiplication.

Class is Mat4{
	replace [String] is namespace: ['base', 'mold'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Cpu()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Simd()],
		['base', 'sys', Vulkan],
		['base', 'math', Math]
	];

	local Int is data: 0;

	## Initializes a 4x4 identity matrix.
	replace Function is init(){
		:data: Mem:alloc(bytes: 128);
		if({ Cpu:hasSimd() }, {
			Simd:fill4(dst: :data, val: 0.0);
			Simd:fill4(dst: :data + 32, val: 0.0);
			Simd:fill4(dst: :data + 64, val: 0.0);
			Simd:fill4(dst: :data + 96, val: 0.0);
		}, {
			local Int is i: 0;
			while({ i < 16 }, {
				Mem:storeF64(ptr: :data, byteOffset: i * 8, val: 0.0);
				i: i + 1;
			});
		});
		Mem:storeF64(ptr: :data, byteOffset: 0, val: 1.0);
		Mem:storeF64(ptr: :data, byteOffset: 40, val: 1.0);
		Mem:storeF64(ptr: :data, byteOffset: 80, val: 1.0);
		Mem:storeF64(ptr: :data, byteOffset: 120, val: 1.0);
	}

	Function is destroy(){
		if({ :data != 0 }, {
			Mem:free(ptr: :data);
			:data: 0;
		});
	}

	## Returns the raw pointer to the 16-element column-major f64 buffer.
	Function of Int is dataAddr(){ :data }

	## Returns element at ([col], [row]).
	Function of Float is get(Int is col, Int is row){
		if({ :data == 0 || col < 0 || col >= 4 || row < 0 || row >= 4 }, { return 0.0; });
		return Mem:loadF64(ptr: :data, byteOffset: (col * 4 + row) * 8);
	}

	## Sets element at ([col], [row]) to [val].
	Function is set(Int is col, Int is row, Float is val){
		if({ :data == 0 || col < 0 || col >= 4 || row < 0 || row >= 4 }, { return; });
		Mem:storeF64(ptr: :data, byteOffset: (col * 4 + row) * 8, val: val);
	}

	## Returns a fresh 4x4 identity matrix.
	Function of Mat4 is identity(){
		return Mat4();
	}

	## Multiplies `this * other` into [out] using 4-wide SIMD column `axpy4`
	## (safe even if [out] aliases `this` or [other]).
	Function is mulInto(Mat4 is other, Mat4 is out){
		local Int is aPtr: :data;
		local Int is bPtr: other:dataAddr();
		local Int is oPtr: out:dataAddr();
		if({ aPtr == 0 || bPtr == 0 || oPtr == 0 }, { return; });
		local Boolean is aliased: oPtr == aPtr || oPtr == bPtr;
		local Int is dstPtr: if({ aliased }, { Mem:alloc(bytes: 128) }, { oPtr });
		if({ Cpu:hasSimd() }, {
			local Int is col: 0;
			while({ col < 4 }, {
				local Int is bColOff: col * 32;
				local Int is dCol: dstPtr + bColOff;
				local Float is b0: Mem:loadF64(ptr: bPtr, byteOffset: bColOff);
				local Float is b1: Mem:loadF64(ptr: bPtr, byteOffset: bColOff + 8);
				local Float is b2: Mem:loadF64(ptr: bPtr, byteOffset: bColOff + 16);
				local Float is b3: Mem:loadF64(ptr: bPtr, byteOffset: bColOff + 24);
				Simd:scale4(dst: dCol, a: aPtr, scalar: b0);
				Simd:axpy4(dst: dCol, a: aPtr + 32, scalar: b1, c: dCol);
				Simd:axpy4(dst: dCol, a: aPtr + 64, scalar: b2, c: dCol);
				Simd:axpy4(dst: dCol, a: aPtr + 96, scalar: b3, c: dCol);
				col: col + 1;
			});
		}, {
			local Int is col2: 0;
			while({ col2 < 4 }, {
				local Int is row: 0;
				while({ row < 4 }, {
					local Float is sum: 0.0;
					local Int is k: 0;
					while({ k < 4 }, {
						sum: sum + Mem:loadF64(ptr: aPtr, byteOffset: (k * 4 + row) * 8) * Mem:loadF64(ptr: bPtr, byteOffset: (col2 * 4 + k) * 8);
						k: k + 1;
					});
					Mem:storeF64(ptr: dstPtr, byteOffset: (col2 * 4 + row) * 8, val: sum);
					row: row + 1;
				});
				col2: col2 + 1;
			});
		});
		if({ aliased }, {
			Mem:copy(dst: oPtr, src: dstPtr, bytes: 128);
			Mem:free(ptr: dstPtr);
		});
	}

	## Multiplies `this * other` and returns the resulting `Mat4`.
	Function of Mat4 is mul(Mat4 is other){
		local Mat4 is out: Mat4();
		:mulInto(other: other, out: out);
		return out;
	}

	## Returns a translation matrix for ([tx], [ty], [tz]).
	Function of Mat4 is translate(Float is tx, Float is ty, Float is tz){
		local Mat4 is out: Mat4();
		out:set(col: 3, row: 0, val: tx);
		out:set(col: 3, row: 1, val: ty);
		out:set(col: 3, row: 2, val: tz);
		return out;
	}

	held Math is sharedMath: Math();
	held Vulkan is sharedVulkan: Vulkan();

	## Returns a rotation matrix around the X axis by [rad] radians.
	Function of Mat4 is rotateX(Float is rad){
		local Mat4 is out: Mat4();
		local Float is c: Mat4:sharedMath:cos(value: rad);
		local Float is s: Mat4:sharedMath:sin(value: rad);
		out:set(col: 1, row: 1, val: c);
		out:set(col: 1, row: 2, val: s);
		out:set(col: 2, row: 1, val: 0.0 - s);
		out:set(col: 2, row: 2, val: c);
		return out;
	}

	## Returns a rotation matrix around the Y axis by [rad] radians.
	Function of Mat4 is rotateY(Float is rad){
		local Mat4 is out: Mat4();
		local Float is c: Mat4:sharedMath:cos(value: rad);
		local Float is s: Mat4:sharedMath:sin(value: rad);
		out:set(col: 0, row: 0, val: c);
		out:set(col: 0, row: 2, val: 0.0 - s);
		out:set(col: 2, row: 0, val: s);
		out:set(col: 2, row: 2, val: c);
		return out;
	}

	## Returns a rotation matrix around the Z axis by [rad] radians.
	Function of Mat4 is rotateZ(Float is rad){
		local Mat4 is out: Mat4();
		local Float is c: Mat4:sharedMath:cos(value: rad);
		local Float is s: Mat4:sharedMath:sin(value: rad);
		out:set(col: 0, row: 0, val: c);
		out:set(col: 0, row: 1, val: s);
		out:set(col: 1, row: 0, val: 0.0 - s);
		out:set(col: 1, row: 1, val: c);
		return out;
	}

	## Returns a Vulkan-clip-space ([0, 1] depth, Y-flipped) perspective matrix.
	Function of Mat4 is perspective(Float is fovRad, Float is aspect, Float is nearZ, Float is farZ){
		local Mat4 is out: Mat4();
		local Float is f: 1.0 / Mat4:sharedMath:tan(value: fovRad * 0.5);
		out:set(col: 0, row: 0, val: f / aspect);
		out:set(col: 1, row: 1, val: 0.0 - f);
		out:set(col: 2, row: 2, val: farZ / (nearZ - farZ));
		out:set(col: 2, row: 3, val: -1.0);
		out:set(col: 3, row: 2, val: (nearZ * farZ) / (nearZ - farZ));
		out:set(col: 3, row: 3, val: 0.0);
		return out;
	}

	## Packs all 16 elements as 32-bit IEEE-754 floats (64 bytes) at [dstAddr].
	Function is packF32(Int is dstAddr){
		if({ :data == 0 }, { return; });
		local Int is i: 0;
		while({ i < 16 }, {
			Mat4:sharedVulkan:packF32(dstAddr: dstAddr, byteOffset: i * 4, val: Mem:loadF64(ptr: :data, byteOffset: i * 8));
			i: i + 1;
		});
	}
}
