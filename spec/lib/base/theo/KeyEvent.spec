#! Package base:theo
#! Decoded keyboard input event for Theo frames and widgets.

Class is KeyEvent{
	replace [String] is namespace: ['base', 'theo'];

	String is kind: 'none';
	String is key: '';
	Boolean is ctrl: false;
	Boolean is alt: false;

	replace Function is init(String is kind: 'none', String is key: '', Boolean is ctrl: false, Boolean is alt: false){
		:kind: kind;
		:key: key;
		:ctrl: ctrl;
		:alt: alt;
	}

	Function of Boolean is isNone(){ kind == 'none' }
	Function of Boolean is isChar(){ kind == 'char' }
	Function of Boolean is isEnter(){ kind == 'enter' }
	Function of Boolean is isEsc(){ kind == 'esc' }
	Function of Boolean is isTab(){ kind == 'tab' }
	Function of Boolean is isBackTab(){ kind == 'backtab' }
	Function of Boolean is isBackspace(){ kind == 'backspace' }
	Function of Boolean is isDelete(){ kind == 'delete' }
	Function of Boolean is isUp(){ kind == 'up' }
	Function of Boolean is isDown(){ kind == 'down' }
	Function of Boolean is isLeft(){ kind == 'left' }
	Function of Boolean is isRight(){ kind == 'right' }
	Function of Boolean is isHome(){ kind == 'home' }
	Function of Boolean is isEnd(){ kind == 'end' }
	Function of Boolean is isPageUp(){ kind == 'pageUp' }
	Function of Boolean is isPageDown(){ kind == 'pageDown' }
	Function of Boolean is isMouse(){ kind == 'mouse' }
}
