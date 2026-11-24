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

	Function of Boolean is isNone(){ return kind == 'none'; }
	Function of Boolean is isChar(){ return kind == 'char'; }
	Function of Boolean is isEnter(){ return kind == 'enter'; }
	Function of Boolean is isEsc(){ return kind == 'esc'; }
	Function of Boolean is isTab(){ return kind == 'tab'; }
	Function of Boolean is isBackTab(){ return kind == 'backtab'; }
	Function of Boolean is isBackspace(){ return kind == 'backspace'; }
	Function of Boolean is isDelete(){ return kind == 'delete'; }
	Function of Boolean is isUp(){ return kind == 'up'; }
	Function of Boolean is isDown(){ return kind == 'down'; }
	Function of Boolean is isLeft(){ return kind == 'left'; }
	Function of Boolean is isRight(){ return kind == 'right'; }
	Function of Boolean is isHome(){ return kind == 'home'; }
	Function of Boolean is isEnd(){ return kind == 'end'; }
	Function of Boolean is isPageUp(){ return kind == 'pageUp'; }
	Function of Boolean is isPageDown(){ return kind == 'pageDown'; }
	Function of Boolean is isMouse(){ return kind == 'mouse'; }
}
