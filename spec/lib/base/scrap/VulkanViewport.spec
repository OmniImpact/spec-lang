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

	Vulkan is vk: Vulkan();
	Boolean is vkTried: false;
	Boolean is vkReady: false;
	Int is mvpAddr: 0;
	Int is outBufAddr: 0;
	Int is outBufBytes: 0;
	CubeMesh is cube: CubeMesh();
	CubeMesh is roomCube: CubeMesh(inward: true);
	SphereMesh is sphere: SphereMesh();
	Float is rotY: 0.4;
	Float is rotX: 0.35;
	Int is lastTickMs: 0;

	replace Function is init(
		Float is widthPt: 180.0,
		Float is heightPt: 180.0,
		Boolean is sphereInCube: false,
		Color is sphereColor: Color(r: 175, g: 178, b: 184),
		String is tooltip: ''
	){
		:widthPt: widthPt;
		:heightPt: heightPt;
		:sphereInCube: sphereInCube;
		:sphereColor: sphereColor;
		:tooltip: tooltip;
		:mvpAddr: alloc(bytes: 64);
		:sphere: SphereMesh(
			radius: 0.28,
			r: (sphereColor:r as Float) / 255.0,
			g: (sphereColor:g as Float) / 255.0,
			b: (sphereColor:b as Float) / 255.0
		);
	}

	Function is setSphereColor(Color is next){
		:sphereColor: next;
		sphere:setColor(
			r: (next:r as Float) / 255.0,
			g: (next:g as Float) / 255.0,
			b: (next:b as Float) / 255.0
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

	local Function is ensureVulkan(Int is w, Int is h){
		if({ vkTried }, { return; });
		:vkTried: true;
		local SpirvBuilder is vertSpv: SpirvBuilder();
		vertSpv:buildColorVertexShader();
		local SpirvBuilder is fragSpv: SpirvBuilder();
		fragSpv:buildColorFragmentShader();
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
			vk:setMesh(
				vertAddr: sphere:vertAddr,
				vertBytes: sphere:vertBytes,
				idxAddr: sphere:idxAddr,
				idxBytes: sphere:idxBytes,
				idxCount: sphere:idxCount
			);
			vk:setBlendMesh(
				vertAddr: roomCube:vertAddr,
				vertBytes: roomCube:vertBytes,
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
}
