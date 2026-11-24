#! Package base:compiler:ir
#! Typed IR instructions for a basic block.

Enum is IrInst {
	replace [String] is namespace: ['base', 'compiler', 'ir'];

	replace [[String]] is using: [
		['base', 'compiler', 'ir', IrType]
	];

	ConstInt(String is dst, Int is value),
	ConstIntTy(String is dst, Int is value, IrType is ty),
	ConstFloat(String is dst, String is text),
	ConstFloat32(String is dst, String is text),
	ConstBool(String is dst, Boolean is value),
	ConstString(String is dst, Int is strId),
	Alloca(String is slot, IrType is ty),
	Load(String is dst, String is slot, IrType is ty),
	Store(String is slot, String is val, IrType is ty),
	BinOp(String is dst, String is op, String is lhs, String is rhs, IrType is ty),
	UnaryOp(String is dst, String is op, String is operand, IrType is ty),
	Cmp(String is dst, String is op, String is lhs, String is rhs, IrType is ty),
	IrCall(String is dst, Boolean is hasDst, IrType is retType, String is callee, [IrType] is argTypes, [String] is args),
	IndirectCall(String is dst, Boolean is hasDst, IrType is retType, String is fnPtr, [IrType] is argTypes, [String] is args),
	GlobalAddr(String is dst, String is globalName),
	AllocObj(String is dst, String is structName, String is destroyFn),
	FieldPtr(String is dst, String is objPtr, String is structName, Int is fieldIndex),
	PtrElem(String is dst, String is basePtr, Int is index),
	IrCast(String is dst, String is val, IrType is fromType, IrType is toType),
	IrCastU(String is dst, String is val, IrType is fromType, IrType is toType),
	Retain(String is val),
	Release(String is val),
	Ret(Boolean is hasVal, String is val, IrType is ty),
	Br(String is target),
	CondBr(String is cond, String is thenLabel, String is elseLabel)
}
