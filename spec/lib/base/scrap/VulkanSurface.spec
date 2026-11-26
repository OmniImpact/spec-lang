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

	## Initializes the Vulkan surface wrapper.
	replace Function is init(){
		vk: Vulkan();
		mvpAddr: alloc(bytes: 64);
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
		vk:shutdown();
		if({ mvpAddr != 0 }, {
			free(ptr: mvpAddr);
			mvpAddr: 0;
		});
	}
}
