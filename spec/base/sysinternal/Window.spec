#! Package base:sysinternal
#! Floor bindings for native OS windows (`spec_pal_window_*`).
#! Only `base:sys:Window` is permitted to call these declarations.

Class is Window{
	replace [String] is namespace: ['base', 'sysinternal'];

	## Opens a native window with [title_cstr], [width]x[height], and optional decorations.
	## Bound to `spec_pal_window_open`.
	Function of Int is pal_window_open(Int is title_cstr, Int is width, Int is height, Int is decorated);

	## Dispatches pending window events; returns `1` while open or `0` on close.
	## Bound to `spec_pal_window_poll`.
	Function of Int is pal_window_poll(Int is handle);

	## Closes the native window and releases its resources.
	## Bound to `spec_pal_window_close`.
	Function of Int is pal_window_close(Int is handle);

	## Returns the C-string address of the last window error message.
	## Bound to `spec_pal_window_last_error`.
	Function of Int is pal_window_last_error();
}
