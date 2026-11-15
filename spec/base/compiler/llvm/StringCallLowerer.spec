#! Package base:compiler:llvm
#! Lowers String runtime method calls (length, contains, substring) to Spec IR.

Class of CallLowerer is StringCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', CallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(){
		return;
	}

	replace Function of String is name(){
		return 'StringCallLowerer';
	}

	replace Function of Int is order(){
		return 20;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		if({ call:target:resolvedType != 'String' }, { return false; });
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: call:name, when: [
			'length': { ok: true; },
			'contains': { ok: argc >= 1; },
			'substring': { ok: argc >= 2; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is sRecv: b:lowerExpr(expr: call:target);
		local String is res: '0';
		match(on: call:name, when: [
			'length': {
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_string_length', argTypes: [IrType:Ptr], args: [sRecv]));
				res: dst;
			},
			'contains': {
				local NamedArg is na0: call:args:get(index: 0);
				local String is needle: b:lowerExpr(expr: na0:value);
				local String is idxTmp: b:nextTmp();
				local String is negOne: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: negOne, value: -1));
				b:emit(inst: IrInst:IrCall(dst: idxTmp, hasDst: true, retType: IrType:I64, callee: 'spec_string_index_of', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64], args: [sRecv, needle, negOne]));
				local String is zeroTmp: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: zeroTmp, value: 0));
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:Cmp(dst: dst, op: '>=', lhs: idxTmp, rhs: zeroTmp, ty: IrType:I64));
				res: dst;
			},
			'substring': {
				local NamedArg is na0: call:args:get(index: 0);
				local NamedArg is na1: call:args:get(index: 1);
				local String is st: b:lowerExpr(expr: na0:value);
				local String is en: b:lowerExpr(expr: na1:value);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_substring', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [sRecv, st, en]));
				res: dst;
			}
		]);
		return res;
	}
}
