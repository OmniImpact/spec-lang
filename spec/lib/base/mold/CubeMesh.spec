#! Package base:mold
#! Unit colored 3D cube mesh (24 vertices, 36 uint16 indices, CCW winding).

Class is CubeMesh{
	replace [String] is namespace: ['base', 'mold'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'sys', Vulkan]
	];

	Int is vertAddr: 0;
	Int is vertBytes: 576;
	Int is idxAddr: 0;
	Int is idxBytes: 72;
	Int is idxCount: 36;
	Int is vCursor: 0;
	Int is iCursor: 0;

	## Allocates and populates the colored cube vertex and index buffers.
	replace Function is init(){
		vertAddr: alloc(bytes: vertBytes);
		idxAddr: alloc(bytes: idxBytes);
		vCursor: 0;
		iCursor: 0;

		## Front (+Z) - Coral Red
		:addFace(
			x0: -0.5, y0: -0.5, z0: 0.5,
			x1: 0.5, y1: -0.5, z1: 0.5,
			x2: 0.5, y2: 0.5, z2: 0.5,
			x3: -0.5, y3: 0.5, z3: 0.5,
			r: 0.95, g: 0.28, b: 0.28, baseIdx: 0
		);
		## Back (-Z) - Cyan
		:addFace(
			x0: 0.5, y0: -0.5, z0: -0.5,
			x1: -0.5, y1: -0.5, z1: -0.5,
			x2: -0.5, y2: 0.5, z2: -0.5,
			x3: 0.5, y3: 0.5, z3: -0.5,
			r: 0.22, g: 0.85, b: 0.90, baseIdx: 4
		);
		## Left (-X) - Emerald Green
		:addFace(
			x0: -0.5, y0: -0.5, z0: -0.5,
			x1: -0.5, y1: -0.5, z1: 0.5,
			x2: -0.5, y2: 0.5, z2: 0.5,
			x3: -0.5, y3: 0.5, z3: -0.5,
			r: 0.25, g: 0.88, b: 0.45, baseIdx: 8
		);
		## Right (+X) - Magenta
		:addFace(
			x0: 0.5, y0: -0.5, z0: 0.5,
			x1: 0.5, y1: -0.5, z1: -0.5,
			x2: 0.5, y2: 0.5, z2: -0.5,
			x3: 0.5, y3: 0.5, z3: 0.5,
			r: 0.88, g: 0.28, b: 0.82, baseIdx: 12
		);
		## Top (+Y) - Gold Yellow
		:addFace(
			x0: -0.5, y0: 0.5, z0: 0.5,
			x1: 0.5, y1: 0.5, z1: 0.5,
			x2: 0.5, y2: 0.5, z2: -0.5,
			x3: -0.5, y3: 0.5, z3: -0.5,
			r: 0.98, g: 0.82, b: 0.22, baseIdx: 16
		);
		## Bottom (-Y) - Cobalt Blue
		:addFace(
			x0: -0.5, y0: -0.5, z0: -0.5,
			x1: 0.5, y1: -0.5, z1: -0.5,
			x2: 0.5, y2: -0.5, z2: 0.5,
			x3: -0.5, y3: -0.5, z3: 0.5,
			r: 0.25, g: 0.48, b: 0.96, baseIdx: 20
		);
	}

	local Function is pushVertex(Float is x, Float is y, Float is z, Float is r, Float is g, Float is b){
		local Vulkan is vk: Vulkan();
		vk:packF32(dstAddr: vertAddr, byteOffset: vCursor, val: x);
		vk:packF32(dstAddr: vertAddr, byteOffset: vCursor + 4, val: y);
		vk:packF32(dstAddr: vertAddr, byteOffset: vCursor + 8, val: z);
		vk:packF32(dstAddr: vertAddr, byteOffset: vCursor + 12, val: r);
		vk:packF32(dstAddr: vertAddr, byteOffset: vCursor + 16, val: g);
		vk:packF32(dstAddr: vertAddr, byteOffset: vCursor + 20, val: b);
		vCursor: vCursor + 24;
	}

	local Function is pushTriPair(Int is a, Int is b, Int is c, Int is d, Int is e, Int is f){
		storeI32(ptr: idxAddr, byteOffset: iCursor, val: (b * 65536) + a);
		storeI32(ptr: idxAddr, byteOffset: iCursor + 4, val: (d * 65536) + c);
		storeI32(ptr: idxAddr, byteOffset: iCursor + 8, val: (f * 65536) + e);
		iCursor: iCursor + 12;
	}

	local Function is addFace(
		Float is x0, Float is y0, Float is z0,
		Float is x1, Float is y1, Float is z1,
		Float is x2, Float is y2, Float is z2,
		Float is x3, Float is y3, Float is z3,
		Float is r, Float is g, Float is b,
		Int is baseIdx
	){
		:pushVertex(x: x0, y: y0, z: z0, r: r, g: g, b: b);
		:pushVertex(x: x1, y: y1, z: z1, r: r, g: g, b: b);
		:pushVertex(x: x2, y: y2, z: z2, r: r, g: g, b: b);
		:pushVertex(x: x3, y: y3, z: z3, r: r, g: g, b: b);
		:pushTriPair(a: baseIdx, b: baseIdx + 1, c: baseIdx + 2, d: baseIdx, e: baseIdx + 2, f: baseIdx + 3);
	}

	Function of Int is vertexAddr(){ return vertAddr; }
	Function of Int is vertexBytes(){ return vertBytes; }
	Function of Int is indexAddr(){ return idxAddr; }
	Function of Int is indexBytes(){ return idxBytes; }
	Function of Int is indexCount(){ return idxCount; }

	## Frees the native vertex and index buffers.
	Function is dispose(){
		if({ vertAddr != 0 }, {
			free(ptr: vertAddr);
			vertAddr: 0;
		});
		if({ idxAddr != 0 }, {
			free(ptr: idxAddr);
			idxAddr: 0;
		});
	}
}
