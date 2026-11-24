#! Package base:theo
#! Decoded mouse input event for Theo frames and widgets.

Class is MouseEvent{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', MouseKind]
	];

	MouseKind is kind: MouseKind:NONE;
	Int is x: 0;
	Int is y: 0;
	Int is button: 0;
	Boolean is ctrl: false;
	Boolean is alt: false;
	Boolean is shift: false;

	replace Function is init(
		MouseKind is kind: MouseKind:NONE,
		Int is x: 0,
		Int is y: 0,
		Int is button: 0,
		Boolean is ctrl: false,
		Boolean is alt: false,
		Boolean is shift: false
	){
		:kind: kind;
		:x: x;
		:y: y;
		:button: button;
		:ctrl: ctrl;
		:alt: alt;
		:shift: shift;
	}

	Function of Boolean is isNone(){ kind == MouseKind:NONE }
	Function of Boolean is isPress(){ kind == MouseKind:PRESS }
	Function of Boolean is isRelease(){ kind == MouseKind:RELEASE }
	Function of Boolean is isMove(){ kind == MouseKind:MOVE }
	Function of Boolean is isWheelUp(){ kind == MouseKind:WHEEL_UP }
	Function of Boolean is isWheelDown(){ kind == MouseKind:WHEEL_DOWN }
	Function of Boolean is isLeftPress(){ kind == MouseKind:PRESS && button == 0 }
}