#! Package base:sysinternal
#! Floor bindings for native OS windows (`spec_pal_window_*`).
#! Only `base:sys:Window` is permitted to call these declarations.

Class is Window{
	replace [String] is namespace: ['base', 'sysinternal'];

	## Opens a native window with [title_cstr], [width]x[height], and optional decorations.
	## Bound to `spec_pal_window_open`.
	Function of Int is pal_window_open(Int is title_cstr, Int is width, Int is height, Int is decorated);

	## Opens a native window with [title_cstr], [width]x[height], optional decorations, and Vulkan mode.
	## Bound to `spec_pal_window_open_ex`.
	Function of Int is pal_window_open_ex(Int is title_cstr, Int is width, Int is height, Int is decorated, Int is use_vulkan);

	## Returns the native display handle (`wl_display*`, etc.).
	## Bound to `spec_pal_window_display_handle`.
	Function of Int is pal_window_display_handle(Int is handle);

	## Returns the native surface handle (`wl_surface*`, etc.).
	## Bound to `spec_pal_window_surface_handle`.
	Function of Int is pal_window_surface_handle(Int is handle);

	## Dispatches pending window events; returns `1` while open or `0` on close.
	## Bound to `spec_pal_window_poll`.
	Function of Int is pal_window_poll(Int is handle);

	## Closes the native window and releases its resources.
	## Bound to `spec_pal_window_close`.
	Function of Int is pal_window_close(Int is handle);

	## Returns the C-string address of the last window error message.
	## Bound to `spec_pal_window_last_error`.
	Function of Int is pal_window_last_error();

	## Returns the next queued key code (`'w'`, `'a'`, `'s'`, `'d'`, `'q'`, `'e'`, `27`), or `0`.
	## Bound to `spec_pal_window_next_key`.
	Function of Int is pal_window_next_key(Int is handle);

	## Returns the current content width in pixels.
	## Bound to `spec_pal_window_width`.
	Function of Int is pal_window_width(Int is handle);

	## Returns the current content height in pixels.
	## Bound to `spec_pal_window_height`.
	Function of Int is pal_window_height(Int is handle);

	Function of Int is pal_window_pointer_x(Int is handle);
	Function of Int is pal_window_pointer_y(Int is handle);
	Function of Int is pal_window_poll_click(Int is handle);
	Function of Int is pal_window_click_x(Int is handle);
	Function of Int is pal_window_click_y(Int is handle);
	Function of Int is pal_window_poll_scroll_y(Int is handle);
	Function of Int is pal_window_set_title(Int is handle, Int is title_cstr);

	## Presents an ARGB8888 pixel buffer at [pixels_addr] to the window.
	## Bound to `spec_pal_window_present`.
	Function of Int is pal_window_present(Int is handle, Int is pixels_addr, Int is width, Int is height);
}
