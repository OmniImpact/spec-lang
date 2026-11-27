#! Package base:scrap
#! Embedded offscreen Vulkan 3D viewport widget (`SewNode`) with transparent background and optional sphere-in-cube scene.

Class of SewNode is VulkanViewport{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'sys', Vulkan],
		['base', 'fabric', Color],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'mold', SpirvBuilder],
		['base', 'mold', CubeMesh],
		['base', 'mold', SphereMesh],
		['base', 'mold', Mat4]
	];

	Float is widthPt: 180.0;
	Float is heightPt: 180.0;
	Boolean is sphereInCube: false;
	Color is sphereColor: Color(r: 175, g: 178, b: 184);
	Float is specularity: 0.55;
	Float is reflectivity: 0.25;

	Vulkan is vk: Vulkan();
	Boolean is vkTried: false;
	Boolean is vkReady: false;
	Int is mvpAddr: 0;
	Int is outBufAddr: 0;
	Int is outBufBytes: 0;
	CubeMesh is cube: CubeMesh();
	CubeMesh is roomCube: CubeMesh(inward: true);
	Int is roomVert36Addr: 0;
	SphereMesh is sphere: SphereMesh();
	Float is rotY: 0.4;
	Float is rotX: 0.35;
	Int is lastTickMs: 0;

	replace Function is init(
		Float is widthPt: 180.0,
		Float is heightPt: 180.0,
		Boolean is sphereInCube: false,
		Color is sphereColor: Color(r: 175, g: 178, b: 184),
		Float is specularity: 0.55,
		Float is reflectivity: 0.25,
		String is tooltip: ''
	){
		:widthPt: widthPt;
		:heightPt: heightPt;
		:sphereInCube: sphereInCube;
		:sphereColor: sphereColor;
		:specularity: specularity;
		:reflectivity: reflectivity;
		:tooltip: tooltip;
		:mvpAddr: alloc(bytes: 128);
		:sphere: SphereMesh(
			radius: 0.28,
			r: (sphereColor:red() as Float) / 255.0,
			g: (sphereColor:green() as Float) / 255.0,
			b: (sphereColor:blue() as Float) / 255.0
		);
	}

	Function is setSphereColor(Color is next){
		:sphereColor: next;
		sphere:setColor(
			r: (next:red() as Float) / 255.0,
			g: (next:green() as Float) / 255.0,
			b: (next:blue() as Float) / 255.0
		);
		if({ vkReady && sphereInCube }, {
			vk:setMesh(
				vertAddr: sphere:vertAddr,
				vertBytes: sphere:vertBytes,
				idxAddr: sphere:idxAddr,
				idxBytes: sphere:idxBytes,
				idxCount: sphere:idxCount
			);
		});
		:invalidate();
	}

	Function is setSpecularity(Float is next){
		local Float is v: next;
		if({ v < 0.0 }, { v: 0.0; });
		if({ v > 1.0 }, { v: 1.0; });
		:specularity: v;
		:invalidate();
	}

	Function is setReflectivity(Float is next){
		local Float is v: next;
		if({ v < 0.0 }, { v: 0.0; });
		if({ v > 1.0 }, { v: 1.0; });
		:reflectivity: v;
		:invalidate();
	}

	local Function is ensureVulkan(Int is w, Int is h){
		if({ vkTried }, { return; });
		:vkTried: true;
		local SpirvBuilder is vertSpv: SpirvBuilder();
		local SpirvBuilder is fragSpv: SpirvBuilder();
		if({ sphereInCube }, {
			vertSpv:buildLitReflectVertexShader();
			fragSpv:buildLitReflectFragmentShader();
		}, {
			vertSpv:buildColorVertexShader();
			fragSpv:buildColorFragmentShader();
		});
		local Boolean is ok: vk:createOffscreen(
			width: w,
			height: h,
			vertSpvAddr: vertSpv:wordsAddr(),
			vertSpvBytes: vertSpv:byteLength(),
			fragSpvAddr: fragSpv:wordsAddr(),
			fragSpvBytes: fragSpv:byteLength()
		);
		vertSpv:dispose();
		fragSpv:dispose();
		if({ !ok }, { return; });
		vk:setClearColor(r: 0.0, g: 0.0, b: 0.0, a: 0.0);
		if({ sphereInCube }, {
			local Int is r36Bytes: 24 * 36;
			if({ roomVert36Addr == 0 }, { :roomVert36Addr: alloc(bytes: r36Bytes); });
			local Int is vi: 0;
			while({ vi < 24 }, {
				local Int is srcOff: vi * 24;
				local Int is dstOff: vi * 36;
				local Int is k: 0;
				while({ k < 24 }, {
					storeI32(ptr: roomVert36Addr, byteOffset: dstOff + k, val: loadI32(ptr: roomCube:vertAddr, byteOffset: srcOff + k));
					k: k + 4;
				});
				vk:packF32(dstAddr: roomVert36Addr, byteOffset: dstOff + 24, val: 0.0);
				vk:packF32(dstAddr: roomVert36Addr, byteOffset: dstOff + 28, val: 0.0);
				vk:packF32(dstAddr: roomVert36Addr, byteOffset: dstOff + 32, val: 0.0);
				vi: vi + 1;
			});
			vk:setMesh(
				vertAddr: sphere:vertAddr,
				vertBytes: sphere:vertBytes,
				idxAddr: sphere:idxAddr,
				idxBytes: sphere:idxBytes,
				idxCount: sphere:idxCount
			);
			vk:setBlendMesh(
				vertAddr: roomVert36Addr,
				vertBytes: r36Bytes,
				idxAddr: roomCube:idxAddr,
				idxBytes: roomCube:idxBytes,
				idxCount: roomCube:idxCount
			);
		}, {
			vk:setMesh(
				vertAddr: cube:vertAddr,
				vertBytes: cube:vertBytes,
				idxAddr: cube:idxAddr,
				idxBytes: cube:idxBytes,
				idxCount: cube:idxCount
			);
		});
		:vkReady: true;
	}

	replace Function of Boolean is tick(Int is nowMs){
		if({ sphereInCube }, { return false; });
		if({ lastTickMs > 0 }, {
			local Int is dt: nowMs - lastTickMs;
			if({ dt > 0 && dt < 200 }, {
				local Float is dtf: (dt as Float) / 1000.0;
				:rotY: rotY + dtf * 1.1;
				:rotX: rotX + dtf * 0.65;
			});
		});
		:lastTickMs: nowMs;
		:invalidate();
		return true;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is w: activeScale:px(pt: widthPt);
		local Int is h: activeScale:px(pt: heightPt);
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		:ensureVulkan(w: b:width, h: b:height);
		if({ !vkReady }, {
			local Int is fpx: activeScale:px(pt: activeTheme:baseTextPt);
			local String is errMsg: vk:lastError();
			local String is msg: if({ errMsg != '' }, { 'Vulkan unavailable: ' . errMsg }, { 'Vulkan unavailable' });
			ctx:drawText(x: b:x + 8, y: b:y + b:height / 2, text: msg, color: activeTheme:textMuted, pixelHeight: fpx);
			return;
		});

		local Int is needBytes: b:width * b:height * 4;
		if({ outBufAddr == 0 || needBytes > outBufBytes }, {
			if({ outBufAddr != 0 }, { free(ptr: outBufAddr); });
			:outBufAddr: alloc(bytes: needBytes);
			:outBufBytes: needBytes;
		});

		local Float is aspect: (b:width as Float) / (b:height as Float);
		local Mat4 is proj: Mat4():perspective(fovRad: 0.785398, aspect: aspect, nearZ: 0.1, farZ: 20.0);
		local Float is camZ: if({ sphereInCube }, { -1.85 }, { -2.45 });
		local Mat4 is view: Mat4():translate(tx: 0.0, ty: 0.0, tz: camZ);
		local Mat4 is model: if({ sphereInCube }, {
			Mat4():identity()
		}, {
			Mat4():rotateY(rad: rotY):mul(other: Mat4():rotateX(rad: rotX))
		});
		local Mat4 is mvp: proj:mul(other: view):mul(other: model);
		mvp:packF32(dstAddr: mvpAddr);
		vk:packF32(dstAddr: mvpAddr, byteOffset: 64, val: specularity);
		vk:packF32(dstAddr: mvpAddr, byteOffset: 68, val: reflectivity);
		vk:packF32(dstAddr: mvpAddr, byteOffset: 72, val: 0.0);
		vk:packF32(dstAddr: mvpAddr, byteOffset: 76, val: 0.0);
		vk:packF32(dstAddr: mvpAddr, byteOffset: 80, val: 1.85);
		vk:packF32(dstAddr: mvpAddr, byteOffset: 84, val: 0.35);
		vk:packF32(dstAddr: mvpAddr, byteOffset: 88, val: 0.40);
		vk:packF32(dstAddr: mvpAddr, byteOffset: 92, val: 0.45);

		if({ !vk:renderToPixels(mvpF32Addr: mvpAddr, outPixelsAddr: outBufAddr, width: b:width, height: b:height) }, {
			return;
		});

		local Int is py: 0;
		while({ py < b:height }, {
			local Int is rowOff: py * b:width * 4;
			local Int is px: 0;
			while({ px < b:width }, {
				local Int is col: loadI32(ptr: outBufAddr, byteOffset: rowOff + px * 4);
				local Int is a: (col >> 24) & 255;
				if({ a > 0 }, {
					ctx:fillRect(x: b:x + px, y: b:y + py, w: 1, h: 1, color: col);
				});
				px: px + 1;
			});
			py: py + 1;
		});
	}

	## Releases native pixel/push-constant buffers, GPU meshes, and offscreen Vulkan state.
	Function is dispose(){
		if({ vkReady }, {
			vk:shutdown();
			:vkReady: false;
		});
		cube:dispose();
		roomCube:dispose();
		sphere:dispose();
		if({ mvpAddr != 0 }, {
			free(ptr: mvpAddr);
			:mvpAddr: 0;
		});
		if({ outBufAddr != 0 }, {
			free(ptr: outBufAddr);
			:outBufAddr: 0;
			:outBufBytes: 0;
		});
		if({ roomVert36Addr != 0 }, {
			free(ptr: roomVert36Addr);
			:roomVert36Addr: 0;
		});
	}

	Function is destroy(){
		:dispose();
	}
}
