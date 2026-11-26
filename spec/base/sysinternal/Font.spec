#! Package base:sysinternal
#! Thin floor bindings for `stb_truetype` font loading and scalar glyph metrics/rasterization (`spec_pal_font_*`).
#! Only `base:sys:Font` is permitted to call these declarations.

Class is Font{
	replace [String] is namespace: ['base', 'sysinternal'];

	## Loads a TrueType/OpenType font file from [path_cstr]; returns handle > 0 or -1.
	## Bound to `spec_pal_font_load`.
	Function of Int is pal_font_load(Int is path_cstr);

	## Resolves and loads the OS default sans-serif TrueType font; returns handle > 0 or -1.
	## Bound to `spec_pal_font_load_default`.
	Function of Int is pal_font_load_default();

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

	## Returns the C-string address of the last font error message.
	## Bound to `spec_pal_font_last_error`.
	Function of Int is pal_font_last_error();
}
