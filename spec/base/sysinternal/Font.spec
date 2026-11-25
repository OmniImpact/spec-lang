#! Package base:sysinternal
#! Floor bindings for `stb_truetype` font loading and glyph rasterization (`spec_pal_font_*`).
#! Only `base:sys:Font` is permitted to call these declarations.

Class is Font{
	replace [String] is namespace: ['base', 'sysinternal'];

	## Loads a TrueType/OpenType font file at [path_cstr]; returns a handle > 0 or -1.
	## Bound to `spec_pal_font_load`.
	Function of Int is pal_font_load(Int is path_cstr);

	## Frees the font handle.
	## Bound to `spec_pal_font_close`.
	Function of Int is pal_font_close(Int is handle);

	## Draws UTF-8 [text_cstr] into an ARGB8888 buffer at [pixels_addr].
	## Bound to `spec_pal_font_draw_text`.
	Function of Int is pal_font_draw_text(Int is handle, Int is pixels_addr, Int is buf_w, Int is buf_h, Int is x, Int is y, Int is text_cstr, Int is pixel_height, Int is argb_color);

	## Returns the C-string address of the last font error.
	## Bound to `spec_pal_font_last_error`.
	Function of Int is pal_font_last_error();
}
