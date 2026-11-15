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
		['base', 'compiler', 'ir', IrBlock],
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
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: call:name, when: [
			'length': { ok: true; },
			['add', 'get', 'each']: { ok: argc >= 1; },
			'set': { ok: argc >= 2; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is aRecv: b:lowerExpr(expr: call:target);
		local String is res: '0';
		match(on: call:name, when: [
			'length': {
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_array_length', argTypes: [IrType:Ptr], args: [aRecv]));
				res: dst;
			},
			'add': {
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
			},
			'get': {
				local NamedArg is na0: call:args:get(index: 0);
				local String is idxV: b:lowerExpr(expr: na0:value);
				local String is raw: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'spec_array_get', argTypes: [IrType:Ptr, IrType:I64], args: [aRecv, idxV]));
				local IrType is grTy: b:irTypeFor(specType: expr:resolvedType);
				if({ grTy != IrType:Ptr && grTy != IrType:Void }, {
					local String is casted: b:nextTmp();
					b:emit(inst: IrInst:IrCast(dst: casted, val: raw, fromType: IrType:Ptr, toType: grTy));
					res: casted;
				}, {
					res: raw;
				});
			},
			'set': {
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
			},
			'each': {
				local NamedArg is na0: call:args:get(index: 0);
				local String is cObj: b:lowerExpr(expr: na0:value);
				local String is fnPtrAddr: b:nextTmp();
				b:emit(inst: IrInst:FieldPtr(dst: fnPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 0));
				local String is fnPtrVal: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: fnPtrVal, slot: fnPtrAddr, ty: IrType:Ptr));
				local String is envPtrAddr: b:nextTmp();
				b:emit(inst: IrInst:FieldPtr(dst: envPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 1));
				local String is envVal: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: envVal, slot: envPtrAddr, ty: IrType:Ptr));

				local String is recvType: call:target:resolvedType;
				local IrType is elemTy: IrType:Ptr;
				if({ recvType:startsWith(prefix: 'Array:') }, {
					elemTy: b:irTypeFor(specType: recvType:substring(start: 6, end: recvType:length()));
				}, {
					if({ recvType:startsWith(prefix: 'Array of ') }, {
						elemTy: b:irTypeFor(specType: recvType:substring(start: 9, end: recvType:length()));
					});
				});
				if({ elemTy == IrType:Void }, { elemTy: IrType:Ptr; });

				local String is lenV: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: lenV, hasDst: true, retType: IrType:I64, callee: 'spec_array_length', argTypes: [IrType:Ptr], args: [aRecv]));
				local String is idxSlot: '%each_i_' . (b:nextTmp());
				idxSlot: '%each_i_' . (b:tmpCounter as String);
				b:emit(inst: IrInst:Alloca(slot: idxSlot, ty: IrType:I64));
				local String is zeroV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: zeroV, value: 0));
				b:emit(inst: IrInst:Store(slot: idxSlot, val: zeroV, ty: IrType:I64));

				local String is hdrLbl: b:nextLabel(prefix: 'each_hdr');
				local String is bodyLbl: b:nextLabel(prefix: 'each_body');
				local String is endLbl: b:nextLabel(prefix: 'each_end');
				b:terminate(inst: IrInst:Br(target: hdrLbl));

				local IrBlock is hdrBlk: b:curFn:addBlock(label: hdrLbl);
				b:switchBlock(blk: hdrBlk);
				local String is curI: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: curI, slot: idxSlot, ty: IrType:I64));
				local String is condV: b:nextTmp();
				b:emit(inst: IrInst:Cmp(dst: condV, op: '<', lhs: curI, rhs: lenV, ty: IrType:I64));
				b:terminate(inst: IrInst:CondBr(cond: condV, thenLabel: bodyLbl, elseLabel: endLbl));

				local IrBlock is bodyBlk: b:curFn:addBlock(label: bodyLbl);
				b:switchBlock(blk: bodyBlk);
				local String is raw: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'spec_array_get', argTypes: [IrType:Ptr, IrType:I64], args: [aRecv, curI]));
				local String is elemV: raw;
				if({ elemTy != IrType:Ptr }, {
					elemV: b:nextTmp();
					b:emit(inst: IrInst:IrCast(dst: elemV, val: raw, fromType: IrType:Ptr, toType: elemTy));
				});
				b:emit(inst: IrInst:IndirectCall(dst: '', hasDst: false, retType: IrType:Void, fnPtr: fnPtrVal, argTypes: [IrType:Ptr, elemTy], args: [envVal, elemV]));
				local String is oneV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: oneV, value: 1));
				local String is nextI: b:nextTmp();
				b:emit(inst: IrInst:BinOp(dst: nextI, op: '+', lhs: curI, rhs: oneV, ty: IrType:I64));
				b:emit(inst: IrInst:Store(slot: idxSlot, val: nextI, ty: IrType:I64));
				b:terminate(inst: IrInst:Br(target: hdrLbl));

				local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
				b:switchBlock(blk: endBlk);
			}
		]);
		return res;
	}
}
