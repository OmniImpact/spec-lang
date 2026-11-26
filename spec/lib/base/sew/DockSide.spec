#! Package base:sew
#! Edge/docking side enum for bars, tab strips, and scrollbars.

Enum is DockSide{
	replace [String] is namespace: ['base', 'sew'];

	TOP,
	BOTTOM,
	LEFT,
	RIGHT,
	NONE
}