#! Package base:mold
#! UV-sphere 3D mesh with configurable radius and color plus directional shading (6 floats/vertex: xyz + rgb).

Class is SphereMesh{
	replace [String] is namespace: ['base', 'mold'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'math', as Math()],
		['base', 'sys', Vulkan]
	];

	Float is radius: 0.36;
	Int is stacks: 14;
	Int is slices: 22;
	Float is colorR: 0.25;
	Float is colorG: 0.72;
	Float is colorB: 0.96;

	Int is vertAddr: 0;
	Int is vertBytes: 0;
	Int is idxAddr: 0;
	Int is idxBytes: 0;
	Int is idxCount: 0;

	replace Function is init(
		Float is radius: 0.36,
		Int is stacks: 14,
		Int is slices: 22,
		Float is r: 0.25,
		Float is g: 0.72,
		Float is b: 0.96
	){
		:radius: radius;
		:stacks: stacks;
		:slices: slices;
		:colorR: r;
		:colorG: g;
		:colorB: b;
		local Int is vCount: (stacks + 1) * (slices + 1);
		:vertBytes: vCount * 24;
		:idxCount: stacks * slices * 6;
		:idxBytes: idxCount * 2;
		:vertAddr: alloc(bytes: vertBytes);
		:idxAddr: alloc(bytes: idxBytes);
		:rebuild();
	}

	Function is setColor(Float is r, Float is g, Float is b){
		:colorR: r;
		:colorG: g;
		:colorB: b;
		:rebuild();
	}

	local Function is rebuild(){
		local Vulkan is vk: Vulkan();
		local Float is pi: 3.14159265;
		local Int is vCursor: 0;
		local Int is st: 0;
		while({ st <= stacks }, {
			local Float is v: (st as Float) / (stacks as Float);
			local Float is phi: v * pi;
			local Float is sinP: Math:sin(value: phi);
			local Float is cosP: Math:cos(value: phi);
			local Int is sl: 0;
			while({ sl <= slices }, {
				local Float is u: (sl as Float) / (slices as Float);
				local Float is theta: u * 2.0 * pi;
				local Float is nx: sinP * Math:cos(value: theta);
				local Float is ny: cosP;
				local Float is nz: sinP * Math:sin(value: theta);
				local Float is px: nx * radius;
				local Float is py: ny * radius;
				local Float is pz: nz * radius;
				# Directional diffuse + Blinn-Phong specular highlight from upper-front-right light source
				local Float is ndotl: nx * 0.42 + ny * 0.68 + nz * 0.60;
				if({ ndotl < 0.0 }, { ndotl: 0.0; });
				local Float is shade: 0.25 + 0.75 * ndotl;
				# Half-vector H = normalize((0.42, 0.68, 0.60) + (0, 0, 1)) ~= (0.235, 0.380, 0.895)
				local Float is ndoth: nx * 0.235 + ny * 0.380 + nz * 0.895;
				if({ ndoth < 0.0 }, { ndoth: 0.0; });
				local Float is spec2: ndoth * ndoth;
				local Float is spec4: spec2 * spec2;
				local Float is spec16: spec4 * spec4 * spec4 * spec4;
				local Float is spec: spec16 * 0.55;
				local Float is outR: colorR * shade + spec;
				local Float is outG: colorG * shade + spec;
				local Float is outB: colorB * shade + spec;
				if({ outR > 1.0 }, { outR: 1.0; });
				if({ outG > 1.0 }, { outG: 1.0; });
				if({ outB > 1.0 }, { outB: 1.0; });
				vk:packF32(dstAddr: vertAddr, byteOffset: vCursor, val: px);
				vk:packF32(dstAddr: vertAddr, byteOffset: vCursor + 4, val: py);
				vk:packF32(dstAddr: vertAddr, byteOffset: vCursor + 8, val: pz);
				vk:packF32(dstAddr: vertAddr, byteOffset: vCursor + 12, val: outR);
				vk:packF32(dstAddr: vertAddr, byteOffset: vCursor + 16, val: outG);
				vk:packF32(dstAddr: vertAddr, byteOffset: vCursor + 20, val: outB);
				vCursor: vCursor + 24;
				sl: sl + 1;
			});
			st: st + 1;
		});

		local Int is iCursor: 0;
		local Int is s: 0;
		local Int is stride: slices + 1;
		while({ s < stacks }, {
			local Int is c: 0;
			while({ c < slices }, {
				local Int is a: s * stride + c;
				local Int is b: a + stride;
				local Int is c0: a + 1;
				local Int is d0: b + 1;
				storeI32(ptr: idxAddr, byteOffset: iCursor, val: (b * 65536) + a);
				storeI32(ptr: idxAddr, byteOffset: iCursor + 4, val: (b * 65536) + c0);
				storeI32(ptr: idxAddr, byteOffset: iCursor + 8, val: (c0 * 65536) + d0);
				iCursor: iCursor + 12;
				c: c + 1;
			});
			s: s + 1;
		});
	}

	Function is dispose(){
		if({ vertAddr != 0 }, { free(ptr: vertAddr); vertAddr: 0; });
		if({ idxAddr != 0 }, { free(ptr: idxAddr); idxAddr: 0; });
	}
}
