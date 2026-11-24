#! Package theoedit:util
#! Active message/prompt mode for the editor.

Enum is EditorMessageMode{
	replace [String] is namespace: ['theoedit', 'util'];
	NONE,
	CONFIRM_QUIT,
	CONFIRM_OPEN
}
