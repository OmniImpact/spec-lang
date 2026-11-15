#! Package base:compiler:llvm
#! Lowers Array runtime method calls (length, add, get, set) to Spec IR.

Class of CallLowerer is ArrayCallLowerer{
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
		return 'ArrayCallLowerer';
	}

	replace Function of Int is order(){
		return 30;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		local String is recvType: call:target:resolvedType;
		if({ recvType != 'Array' && !recvType:startsWith(prefix: 'Array of ') && !recvType:startsWith(prefix: 'Array:') }, {
			return false;
		});
		local String is nm: call:name;
		if({ nm == 'length' }, { return true; });
		if({ nm == 'add' && call:args:length() >= 1 }, { return true; });
		if({ nm == 'get' && call:args:length() >= 1 }, { return true; });
		if({ nm == 'set' && call:args:length() >= 2 }, { return true; });
		return false;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		local String is aRecv: b:lowerExpr(expr: call:target);
		if({ nm == 'length' }, {
			local String is dst: b:nextTmp();
			b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_array_length', argTypes: [IrType:Ptr], args: [aRecv]));
			return dst;
		});
		if({ nm == 'add' }, {
			local NamedArg is na0: call:args:get(index: 0);
			local Expression is ivExpr: na0:value;
			local String is iv: b:lowerExpr(expr: ivExpr);
			local IrType is ity: b:irTypeFor(specType: ivExpr:resolvedType);
			local String is ip: iv;
			if({ ity != IrType:Ptr }, {
				ip: b:nextTmp();
				b:emit(inst: IrInst:IrCast(dst: ip, val: iv, fromType: ity, toType: IrType:Ptr));
			});
			b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_array_add', argTypes: [IrType:Ptr, IrType:Ptr], args: [aRecv, ip]));
			return '0';
		});
		if({ nm == 'get' }, {
			local NamedArg is na0: call:args:get(index: 0);
			local String is idxV: b:lowerExpr(expr: na0:value);
			local String is raw: b:nextTmp();
			b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'spec_array_get', argTypes: [IrType:Ptr, IrType:I64], args: [aRecv, idxV]));
			local IrType is grTy: b:irTypeFor(specType: expr:resolvedType);
			if({ grTy != IrType:Ptr && grTy != IrType:Void }, {
				local String is casted: b:nextTmp();
				b:emit(inst: IrInst:IrCast(dst: casted, val: raw, fromType: IrType:Ptr, toType: grTy));
				return casted;
			});
			return raw;
		});
		if({ nm == 'set' }, {
			local NamedArg is na0: call:args:get(index: 0);
			local NamedArg is na1: call:args:get(index: 1);
			local String is idxV: b:lowerExpr(expr: na0:value);
			local Expression is ivExpr: na1:value;
			local String is iv: b:lowerExpr(expr: ivExpr);
			local IrType is ity: b:irTypeFor(specType: ivExpr:resolvedType);
			local String is ip: iv;
			if({ ity != IrType:Ptr }, {
				ip: b:nextTmp();
				b:emit(inst: IrInst:IrCast(dst: ip, val: iv, fromType: ity, toType: IrType:Ptr));
			});
			b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_array_set', argTypes: [IrType:Ptr, IrType:I64, IrType:Ptr], args: [aRecv, idxV, ip]));
			return '0';
		});
		return '0';
	}
}
