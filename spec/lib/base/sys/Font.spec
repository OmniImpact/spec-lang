#! Package base:sys
#! Safe Spec wrapper over `base:sysinternal:Font` (`stb_truetype`).

Class is Font{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'sysinternal', Font]
	];

	Int is handle: -1;

	local Function of Int is cstrAddr(String is s){
		local Int is sAddr: Mem:objToAddr(obj: s);
		return if({ sAddr != 0 }, { Mem:loadI64(ptr: sAddr, byteOffset: 0) }, { 0 });
	}

	## Loads a TrueType/OpenType font from [path].
	Function of Boolean is load(String is path){
		if({ handle > 0 }, { close(); });
		handle: base:sysinternal:Font:pal_font_load(path_cstr: :cstrAddr(s: path));
		return handle > 0;
	}

	## Closes the loaded font.
	Function is close(){
		if({ handle > 0 }, {
			base:sysinternal:Font:pal_font_close(handle: handle);
			handle: -1;
		});
	}

	## True when a font is loaded.
	Function of Boolean is isLoaded(){
		return handle > 0;
	}

	## Rasterizes UTF-8 [text] onto an ARGB8888 pixel buffer at [pixelsAddr].
	Function of Boolean is drawText(Int is pixelsAddr, Int is bufW, Int is bufH, Int is x, Int is y, String is text, Int is pixelHeight: 16, Int is argbColor: -1){
		if({ handle <= 0 || pixelsAddr == 0 }, { return false; });
		return base:sysinternal:Font:pal_font_draw_text(
			handle: handle,
			pixels_addr: pixelsAddr,
			buf_w: bufW,
			buf_h: bufH,
			x: x,
			y: y,
			text_cstr: :cstrAddr(s: text),
			pixel_height: pixelHeight,
			argb_color: argbColor
		) != 0;
	}

	## Returns the last font error message.
	Function of String is lastError(){
		local Int is cstr: base:sysinternal:Font:pal_font_last_error();
		if({ cstr == 0 }, { return ''; });
		return Mem:strFromBytes(srcAddr: cstr, len: Mem:cstrLen(cstrAddr: cstr));
	}
}
