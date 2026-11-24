#! Package base:compiler:ast
#! The primitive type names, as an enum.
##
## Primitives are NOT classes: they have no ClassInfo, no members, and no
## runtime identity — they are the builtin type vocabulary of the language,
## and this enum is the single authoritative list. Class registries and
## visibility machinery never contain them. Canonical spellings only.
## [NONE] marks "not a primitive".

Enum of String is Primitive {
	replace [String] is namespace: ['base', 'compiler', 'ast'];
	NONE: '',
	INT: 'Int',
	INT8: 'Int8',
	INT16: 'Int16',
	INT32: 'Int32',
	INT128: 'Int128',
	ISIZE: 'ISize',
	FLOAT: 'Float',
	FLOAT32: 'Float32',
	BOOLEAN: 'Boolean',
	STRING: 'String',
	BYTE: 'Byte',
	UINT8: 'UInt8',
	UINT16: 'UInt16',
	UINT32: 'UInt32',
	UINT64: 'UInt64',
	UINT128: 'UInt128',
	USIZE: 'USize',
	RUNE: 'Rune',
	RAWPTR: 'RawPtr',
	VOID: 'Void',
	ANY: 'Any',
	FUNCTION: 'Function'
}
