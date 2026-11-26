#! Package base:scrap
#! Scrap component binding a `SuitWindow` to a `base:sys:Vulkan` swapchain & 3D render pipeline.

Class of SewNode is VulkanSurface{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'sys', Vulkan],
		['base', 'suit', SuitWindow],
		['base', 'suit', SuitCanvas],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Constraints],
		['base', 'mold', SpirvBuilder],
		['base', 'mold', CubeMesh],
		['base', 'mold', Mat4]
	];

	Vulkan is vk: Vulkan();
	Int is mvpAddr: 0;
	CubeMesh is mesh: CubeMesh();
	Boolean is hasMesh: false;

	## Initializes the Vulkan surface wrapper.
	replace Function is init(CubeMesh is mesh: CubeMesh(), Boolean is hasMesh: false){
		vk: Vulkan();
		mvpAddr: alloc(bytes: 64);
		:mesh: mesh;
		:hasMesh: hasMesh;
	}

	## Attaches this Vulkan surface to an already-opened `SuitWindow` (`useVulkan: true`).
	Function of Boolean is attach(SuitWindow is window){
		local SpirvBuilder is vertSpv: SpirvBuilder();
		vertSpv:buildColorVertexShader();
		local SpirvBuilder is fragSpv: SpirvBuilder();
		fragSpv:buildColorFragmentShader();

		local Boolean is ok: vk:create(
			displayHandle: window:nativeDisplayHandle(),
			surfaceHandle: window:nativeSurfaceHandle(),
			width: window:width(),
			height: window:height(),
			vertSpvAddr: vertSpv:wordsAddr(),
			vertSpvBytes: vertSpv:byteLength(),
			fragSpvAddr: fragSpv:wordsAddr(),
			fragSpvBytes: fragSpv:byteLength()
		);

		vertSpv:dispose();
		fragSpv:dispose();
		if({ ok }, {
			local SpirvBuilder is ovVert: SpirvBuilder();
			ovVert:buildOverlayVertexShader();
			local SpirvBuilder is ovFrag: SpirvBuilder();
			ovFrag:buildOverlayFragmentShader();
			local Int is quadBuf: alloc(bytes: 96);
			vk:packF32(dstAddr: quadBuf, byteOffset: 0, val: -1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 4, val: -1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 8, val: 0.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 12, val: 0.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 16, val: 1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 20, val: -1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 24, val: 1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 28, val: 0.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 32, val: 1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 36, val: 1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 40, val: 1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 44, val: 1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 48, val: -1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 52, val: -1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 56, val: 0.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 60, val: 0.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 64, val: 1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 68, val: 1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 72, val: 1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 76, val: 1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 80, val: -1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 84, val: 1.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 88, val: 0.0);
			vk:packF32(dstAddr: quadBuf, byteOffset: 92, val: 1.0);
			vk:setOverlayPipeline(
				vertSpvAddr: ovVert:wordsAddr(),
				vertSpvBytes: ovVert:byteLength(),
				fragSpvAddr: ovFrag:wordsAddr(),
				fragSpvBytes: ovFrag:byteLength(),
				quadAddr: quadBuf,
				quadBytes: 96
			);
			free(ptr: quadBuf);
			ovVert:dispose();
			ovFrag:dispose();
		});
		if({ ok && hasMesh }, {
			:uploadCube(mesh: mesh);
		});
		return ok;
	}

	## Uploads a `CubeMesh` to the Vulkan vertex and index buffers.
	Function of Boolean is uploadCube(CubeMesh is mesh){
		return vk:setMesh(
			vertAddr: mesh:vertexAddr(),
			vertBytes: mesh:vertexBytes(),
			idxAddr: mesh:indexAddr(),
			idxBytes: mesh:indexBytes(),
			idxCount: mesh:indexCount()
		);
	}

	## Renders one frame using [mvp] and current surface dimensions [width] x [height].
	Function of Boolean is render(Mat4 is mvp, Int is width, Int is height){
		if({ mvpAddr == 0 }, { return false; });
		mvp:packF32(dstAddr: mvpAddr);
		return vk:render(mvpF32Addr: mvpAddr, width: width, height: height);
	}

	## Uploads an ARGB8888 [canvas] as the 2D HUD overlay composited over the 3D scene.
	Function of Boolean is setOverlay(SuitCanvas is canvas){
		return vk:setOverlay(pixelsAddr: canvas:pixelsAddr(), width: canvas:width, height: canvas:height);
	}

	## Constrains the 3D render viewport/scissor to ([x], [y], [w], [h]).
	Function of Boolean is setViewport(Int is x, Int is y, Int is w, Int is h){
		return vk:setViewport(x: x, y: y, w: w, h: h);
	}

	## Sets the 3D renderpass clear color.
	Function of Boolean is setClearColor(Float is r, Float is g, Float is b, Float is a: 1.0){
		return vk:setClearColor(r: r, g: g, b: b, a: a);
	}

	## Renders the 2D overlay only (no 3D mesh push constants).
	Function of Boolean is presentOverlay(Int is width, Int is height){
		return vk:render(mvpF32Addr: 0, width: width, height: height);
	}

	replace Function of Size is measure(Constraints is c){
		desiredSize: Size(width: c:maxW, height: c:maxH);
		return desiredSize;
	}

	## Returns the last Vulkan error message, or `''`.
	Function of String is lastError(){
		return vk:lastError();
	}

	## Releases Vulkan resources and native staging memory.
	Function is dispose(){
		if({ hasMesh }, { mesh:dispose(); });
		vk:shutdown();
		if({ mvpAddr != 0 }, {
			free(ptr: mvpAddr);
			mvpAddr: 0;
		});
	}
}
