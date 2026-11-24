#! Package base:compiler:ast
#! The class-member categories.

Enum of String is MemberKind {
	replace [String] is namespace: ['base', 'compiler', 'ast'];
	METHOD: 'METHOD',
	FIELD: 'FIELD',
	CLASS: 'CLASS',
	ENUM: 'ENUM'
}
