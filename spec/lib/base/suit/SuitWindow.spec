#! Package base:suit
#! Suit (Spec UI Toolkit) native window abstraction.

Class is SuitWindow{
	replace [String] is namespace: ['base', 'suit'];

	merge [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'struct', Array],
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

	## Dispatches pending window events, waiting up to [timeoutMs] ms for input.
	Function of Boolean is pollTimeout(Int is timeoutMs){
		return native:pollTimeout(timeoutMs: timeoutMs);
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

	held Array of Function is eventBuilders: Array([
		local Function of InputEvent(Int is _a, Int is _b, Int is _c, Int is _d){ InputEvent:None },
		local Function of InputEvent(Int is a, Int is b, Int is _c, Int is _d){ InputEvent:PointerMotion(x: a, y: b) },
		local Function of InputEvent(Int is a, Int is b, Int is c, Int is d){ InputEvent:PointerButton(button: a, pressed: b != 0, x: c, y: d) },
		local Function of InputEvent(Int is a, Int is b, Int is _c, Int is _d){ InputEvent:PointerAxis(axis: a, delta: b) },
		local Function of InputEvent(Int is a, Int is b, Int is c, Int is _d){ InputEvent:Key(key: a, pressed: b != 0, mods: c) },
		local Function of InputEvent(Int is a, Int is b, Int is _c, Int is _d){ InputEvent:TextChar(codepoint: a, mods: b) },
		local Function of InputEvent(Int is a, Int is b, Int is c, Int is _d){ InputEvent:TouchDown(id: a, x: b, y: c) },
		local Function of InputEvent(Int is a, Int is _b, Int is _c, Int is _d){ InputEvent:TouchUp(id: a) },
		local Function of InputEvent(Int is a, Int is b, Int is c, Int is _d){ InputEvent:TouchMotion(id: a, x: b, y: c) },
		local Function of InputEvent(Int is _a, Int is _b, Int is _c, Int is _d){ InputEvent:TouchCancel },
		local Function of InputEvent(Int is a, Int is b, Int is c, Int is _d){ InputEvent:PointerEnter(entered: a != 0, x: b, y: c) },
		local Function of InputEvent(Int is a, Int is _b, Int is _c, Int is _d){ InputEvent:KeyFocus(focused: a != 0) }
	]);

	## Pops the next raw input event as an `InputEvent` variant (`InputEvent:None` when empty),
	## covering all pointer buttons (left/right/middle/side/extra), pointer motion, scroll axes,
	## keys (press/release), UTF-8 chars, touch events, and enter/focus events.
	Function of InputEvent is pollEvent(){
		if({ evBufAddr == 0 }, { evBufAddr: Mem:alloc(bytes: 20); });
		if({ !native:pollEventRaw(out5I32Addr: evBufAddr) }, { return InputEvent:None; });
		local Int is kind: Mem:loadI32(ptr: evBufAddr, byteOffset: 0);
		if({ kind < 0 || kind >= SuitWindow:eventBuilders:length() }, { return InputEvent:None; });
		local Function is ctor: SuitWindow:eventBuilders:get(index: kind);
		local Int is rawB: Mem:loadI32(ptr: evBufAddr, byteOffset: 8);
		local Int is bVal: if({ kind == 3 && rawB >= 2147483648 }, { rawB - 4294967296 }, { rawB });
		return ctor(
			Mem:loadI32(ptr: evBufAddr, byteOffset: 4),
			bVal,
			Mem:loadI32(ptr: evBufAddr, byteOffset: 12),
			Mem:loadI32(ptr: evBufAddr, byteOffset: 16)
		) as InputEvent;
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
	Function is setIcon(Int is pixelsAddr, Int is width, Int is height){ native:setIcon(pixelsAddr: pixelsAddr, width: width, height: height); }
	Function is setClipboard(String is text){ native:setClipboard(text: text); }
	Function of String is getClipboard(){ return native:getClipboard(); }

	## Presents [canvas] pixels to the window surface.
	Function of Boolean is present(SuitCanvas is canvas){
		return native:present(pixelsAddr: canvas:pixelsAddr(), width: canvas:width, height: canvas:height);
	}
}
