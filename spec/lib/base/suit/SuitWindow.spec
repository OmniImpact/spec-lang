#! Package base:suit
#! Suit (Spec UI Toolkit) native window abstraction.

Class is SuitWindow{
	replace [String] is namespace: ['base', 'suit'];

	merge [[String]] is using: [
		['base', 'suit', SuitCanvas],
		['base', 'sys', Window]
	];

	String is title: 'Suit';
	Int is width: 800;
	Int is height: 600;
	Boolean is decorated: true;
	Boolean is useVulkan: false;
	Window is native: Window();

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

	## Presents [canvas] pixels to the window surface.
	Function of Boolean is present(SuitCanvas is canvas){
		return native:present(pixelsAddr: canvas:pixelsAddr(), width: canvas:width, height: canvas:height);
	}
}
