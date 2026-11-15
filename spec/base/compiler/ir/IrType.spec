#! Package base:compiler:ir
#! Backend-agnostic scalar/pointer IR types.

Enum is IrType {
	namespace: ['base', 'compiler', 'ir'],

	Void,
	I1,
	I64,
	F64,
	Ptr
}
