#! Package base:sysinternal
#! Minimum-floor bindings for `stb_truetype` font initialization and scalar glyph primitives (`spec_pal_font_*`).
#! Only `base:sys:Font` is permitted to call these declarations.

Class is Font{
	replace [String] is namespace: ['base', 'sysinternal'];

	## Initializes a TrueType/OpenType font from a memory buffer ([data_ptr], [data_len]); returns handle > 0 or -1.
	## Bound to `spec_pal_font_init_memory`.
	Function of Int is pal_font_init_memory(Int is data_ptr, Int is data_len);

	## Queries the OS default sans-serif font path (e.g. via libfontconfig) into [out_buf]; returns byte length or 0.
	## Bound to `spec_pal_font_default_path`.
	Function of Int is pal_font_default_path(Int is out_buf, Int is out_cap);

	## Queries a system font path matching [mono], [bold], and [italic] into [out_buf]; returns byte length or 0.
	## Bound to `spec_pal_font_find_path`.
	Function of Int is pal_font_find_path(Int is mono, Int is bold, Int is italic, Int is out_buf, Int is out_cap);

	## Releases a loaded font handle.
	## Bound to `spec_pal_font_close`.
	Function of Int is pal_font_close(Int is handle);

	## Returns `stbtt_ScaleForPixelHeight` for [pixel_height].
	## Bound to `spec_pal_font_scale`.
	Function of Float is pal_font_scale(Int is handle, Int is pixel_height);

	## Writes `[ascent, descent, lineGap]` (raw font units) to 3 `i32` slots at [out_3_i32_ptr].
	## Bound to `spec_pal_font_vmetrics`.
	Function of Int is pal_font_vmetrics(Int is handle, Int is out_3_i32_ptr);

	## Writes `[advanceWidth, leftSideBearing]` (raw font units) for [cp] to 2 `i32` slots at [out_2_i32_ptr].
	## Bound to `spec_pal_font_hmetrics`.
	Function of Int is pal_font_hmetrics(Int is handle, Int is cp, Int is out_2_i32_ptr);

	## Returns raw kerning advance between [cp1] and [cp2].
	## Bound to `spec_pal_font_kern_advance`.
	Function of Int is pal_font_kern_advance(Int is handle, Int is cp1, Int is cp2);

	## Writes `[x0, y0, x1, y1]` bitmap bounding box for [cp] at [pixel_height] to 4 `i32` slots at [out_4_i32_ptr].
	## Bound to `spec_pal_font_glyph_box`.
	Function of Int is pal_font_glyph_box(Int is handle, Int is cp, Int is pixel_height, Int is out_4_i32_ptr);

	## Rasterizes [cp] at [pixel_height] as 8-bit coverage into [dst_ptr] ([gw] x [gh]).
	## Bound to `spec_pal_font_rasterize_glyph`.
	Function of Int is pal_font_rasterize_glyph(Int is handle, Int is cp, Int is pixel_height, Int is dst_ptr, Int is gw, Int is gh);

	## Writes `[x0, y0, x1, y1]` bitmap bounding box for [cp] at [pixel_height] with horizontal subpixel [shift_x] in `[0, 1)`.
	## Bound to `spec_pal_font_glyph_box_subpixel`.
	Function of Int is pal_font_glyph_box_subpixel(Int is handle, Int is cp, Int is pixel_height, Float is shift_x, Int is out_4_i32_ptr);

	## Rasterizes [cp] at [pixel_height] with horizontal subpixel [shift_x] into [dst_ptr] ([gw] x [gh]).
	## Bound to `spec_pal_font_rasterize_glyph_subpixel`.
	Function of Int is pal_font_rasterize_glyph_subpixel(Int is handle, Int is cp, Int is pixel_height, Float is shift_x, Int is dst_ptr, Int is gw, Int is gh);

	## Returns 1 if [cp] maps to a non-zero glyph index in [handle], else 0.
	## Bound to `spec_pal_font_has_glyph`.
	Function of Int is pal_font_has_glyph(Int is handle, Int is cp);

	## Returns the C-string address of the last font error message.
	## Bound to `spec_pal_font_last_error`.
	Function of Int is pal_font_last_error();
}
