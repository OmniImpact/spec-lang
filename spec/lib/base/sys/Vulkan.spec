#! Package base:sys
#! Safe Spec wrapper over `base:sysinternal:Vulkan` for native Vulkan rendering.

Class is Vulkan{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'sysinternal', Vulkan]
	];

	Int is handle: 0;

	## Creates a Vulkan context attached to native [displayHandle] and [surfaceHandle].
	Function of Boolean is create(
		Int is displayHandle,
		Int is surfaceHandle,
		Int is width,
		Int is height,
		Int is vertSpvAddr,
		Int is vertSpvBytes,
		Int is fragSpvAddr,
		Int is fragSpvBytes
	){
		if({ handle != 0 }, { shutdown(); });
		handle: base:sysinternal:Vulkan:pal_vulkan_create(
			wl_display: displayHandle,
			wl_surface: surfaceHandle,
			width: width,
			height: height,
			vert_spv_ptr: vertSpvAddr,
			vert_spv_bytes: vertSpvBytes,
			frag_spv_ptr: fragSpvAddr,
			frag_spv_bytes: fragSpvBytes
		);
		return handle != 0;
	}

	## Uploads vertex and index buffers for the active mesh.
	Function of Boolean is setMesh(Int is vertAddr, Int is vertBytes, Int is idxAddr, Int is idxBytes, Int is idxCount){
		if({ handle == 0 }, { return false; });
		return base:sysinternal:Vulkan:pal_vulkan_set_mesh(
			handle: handle,
			vert_ptr: vertAddr,
			vert_bytes: vertBytes,
			idx_ptr: idxAddr,
			idx_bytes: idxBytes,
			idx_count: idxCount
		) != 0;
	}

	## Renders a frame with the given 64-byte column-major `mat4` push constant at [mvpF32Addr].
	Function of Boolean is render(Int is mvpF32Addr, Int is width, Int is height){
		if({ handle == 0 }, { return false; });
		return base:sysinternal:Vulkan:pal_vulkan_render(
			handle: handle,
			mvp_f32_ptr: mvpF32Addr,
			width: width,
			height: height
		) != 0;
	}

	## Uploads an ARGB8888 2D overlay buffer at [pixelsAddr] to composite over the 3D scene.
	Function of Boolean is setOverlay(Int is pixelsAddr, Int is width, Int is height){
		if({ handle == 0 || pixelsAddr == 0 || width <= 0 || height <= 0 }, { return false; });
		return base:sysinternal:Vulkan:pal_vulkan_set_overlay(
			handle: handle,
			pixels_addr: pixelsAddr,
			width: width,
			height: height
		) != 0;
	}

	## Destroys the Vulkan context and releases GPU resources.
	Function is shutdown(){
		if({ handle != 0 }, {
			base:sysinternal:Vulkan:pal_vulkan_destroy(handle: handle);
			handle: 0;
		});
	}

	## Returns `true` if a Vulkan context is active.
	Function of Boolean is isCreated(){
		return handle != 0;
	}

	## Returns the last Vulkan error message, or `''`.
	Function of String is lastError(){
		local Int is cstr: base:sysinternal:Vulkan:pal_vulkan_last_error();
		if({ cstr == 0 }, { return ''; });
		local Int is len: Mem:cstrLen(cstrAddr: cstr);
		if({ len <= 0 }, { return ''; });
		return Mem:strFromBytes(srcAddr: cstr, len: len);
	}

	## Packs a Spec `Float` (`f64`) as IEEE-754 `f32` at [dstAddr] + [byteOffset].
	Function is packF32(Int is dstAddr, Int is byteOffset, Float is val){
		base:sysinternal:Vulkan:pal_vulkan_pack_f32(dst_ptr: dstAddr, byte_offset: byteOffset, val: val);
	}
}
