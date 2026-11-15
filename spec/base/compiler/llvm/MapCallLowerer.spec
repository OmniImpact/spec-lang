#! Package base:compiler:llvm
#! Lowers Map runtime method calls (length, has, set, get) to Spec IR.

Class of CallLowerer is MapCallLowerer{
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
		return 'MapCallLowerer';
	}

	replace Function of Int is order(){
		return 40;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		local String is recvType: call:target:resolvedType;
		if({ recvType != 'Map' && !recvType:startsWith(prefix: 'Map of ') && !recvType:startsWith(prefix: 'Map:') }, {
			return false;
		});
		local String is nm: call:name;
		if({ nm == 'length' }, { return true; });
		if({ nm == 'has' && call:args:length() >= 1 }, { return true; });
		if({ nm == 'set' && call:args:length() >= 2 }, { return true; });
		if({ nm == 'get' && call:args:length() >= 1 }, { return true; });
		return false;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		local String is mRecv: b:lowerExpr(expr: call:target);
		if({ nm == 'length' }, {
			local String is dst: b:nextTmp();
			b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_map_length', argTypes: [IrType:Ptr], args: [mRecv]));
			return dst;
		});
		if({ nm == 'has' }, {
			local NamedArg is na0: call:args:get(index: 0);
			local String is kv: b:lowerExpr(expr: na0:value);
			local String is dst: b:nextTmp();
			b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I1, callee: 'spec_map_has', argTypes: [IrType:Ptr, IrType:Ptr], args: [mRecv, kv]));
			return dst;
		});
		if({ nm == 'set' }, {
			local NamedArg is na0: call:args:get(index: 0);
			local NamedArg is na1: call:args:get(index: 1);
			local String is kv: b:lowerExpr(expr: na0:value);
			local Expression is vvExpr: na1:value;
			local String is vv: b:lowerExpr(expr: vvExpr);
			local IrType is vty: b:irTypeFor(specType: vvExpr:resolvedType);
			local String is vp: vv;
			if({ vty != IrType:Ptr }, {
				vp: b:nextTmp();
				b:emit(inst: IrInst:IrCast(dst: vp, val: vv, fromType: vty, toType: IrType:Ptr));
			});
			b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_map_set', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: [mRecv, kv, vp]));
			return '0';
		});
		if({ nm == 'get' }, {
			local NamedArg is na0: call:args:get(index: 0);
			local String is kv: b:lowerExpr(expr: na0:value);
			local String is defV: 'null';
			if({ call:args:length() >= 2 }, {
				local NamedArg is na1: call:args:get(index: 1);
				local Expression is dvExpr: na1:value;
				local String is dv: b:lowerExpr(expr: dvExpr);
				local IrType is dty: b:irTypeFor(specType: dvExpr:resolvedType);
				if({ dty != IrType:Ptr }, {
					defV: b:nextTmp();
					b:emit(inst: IrInst:IrCast(dst: defV, val: dv, fromType: dty, toType: IrType:Ptr));
				}, {
					defV: dv;
				});
			});
			local String is raw: b:nextTmp();
			b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'spec_map_get', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: [mRecv, kv, defV]));
			local IrType is mrTy: b:irTypeFor(specType: expr:resolvedType);
			if({ mrTy != IrType:Ptr && mrTy != IrType:Void }, {
				local String is casted: b:nextTmp();
				b:emit(inst: IrInst:IrCast(dst: casted, val: raw, fromType: IrType:Ptr, toType: mrTy));
				return casted;
			});
			return raw;
		});
		return '0';
	}
}
