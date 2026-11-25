#! Package base:sys
#! Safe Spec wrapper over `base:sysinternal:Window` for native OS windowing.

Class is Window{
	replace [String] is namespace: ['base', 'sys'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'sysinternal', Window]
	];

	Int is handle: -1;

	local Function of Int is cstrAddr(String is s){
		local Int is sAddr: Mem:objToAddr(obj: s);
		return if({ sAddr != 0 }, { Mem:loadI64(ptr: sAddr, byteOffset: 0) }, { 0 });
	}

	## Opens a native OS window.
	Function of Boolean is open(String is title: 'Suit', Int is width: 800, Int is height: 600, Boolean is decorated: true){
		if({ handle > 0 }, { close(); });
		local Int is decFlag: if({ decorated }, { 1 }, { 0 });
		handle: base:sysinternal:Window:pal_window_open(
			title_cstr: :cstrAddr(s: title),
			width: width,
			height: height,
			decorated: decFlag
		);
		return handle > 0;
	}

	## Dispatches pending window events; returns `true` while the window remains open.
	Function of Boolean is poll(){
		if({ handle <= 0 }, { return false; });
		local Int is alive: base:sysinternal:Window:pal_window_poll(handle: handle);
		if({ alive == 0 }, {
			close();
			return false;
		});
		return true;
	}

	## Closes the window if open.
	Function is close(){
		if({ handle > 0 }, {
			base:sysinternal:Window:pal_window_close(handle: handle);
			handle: -1;
		});
	}

	## True when the native window is currently open.
	Function of Boolean is isOpen(){
		return handle > 0;
	}

	## Returns the last windowing error message.
	Function of String is lastError(){
		local Int is cstr: base:sysinternal:Window:pal_window_last_error();
		if({ cstr == 0 }, { return ''; });
		return Mem:strFromBytes(srcAddr: cstr, len: Mem:cstrLen(cstrAddr: cstr));
	}

	## Returns the next queued ASCII/key code, or `0` if none.
	Function of Int is nextKey(){
		if({ handle <= 0 }, { return 0; });
		return base:sysinternal:Window:pal_window_next_key(handle: handle);
	}

	## Returns the current content width in pixels.
	Function of Int is width(){
		if({ handle <= 0 }, { return 0; });
		return base:sysinternal:Window:pal_window_width(handle: handle);
	}

	## Returns the current content height in pixels.
	Function of Int is height(){
		if({ handle <= 0 }, { return 0; });
		return base:sysinternal:Window:pal_window_height(handle: handle);
	}

	## Presents an ARGB8888 pixel buffer at [pixelsAddr] to the window.
	Function of Boolean is present(Int is pixelsAddr, Int is width, Int is height){
		if({ handle <= 0 || pixelsAddr == 0 }, { return false; });
		return base:sysinternal:Window:pal_window_present(
			handle: handle,
			pixels_addr: pixelsAddr,
			width: width,
			height: height
		) != 0;
	}
}
