#! Package theoedit:vm
#! Focus and hover targets for the file manager dialog.

Enum is FileManagerFocus{
	replace [String] is namespace: ['theoedit', 'util'];
	NONE,
	LIST,
	INPUT,
	OK,
	CANCEL
}
