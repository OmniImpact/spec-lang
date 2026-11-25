#! Package base:suit
#! Suit (Spec UI Toolkit) native window abstraction.

Class is SuitWindow{
	replace [String] is namespace: ['base', 'suit'];

	merge [[String]] is using: [
		['base', 'sys', Window]
	];

	String is title: 'Suit';
	Int is width: 800;
	Int is height: 600;
	Boolean is decorated: true;
	Window is native: Window();

	replace Function is init(String is title: 'Suit', Int is width: 800, Int is height: 600, Boolean is decorated: true){
		:title: title;
		:width: width;
		:height: height;
		:decorated: decorated;
	}

	## Opens the native window; returns `true` on success.
	Function of Boolean is open(){
		return native:open(title: title, width: width, height: height, decorated: decorated);
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
}
