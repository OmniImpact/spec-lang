#! Package base:fabric
#! Standard typographic roles for headers, body copy, captions, and monospaced code labels.

Enum is TextStyle{
	replace [String] is namespace: ['base', 'fabric'];

	BODY,
	DISPLAY,
	H1,
	H2,
	H3,
	SUBTITLE,
	CAPTION,
	OVERLINE,
	CODE
}
