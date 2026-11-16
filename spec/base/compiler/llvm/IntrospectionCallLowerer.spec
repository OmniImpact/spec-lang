#! Package base:compiler:llvm
#! Lowers Introspection sysinternal calls to Spec IR.

Class of SysinternalCallLowerer is IntrospectionCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', SysinternalCallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'compiler', 'ir', IrBlock],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(){
		return;
	}

	replace Function of String is name(){
		return 'IntrospectionCallLowerer';
	}

	replace Function of Int is order(){
		return 47;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		if({ call:name == 'typeName' && call:args:length() == 0 }, { return true; });
		local String is r: self:receiverName(call: call);
		if({ r == 'Box' }, {
			if({ call:name == 'boxNew' || call:name == 'boxGet' || call:name == 'boxSet' || call:name == 'boxToString' }, { return true; });
			return false;
		});
		if({ r == 'Reflection' }, {
			if({ call:name == 'init' || call:name == 'class' || call:name == 'method' }, { return true; });
			return false;
		});
		if({ r != '' && r != 'Introspection' }, { return false; });
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: call:name, when: [
			'init': { ok: r == 'Introspection'; },
			'classNames': { ok: true; },
			['objectHash', 'heldCount', 'heldIndexOf', 'classSourceFile', 'methodNames', 'functions', 'instantiate', 'instantiateSubclasses', 'typeIdentity']: { ok: argc >= 1; },
			['heldName', 'hasHeld', 'hasMethod', 'extendsClass', 'classExtends', 'invokeVoid', 'invokeVoidByName']: { ok: argc >= 2; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is res: '0';
		local String is r: self:receiverName(call: call);
		if({ r == 'Reflection' }, {
			if({ call:name == 'init' }, { return 'null'; });
			if({ call:name == 'class' }, {
				local String is dst: b:nextTmp();
				local Int is sid: b:mod:internStringLiteral(value: b:currentClass);
				b:emit(inst: IrInst:ConstString(dst: dst, strId: sid));
				return dst;
			});
			if({ call:name == 'method' }, {
				local String is dst: b:nextTmp();
				local Int is sid: b:mod:internStringLiteral(value: b:currentMethod);
				b:emit(inst: IrInst:ConstString(dst: dst, strId: sid));
				return dst;
			});
		});
		match(on: call:name, when: [
			'init': { res: 'null'; },
			'classNames': { res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_class_names', argTypes: [], args: []); },
			'objectHash': {
				local String is o: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_object_hash', argTypes: [IrType:Ptr], args: [o]);
			},
			'heldCount': {
				local String is o: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_held_count', argTypes: [IrType:Ptr], args: [o]);
			},
			'heldIndexOf': {
				local String is o: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_held_index_of', argTypes: [IrType:Ptr], args: [o]);
			},
			'heldName': {
				local String is o: self:lowerArg(b: b, call: call, idx: 0);
				local String is idx: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_held_name', argTypes: [IrType:Ptr, IrType:I64], args: [o, idx]);
			},
			'hasHeld': {
				local String is o: self:lowerArg(b: b, call: call, idx: 0);
				local String is nm: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_has_held', argTypes: [IrType:Ptr, IrType:Ptr], args: [o, nm]);
			},
			'classSourceFile': {
				local String is cn: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_class_source_file', argTypes: [IrType:Ptr], args: [cn]);
			},
			'methodNames': {
				local String is cn: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_method_names', argTypes: [IrType:Ptr], args: [cn]);
			},
			'functions': {
				local String is cn: self:lowerArg(b: b, call: call, idx: 0);
				local String is names: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_method_names', argTypes: [IrType:Ptr], args: [cn]);
				local String is out: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_array_new', argTypes: [], args: []);
				b:emitClaimPool(val: out);
				local String is lenV: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_array_length', argTypes: [IrType:Ptr], args: [names]);
				local String is idxSlot: '%ifn_i_' . (b:nextTmp());
				idxSlot: '%ifn_i_' . (b:tmpCounter as String);
				b:emit(inst: IrInst:Alloca(slot: idxSlot, ty: IrType:I64));
				local String is zeroV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: zeroV, value: 0));
				b:emit(inst: IrInst:Store(slot: idxSlot, val: zeroV, ty: IrType:I64));
				local String is hdrLbl: b:nextLabel(prefix: 'ifn_hdr');
				local String is bodyLbl: b:nextLabel(prefix: 'ifn_body');
				local String is endLbl: b:nextLabel(prefix: 'ifn_end');
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
				local String is mName: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: mName, hasDst: true, retType: IrType:Ptr, callee: 'spec_array_get', argTypes: [IrType:Ptr, IrType:I64], args: [names, curI]));
				local String is pArr: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_array_new', argTypes: [], args: []);
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_array_add', argTypes: [IrType:Ptr, IrType:Ptr], args: [pArr, cn]));
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_array_add', argTypes: [IrType:Ptr, IrType:Ptr], args: [pArr, mName]));
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_array_add', argTypes: [IrType:Ptr, IrType:Ptr], args: [out, pArr]));
				local String is oneV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: oneV, value: 1));
				local String is nextI: b:nextTmp();
				b:emit(inst: IrInst:BinOp(dst: nextI, op: '+', lhs: curI, rhs: oneV, ty: IrType:I64));
				b:emit(inst: IrInst:Store(slot: idxSlot, val: nextI, ty: IrType:I64));
				b:terminate(inst: IrInst:Br(target: hdrLbl));
				local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
				b:switchBlock(blk: endBlk);
				res: out;
			},
			'instantiateSubclasses': {
				local String is bn: self:lowerArg(b: b, call: call, idx: 0);
				local String is names: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_class_names', argTypes: [], args: []);
				local String is found: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_array_new', argTypes: [], args: []);
				b:emitClaimPool(val: found);
				local String is lenV: self:emitSysCall(b: b, retType: IrType:I64, callee: 'spec_array_length', argTypes: [IrType:Ptr], args: [names]);
				local String is idxSlot: '%isub_i_' . (b:nextTmp());
				idxSlot: '%isub_i_' . (b:tmpCounter as String);
				b:emit(inst: IrInst:Alloca(slot: idxSlot, ty: IrType:I64));
				local String is zeroV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: zeroV, value: 0));
				b:emit(inst: IrInst:Store(slot: idxSlot, val: zeroV, ty: IrType:I64));
				local String is hdrLbl: b:nextLabel(prefix: 'isub_hdr');
				local String is bodyLbl: b:nextLabel(prefix: 'isub_body');
				local String is extLbl: b:nextLabel(prefix: 'isub_ext');
				local String is addLbl: b:nextLabel(prefix: 'isub_add');
				local String is stepLbl: b:nextLabel(prefix: 'isub_step');
				local String is endLbl: b:nextLabel(prefix: 'isub_end');
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
				local String is cname: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: cname, hasDst: true, retType: IrType:Ptr, callee: 'spec_array_get', argTypes: [IrType:Ptr, IrType:I64], args: [names, curI]));
				local String is eqV: self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_string_equals', argTypes: [IrType:Ptr, IrType:Ptr], args: [cname, bn]);
				b:terminate(inst: IrInst:CondBr(cond: eqV, thenLabel: stepLbl, elseLabel: extLbl));
				local IrBlock is extBlk: b:curFn:addBlock(label: extLbl);
				b:switchBlock(blk: extBlk);
				local String is extV: self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_class_extends', argTypes: [IrType:Ptr, IrType:Ptr], args: [cname, bn]);
				b:terminate(inst: IrInst:CondBr(cond: extV, thenLabel: addLbl, elseLabel: stepLbl));
				local IrBlock is addBlk: b:curFn:addBlock(label: addLbl);
				b:switchBlock(blk: addBlk);
				local String is instV: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_instantiate', argTypes: [IrType:Ptr], args: [cname]);
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_array_add', argTypes: [IrType:Ptr, IrType:Ptr], args: [found, instV]));
				b:terminate(inst: IrInst:Br(target: stepLbl));
				local IrBlock is stepBlk: b:curFn:addBlock(label: stepLbl);
				b:switchBlock(blk: stepBlk);
				local String is oneV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: oneV, value: 1));
				local String is nextI: b:nextTmp();
				b:emit(inst: IrInst:BinOp(dst: nextI, op: '+', lhs: curI, rhs: oneV, ty: IrType:I64));
				b:emit(inst: IrInst:Store(slot: idxSlot, val: nextI, ty: IrType:I64));
				b:terminate(inst: IrInst:Br(target: hdrLbl));
				local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
				b:switchBlock(blk: endBlk);
				res: found;
			},
			'hasMethod': {
				local String is cn: self:lowerArg(b: b, call: call, idx: 0);
				local String is mn: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_has_method', argTypes: [IrType:Ptr, IrType:Ptr], args: [cn, mn]);
			},
			['extendsClass', 'classExtends']: {
				local String is cn: self:lowerArg(b: b, call: call, idx: 0);
				local String is bn: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:I1, callee: 'spec_class_extends', argTypes: [IrType:Ptr, IrType:Ptr], args: [cn, bn]);
			},
			'instantiate': {
				local String is cn: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_instantiate', argTypes: [IrType:Ptr], args: [cn]);
			},
			['invokeVoid', 'invokeVoidByName']: {
				local String is inst: self:lowerArg(b: b, call: call, idx: 0);
				local String is mn: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_invoke_void_by_name', argTypes: [IrType:Ptr, IrType:Ptr], args: [inst, mn]);
			},
			'typeIdentity': {
				local String is o: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_type_identity', argTypes: [IrType:Ptr], args: [o]);
			},
			'typeName': {
				local String is o: b:lowerExpr(expr: call:target);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_type_name', argTypes: [IrType:Ptr], args: [o]);
			},
			'boxNew': {
				local NamedArg is ba0: call:args:get(index: 0);
				local IrType is bty: b:irTypeFor(specType: ba0:value:resolvedType);
				local String is bv: b:castIfNeeded(val: b:lowerExpr(expr: ba0:value), fromTy: bty, toTy: IrType:I64);
				local String is ia: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_rt_box_new', argTypes: [IrType:I64, IrType:I1], args: [bv, ia]);
			},
			'boxGet': {
				local String is bp: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_rt_box_get', argTypes: [IrType:Ptr], args: [bp]);
			},
			'boxSet': {
				local String is bp: self:lowerArg(b: b, call: call, idx: 0);
				local NamedArg is ba1: call:args:get(index: 1);
				local IrType is bty: b:irTypeFor(specType: ba1:value:resolvedType);
				local String is nv: b:castIfNeeded(val: b:lowerExpr(expr: ba1:value), fromTy: bty, toTy: IrType:Ptr);
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: 'spec_rt_box_set', argTypes: [IrType:Ptr, IrType:Ptr], args: [bp, nv]);
			},
			'boxToString': {
				local String is bp: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_rt_box_to_string', argTypes: [IrType:Ptr], args: [bp]);
			}
		]);
		return res;
	}
}
