#! Package base:theo
#! Decoded mouse input event for Theo frames and widgets.

Class is MouseEvent{
	namespace: ['base', 'theo'];

	String is kind: 'none';
	Int is x: 0;
	Int is y: 0;
	Int is button: 0;
	Boolean is ctrl: false;
	Boolean is alt: false;
	Boolean is shift: false;

	replace Function is init(
		String is kind: 'none',
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

	Function of Boolean is isNone(){ return kind == 'none'; }
	Function of Boolean is isPress(){ return kind == 'press'; }
	Function of Boolean is isRelease(){ return kind == 'release'; }
	Function of Boolean is isMove(){ return kind == 'move'; }
	Function of Boolean is isWheelUp(){ return kind == 'wheelUp'; }
	Function of Boolean is isWheelDown(){ return kind == 'wheelDown'; }
	Function of Boolean is isLeftPress(){ return kind == 'press' && button == 0; }
}