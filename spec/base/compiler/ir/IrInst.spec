#! Package base:compiler:ir
#! Typed IR instructions for a basic block.

Enum is IrInst {
	namespace: ['base', 'compiler', 'ir'],

	using: [
		['base', 'compiler', 'ir', IrType]
	],

	ConstInt(String is dst, Int is value),
	ConstFloat(String is dst, String is text),
	ConstBool(String is dst, Boolean is value),
	ConstString(String is dst, Int is strId),
	Alloca(String is slot, IrType is ty),
	Load(String is dst, String is slot, IrType is ty),
	Store(String is slot, String is val, IrType is ty),
	BinOp(String is dst, String is op, String is lhs, String is rhs, IrType is ty),
	UnaryOp(String is dst, String is op, String is operand, IrType is ty),
	Cmp(String is dst, String is op, String is lhs, String is rhs, IrType is ty),
	IrCall(String is dst, Boolean is hasDst, IrType is retType, String is callee, Array of IrType is argTypes, Array of String is args),
	IndirectCall(String is dst, Boolean is hasDst, IrType is retType, String is fnPtr, Array of IrType is argTypes, Array of String is args),
	GlobalAddr(String is dst, String is globalName),
	AllocObj(String is dst, String is structName, String is destroyFn),
	FieldPtr(String is dst, String is objPtr, String is structName, Int is fieldIndex),
	IrCast(String is dst, String is val, IrType is fromType, IrType is toType),
	Retain(String is val),
	Release(String is val),
	Ret(Boolean is hasVal, String is val, IrType is ty),
	Br(String is target),
	CondBr(String is cond, String is thenLabel, String is elseLabel)
}
