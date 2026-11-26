#! Package base:suit
#! Sum-type enum of raw native input events popped from `SuitWindow:pollEvent()`.

Enum is InputEvent{
	replace [String] is namespace: ['base', 'suit'];

	None,
	PointerMotion(Int is x, Int is y),
	PointerButton(Int is button, Boolean is pressed, Int is x, Int is y),
	PointerAxis(Int is axis, Int is delta),
	Key(Int is key, Boolean is pressed, Int is mods),
	TextChar(Int is codepoint, Int is mods),
	TouchDown(Int is id, Int is x, Int is y),
	TouchUp(Int is id),
	TouchMotion(Int is id, Int is x, Int is y),
	TouchCancel,
	PointerEnter(Boolean is entered, Int is x, Int is y),
	KeyFocus(Boolean is focused)
}
