#! Package base:compiler:ir
#! Backend-agnostic scalar/pointer IR types.

Enum is IrType {
	replace [String] is namespace: ['base', 'compiler', 'ir'];

	Void,
	I1,
	I8,
	I16,
	I32,
	I64,
	I128,
	F32,
	F64,
	Ptr
}
