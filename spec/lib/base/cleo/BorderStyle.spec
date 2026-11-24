#! Package base:cleo
#! Border and divider line styles for Cleo frames.

Enum of String is BorderStyle {
	replace [String] is namespace: ['base', 'cleo'];
	NONE: 'NONE',
	ASCII: 'ASCII',
	THIN: 'THIN',
	THICK: 'THICK',
	DOUBLE: 'DOUBLE',
	ROUNDED: 'ROUNDED',
	DASHED: 'DASHED'
}
