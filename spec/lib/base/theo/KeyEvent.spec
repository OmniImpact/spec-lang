#! Package base:theo
#! Decoded keyboard input event for Theo frames and widgets.

Class is KeyEvent{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', [KeyKind, KeyAction]]
	];

	KeyKind is kind: KeyKind:NONE;
	KeyAction is action: KeyAction:PRESS;
	String is key: '';
	Boolean is ctrl: false;
	Boolean is alt: false;

	replace Function is init(
		KeyKind is kind: KeyKind:NONE,
		String is key: '',
		Boolean is ctrl: false,
		Boolean is alt: false,
		KeyAction is action: KeyAction:PRESS
	){
		:kind: kind;
		:action: action;
		:key: key;
		:ctrl: ctrl;
		:alt: alt;
	}

	Function of Boolean is isPress(){ action == KeyAction:PRESS }
	Function of Boolean is isRepeat(){ action == KeyAction:REPEAT }
	Function of Boolean is isRelease(){ action == KeyAction:RELEASE }

	Function of Boolean is isNone(){ kind == KeyKind:NONE }
	Function of Boolean is isChar(){ kind == KeyKind:CHAR }
	Function of Boolean is isEnter(){ kind == KeyKind:ENTER }
	Function of Boolean is isEsc(){ kind == KeyKind:ESC }
	Function of Boolean is isTab(){ kind == KeyKind:TAB }
	Function of Boolean is isBackTab(){ kind == KeyKind:BACKTAB }
	Function of Boolean is isBackspace(){ kind == KeyKind:BACKSPACE }
	Function of Boolean is isDelete(){ kind == KeyKind:DELETE }
	Function of Boolean is isUp(){ kind == KeyKind:UP }
	Function of Boolean is isDown(){ kind == KeyKind:DOWN }
	Function of Boolean is isLeft(){ kind == KeyKind:LEFT }
	Function of Boolean is isRight(){ kind == KeyKind:RIGHT }
	Function of Boolean is isHome(){ kind == KeyKind:HOME }
	Function of Boolean is isEnd(){ kind == KeyKind:END }
	Function of Boolean is isPageUp(){ kind == KeyKind:PAGE_UP }
	Function of Boolean is isPageDown(){ kind == KeyKind:PAGE_DOWN }
	Function of Boolean is isMouse(){ kind == KeyKind:MOUSE }
}
