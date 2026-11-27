#! Package base:sew
#! Standard pointer cursor shapes mapped to native windowing cursors.

Enum is CursorShape{
	replace [String] is namespace: ['base', 'sew'];

	DEFAULT,
	TEXT,
	POINTER,
	EW_RESIZE,
	NS_RESIZE
}
