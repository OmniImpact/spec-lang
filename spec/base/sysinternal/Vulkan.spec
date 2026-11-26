#! Package base:sysinternal
#! Floor bindings for native Vulkan surface/swapchain/render (`spec_pal_vulkan_*`).
#! Only `base:sys:Vulkan` is permitted to call these declarations.

Class is Vulkan{
	replace [String] is namespace: ['base', 'sysinternal'];

	## Creates a Vulkan instance, Wayland surface, device, swapchain, and graphics pipeline.
	## Bound to `spec_pal_vulkan_create`.
	Function of Int is pal_vulkan_create(
		Int is wl_display,
		Int is wl_surface,
		Int is width,
		Int is height,
		Int is vert_spv_ptr,
		Int is vert_spv_bytes,
		Int is frag_spv_ptr,
		Int is frag_spv_bytes
	);

	## Uploads vertex and index buffers for the active mesh.
	## Bound to `spec_pal_vulkan_set_mesh`.
	Function of Int is pal_vulkan_set_mesh(
		Int is handle,
		Int is vert_ptr,
		Int is vert_bytes,
		Int is idx_ptr,
		Int is idx_bytes,
		Int is idx_count
	);

	## Renders a frame with the given 64-byte column-major `mat4` push constant.
	## Bound to `spec_pal_vulkan_render`.
	Function of Int is pal_vulkan_render(
		Int is handle,
		Int is mvp_f32_ptr,
		Int is width,
		Int is height
	);

	## Uploads an ARGB8888/BGRA8888 2D overlay image to composite over the 3D scene.
	## Bound to `spec_pal_vulkan_set_overlay`.
	Function of Int is pal_vulkan_set_overlay(
		Int is handle,
		Int is pixels_addr,
		Int is width,
		Int is height
	);

	## Destroys the Vulkan context and releases all GPU resources.
	## Bound to `spec_pal_vulkan_destroy`.
	Function of Int is pal_vulkan_destroy(Int is handle);

	## Returns the C-string address of the last Vulkan error message.
	## Bound to `spec_pal_vulkan_last_error`.
	Function of Int is pal_vulkan_last_error();

	## Converts a Spec `Float` (`f64`) to IEEE-754 `f32` and stores 4 bytes at [dst_ptr] + [byte_offset].
	## Bound to `spec_pal_vulkan_pack_f32`.
	Function of Int is pal_vulkan_pack_f32(Int is dst_ptr, Int is byte_offset, Float is val);
}
