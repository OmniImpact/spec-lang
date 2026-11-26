#! Package base:suit
#! Suit (Spec UI Toolkit) native window abstraction.

Class is SuitWindow{
	replace [String] is namespace: ['base', 'suit'];

	merge [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'suit', SuitCanvas],
		['base', 'suit', InputEvent],
		['base', 'sys', Window]
	];

	String is title: 'Suit';
	Int is width: 800;
	Int is height: 600;
	Boolean is decorated: true;
	Boolean is useVulkan: false;
	Window is native: Window();
	Int is evBufAddr: 0;

	replace Function is init(String is title: 'Suit', Int is width: 800, Int is height: 600, Boolean is decorated: true, Boolean is useVulkan: false){
		:title: title;
		:width: width;
		:height: height;
		:decorated: decorated;
		:useVulkan: useVulkan;
	}

	## Opens the native window; returns `true` on success.
	Function of Boolean is open(){
		return native:open(title: title, width: width, height: height, decorated: decorated, useVulkan: useVulkan);
	}

	Function of Int is nativeDisplayHandle(){
		return native:nativeDisplayHandle();
	}

	Function of Int is nativeSurfaceHandle(){
		return native:nativeSurfaceHandle();
	}

	## Polls/dispatches pending window events; returns `true` while open.
	Function of Boolean is poll(){
		return native:poll();
	}

	## Closes the native window.
	Function is close(){
		native:close();
	}

	## True when the window is currently open.
	Function of Boolean is isOpen(){
		return native:isOpen();
	}

	## Returns the last native windowing error message.
	Function of String is lastError(){
		return native:lastError();
	}

	## Returns the next queued ASCII/key code (`'w'`, `'a'`, `'s'`, `'d'`, `'q'`, `'e'`, `27`), or `0`.
	Function of Int is nextKey(){
		return native:nextKey();
	}

	## Returns the current content width in pixels.
	Function of Int is width(){
		return native:width();
	}

	## Returns the current content height in pixels.
	Function of Int is height(){
		return native:height();
	}

	## Returns the logical point-to-pixel scale factor (1.0 = 1px per pt).
	Function of Float is scaleFactor(){
		return 1.0;
	}

	Function of Int is pointerX(){ return native:pointerX(); }
	Function of Int is pointerY(){ return native:pointerY(); }
	Function of Boolean is pollClick(){ return native:pollClick(); }
	Function of Int is clickX(){ return native:clickX(); }
	Function of Int is clickY(){ return native:clickY(); }
	Function of Boolean is pollRightClick(){ return native:pollRightClick(); }
	Function of Int is rightClickX(){ return native:rightClickX(); }
	Function of Int is rightClickY(){ return native:rightClickY(); }

	## Pops the next raw input event as an `InputEvent` variant (`InputEvent:None` when empty),
	## covering all pointer buttons (left/right/middle/side/extra), pointer motion, scroll axes,
	## keys (press/release), UTF-8 chars, touch events, and enter/focus events.
	Function of InputEvent is pollEvent(){
		if({ evBufAddr == 0 }, { evBufAddr: Mem:alloc(bytes: 20); });
		if({ !native:pollEventRaw(out5I32Addr: evBufAddr) }, { return InputEvent:None; });
		local Int is kind: Mem:loadI32(ptr: evBufAddr, byteOffset: 0);
		local Int is a: Mem:loadI32(ptr: evBufAddr, byteOffset: 4);
		local Int is b: Mem:loadI32(ptr: evBufAddr, byteOffset: 8);
		local Int is c: Mem:loadI32(ptr: evBufAddr, byteOffset: 12);
		local Int is d: Mem:loadI32(ptr: evBufAddr, byteOffset: 16);
		if({ kind == 1 }, { return InputEvent:PointerMotion(x: a, y: b); });
		if({ kind == 2 }, { return InputEvent:PointerButton(button: a, pressed: b != 0, x: c, y: d); });
		if({ kind == 3 }, {
			local Int is dVal: if({ b >= 2147483648 }, { b - 4294967296 }, { b });
			return InputEvent:PointerAxis(axis: a, delta: dVal);
		});
		if({ kind == 4 }, { return InputEvent:Key(key: a, pressed: b != 0, mods: c); });
		if({ kind == 5 }, { return InputEvent:TextChar(codepoint: a, mods: b); });
		if({ kind == 6 }, { return InputEvent:TouchDown(id: a, x: b, y: c); });
		if({ kind == 7 }, { return InputEvent:TouchUp(id: a); });
		if({ kind == 8 }, { return InputEvent:TouchMotion(id: a, x: b, y: c); });
		if({ kind == 9 }, { return InputEvent:TouchCancel; });
		if({ kind == 10 }, { return InputEvent:PointerEnter(entered: a != 0, x: b, y: c); });
		if({ kind == 11 }, { return InputEvent:KeyFocus(focused: a != 0); });
		return InputEvent:None;
	}

	Function is destroy(){
		if({ evBufAddr != 0 }, {
			Mem:free(ptr: evBufAddr);
			evBufAddr: 0;
		});
	}
	Function of Int is pollScrollY(){ return native:pollScrollY(); }
	Function of Int is pollScrollX(){ return native:pollScrollX(); }
	Function of Boolean is pointerDown(){ return native:pointerDown(); }
	Function is setTitle(String is title){ native:setTitle(title: title); }
	Function of Int is nextChar(){ return native:nextChar(); }
	Function of Int is mods(){ return native:mods(); }
	Function is setCursor(Int is kind){ native:setCursor(kind: kind); }
	Function is setMinSize(Int is minW, Int is minH){ native:setMinSize(minW: minW, minH: minH); }
	Function is setAppId(String is appId){ native:setAppId(appId: appId); }

	## Presents [canvas] pixels to the window surface.
	Function of Boolean is present(SuitCanvas is canvas){
		return native:present(pixelsAddr: canvas:pixelsAddr(), width: canvas:width, height: canvas:height);
	}
}
