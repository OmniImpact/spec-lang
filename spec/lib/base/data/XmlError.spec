#! Package base:data
#! Error variants for XML parsing failures (`SpecError of XmlError`).

Enum is XmlError {
	replace [String] is namespace: ['base', 'data'];

	SYNTAX_ERROR
}
