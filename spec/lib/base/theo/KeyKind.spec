#! Package base:theo
#! Kinds of decoded keyboard input carried by [KeyEvent].

Enum of String is KeyKind {
	replace [String] is namespace: ['base', 'theo'];
	NONE: 'none',
	CHAR: 'char',
	ENTER: 'enter',
	ESC: 'esc',
	TAB: 'tab',
	BACKTAB: 'backtab',
	BACKSPACE: 'backspace',
	DELETE: 'delete',
	UP: 'up',
	DOWN: 'down',
	LEFT: 'left',
	RIGHT: 'right',
	HOME: 'home',
	END: 'end',
	PAGE_UP: 'pageUp',
	PAGE_DOWN: 'pageDown',
	MOUSE: 'mouse'
}
