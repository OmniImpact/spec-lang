#! Package base:fabric
#! Typed border and divider stroke style enum (replacing raw style strings).

Enum of String is StrokeStyle{
	replace [String] is namespace: ['base', 'fabric'];

	NONE: 'none',
	SINGLE: 'single',
	DOUBLE: 'double',
	BEVEL: 'bevel',
	GROOVE: 'groove',
	INSET: 'inset',
	OUTSET: 'outset'
}
