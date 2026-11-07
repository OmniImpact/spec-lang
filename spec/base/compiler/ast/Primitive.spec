#! Package base:compiler:ast
#! The primitive type names, as an enum.
##
## Primitives are NOT classes: they have no ClassInfo, no members, and no
## runtime identity — they are the builtin type vocabulary of the language,
## and this enum is the single authoritative list. Class registries and
## visibility machinery never contain them. Canonical spellings only.
## [NONE] marks "not a primitive".

Enum of String is Primitive {
	namespace: ['base', 'compiler', 'ast'],
	NONE: '',
	INT: 'Int',
	FLOAT: 'Float',
	BOOLEAN: 'Boolean',
	STRING: 'String',
	BYTE: 'Byte',
	VOID: 'Void',
	ANY: 'Any',
	FUNCTION: 'Function'
}
