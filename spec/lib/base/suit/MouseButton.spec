#! Package base:suit
#! Linux evdev mouse button codes exposed through `InputEvent:PointerButton`.

Enum of Int is MouseButton{
	replace [String] is namespace: ['base', 'suit'];

	LEFT: 272,
	RIGHT: 273,
	MIDDLE: 274,
	SIDE: 275,
	EXTRA: 276
}
