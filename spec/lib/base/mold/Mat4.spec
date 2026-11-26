#! Package base:mold
#! 4x4 column-major matrix for 3D transforms and Vulkan push constants.

Class is Mat4{
	replace [String] is namespace: ['base', 'mold'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', Vulkan],
		['base', 'math', Math],
		['base', 'struct', Array]
	];

	Array of Float is m: Array();

	## Initializes a 4x4 identity matrix.
	replace Function is init(){
		m: Array();
		times(count: 16, worker: local Function(Int is i){
			m:add(item: 0.0);
		});
		m:set(index: 0, item: 1.0);
		m:set(index: 5, item: 1.0);
		m:set(index: 10, item: 1.0);
		m:set(index: 15, item: 1.0);
	}

	## Returns element at ([col], [row]).
	Function of Float is get(Int is col, Int is row){
		return m:get(index: col * 4 + row);
	}

	## Sets element at ([col], [row]) to [val].
	Function is set(Int is col, Int is row, Float is val){
		m:set(index: col * 4 + row, item: val);
	}

	## Returns a fresh 4x4 identity matrix.
	Function of Mat4 is identity(){
		return Mat4();
	}

	## Multiplies `this * other` and returns the resulting `Mat4`.
	Function of Mat4 is mul(Mat4 is other){
		local Mat4 is out: Mat4();
		times(count: 4, worker: local Function(Int is col){
			times(count: 4, worker: local Function(Int is row){
				local Float is sum: 0.0;
				times(count: 4, worker: local Function(Int is k){
					sum: sum + :get(col: k, row: row) * other:get(col: col, row: k);
				});
				out:set(col: col, row: row, val: sum);
			});
		});
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

	## Returns a rotation matrix around the X axis by [rad] radians.
	Function of Mat4 is rotateX(Float is rad){
		local Mat4 is out: Mat4();
		local Math is math: Math();
		local Float is c: math:cos(value: rad);
		local Float is s: math:sin(value: rad);
		out:set(col: 1, row: 1, val: c);
		out:set(col: 1, row: 2, val: s);
		out:set(col: 2, row: 1, val: 0.0 - s);
		out:set(col: 2, row: 2, val: c);
		return out;
	}

	## Returns a rotation matrix around the Y axis by [rad] radians.
	Function of Mat4 is rotateY(Float is rad){
		local Mat4 is out: Mat4();
		local Math is math: Math();
		local Float is c: math:cos(value: rad);
		local Float is s: math:sin(value: rad);
		out:set(col: 0, row: 0, val: c);
		out:set(col: 0, row: 2, val: 0.0 - s);
		out:set(col: 2, row: 0, val: s);
		out:set(col: 2, row: 2, val: c);
		return out;
	}

	## Returns a rotation matrix around the Z axis by [rad] radians.
	Function of Mat4 is rotateZ(Float is rad){
		local Mat4 is out: Mat4();
		local Math is math: Math();
		local Float is c: math:cos(value: rad);
		local Float is s: math:sin(value: rad);
		out:set(col: 0, row: 0, val: c);
		out:set(col: 0, row: 1, val: s);
		out:set(col: 1, row: 0, val: 0.0 - s);
		out:set(col: 1, row: 1, val: c);
		return out;
	}

	## Returns a Vulkan-clip-space ([0, 1] depth, Y-flipped) perspective matrix.
	Function of Mat4 is perspective(Float is fovRad, Float is aspect, Float is nearZ, Float is farZ){
		local Mat4 is out: Mat4();
		local Math is math: Math();
		local Float is f: 1.0 / math:tan(value: fovRad * 0.5);
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
		times(count: 16, worker: local Function(Int is i){
			Vulkan():packF32(dstAddr: dstAddr, byteOffset: i * 4, val: m:get(index: i));
		});
	}
}
