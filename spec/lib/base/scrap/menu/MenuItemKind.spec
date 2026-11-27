#! Package base:scrap
#! Typed menu item kind enum for [MenuItemConfig], [MenuContext], and [Toolbar].

Enum is MenuItemKind{
	replace [String] is namespace: ['base', 'scrap', 'menu'];

	ACTION,
	TOGGLE,
	RADIO
}
