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
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'compiler', 'ir', IrBlock],
		['base', 'compiler', 'ir', IrModule],
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
		local Boolean is isVec: false;
		match(on: call:target, when: [
			Expression:Ident: local Function(String is tn){
				if({ tn == 'Vector' }, { isVec: true; });
				if({ call:name == 'init' && tn == 'Array' }, { isVec: true; });
			},
			Expression:Path: local Function(Array of String is segs){
				if({ segs:length() > 0 && segs:get(index: segs:length() - 1, default: '') == 'Vector' }, { isVec: true; });
			}
		], default: {});
		if({ isVec }, {
			if({ call:name == 'init' }, { return true; });
			local Boolean is okVec: false;
			match(on: call:name, when: [
				['vecLength', 'vecGetAt', 'vecSetAt', 'vecAdd', 'vecPopLast', 'vecRemoveAt', 'vecClear']: { okVec: true; }
			]);
			return okVec;
		});
		local String is recvType: call:target:resolvedType;
		if({ recvType != 'Array' && !recvType:startsWith(prefix: 'Array of ') && !recvType:startsWith(prefix: 'Array:') && recvType != 'List' && !recvType:startsWith(prefix: 'List of ') && !recvType:startsWith(prefix: 'List:') }, {
			return false;
		});
		local Boolean is isList: recvType == 'List' || recvType:startsWith(prefix: 'List of ') || recvType:startsWith(prefix: 'List:');
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		if({ isList }, {
			match(on: call:name, when: [
				['length', 'clear', 'isEmpty', 'toString', 'pop']: { ok: true; },
				['get', 'push', 'appendString']: { ok: argc >= 1; },
				'set': { ok: argc >= 2; }
			]);
		}, {
			match(on: call:name, when: [
				['length', 'clear', 'isEmpty']: { ok: true; },
				['add', 'get', 'each', 'any', 'count', 'filter', 'map', 'join']: { ok: argc >= 1; },
				['set', 'fold']: { ok: argc >= 2; }
			]);
		});
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local Boolean is isVec: false;
		match(on: call:target, when: [
			Expression:Ident: local Function(String is tn){
				if({ tn == 'Vector' }, { isVec: true; });
			},
			Expression:Path: local Function(Array of String is segs){
				if({ segs:length() > 0 && segs:get(index: segs:length() - 1, default: '') == 'Vector' }, { isVec: true; });
			}
		], default: {});
		if({ isVec }, {
			local NamedArg is va0: call:args:get(index: 0);
			local String is vArg: b:lowerExpr(expr: va0:value);
			local String is nm: call:name;
			if({ nm == 'vecLength' }, {
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_array_length', argTypes: [IrType:Ptr], args: [vArg]));
				return dst;
			});
			if({ nm == 'vecClear' }, {
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_array_clear', argTypes: [IrType:Ptr], args: [vArg]));
				return '0';
			});
			if({ nm == 'vecAdd' }, {
				local NamedArg is va1: call:args:get(index: 1);
				local String is itV: b:castIfNeeded(val: b:lowerExpr(expr: va1:value), fromTy: b:irTypeFor(specType: va1:value:resolvedType), toTy: IrType:Ptr);
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_array_add', argTypes: [IrType:Ptr, IrType:Ptr], args: [vArg, itV]));
				return '0';
			});
			if({ nm == 'vecGetAt' }, {
				local NamedArg is va1: call:args:get(index: 1);
				local String is idxV: b:lowerExpr(expr: va1:value);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_array_get', argTypes: [IrType:Ptr, IrType:I64], args: [vArg, idxV]));
				return dst;
			});
			if({ nm == 'vecSetAt' }, {
				local NamedArg is va1: call:args:get(index: 1);
				local NamedArg is va2: call:args:get(index: 2);
				local String is idxV: b:lowerExpr(expr: va1:value);
				local String is itV: b:castIfNeeded(val: b:lowerExpr(expr: va2:value), fromTy: b:irTypeFor(specType: va2:value:resolvedType), toTy: IrType:Ptr);
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_array_set', argTypes: [IrType:Ptr, IrType:I64, IrType:Ptr], args: [vArg, idxV, itV]));
				return '0';
			});
			if({ nm == 'vecPopLast' }, {
				local NamedArg is va1: call:args:get(index: 1);
				local String is defV: b:castIfNeeded(val: b:lowerExpr(expr: va1:value), fromTy: b:irTypeFor(specType: va1:value:resolvedType), toTy: IrType:Ptr);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_array_pop', argTypes: [IrType:Ptr, IrType:Ptr], args: [vArg, defV]));
				return dst;
			});
			if({ nm == 'vecRemoveAt' }, {
				local NamedArg is va1: call:args:get(index: 1);
				local NamedArg is va2: call:args:get(index: 2);
				local String is idxV: b:lowerExpr(expr: va1:value);
				local String is defV: b:castIfNeeded(val: b:lowerExpr(expr: va2:value), fromTy: b:irTypeFor(specType: va2:value:resolvedType), toTy: IrType:Ptr);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_array_remove_at', argTypes: [IrType:Ptr, IrType:I64, IrType:Ptr], args: [vArg, idxV, defV]));
				return dst;
			});
		});
		if({ call:name == 'init' }, {
			local String is dst: b:nextTmp();
			b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_array_new', argTypes: [], args: []));
			b:emitClaimPool(val: dst);
			return dst;
		});
		local String is aRecv: b:lowerExpr(expr: call:target);
		local String is lRecvType: call:target:resolvedType;
		if({ lRecvType == 'List' || lRecvType:startsWith(prefix: 'List of ') || lRecvType:startsWith(prefix: 'List:') }, {
			local Boolean is isByteList: lRecvType == 'List of Byte' || lRecvType == 'List:Byte';
			if({ isByteList }, {
				if({ call:name == 'length' }, {
					local String is dst: b:nextTmp();
					b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_bytebuffer_length', argTypes: [IrType:Ptr], args: [aRecv]));
					return dst;
				});
				if({ call:name == 'isEmpty' }, {
					local String is lenV: b:nextTmp();
					b:emit(inst: IrInst:IrCall(dst: lenV, hasDst: true, retType: IrType:I64, callee: 'spec_bytebuffer_length', argTypes: [IrType:Ptr], args: [aRecv]));
					local String is zeroV: b:nextTmp();
					b:emit(inst: IrInst:ConstInt(dst: zeroV, value: 0));
					local String is dst: b:nextTmp();
					b:emit(inst: IrInst:Cmp(dst: dst, op: '==', lhs: lenV, rhs: zeroV, ty: IrType:I64));
					return dst;
				});
				if({ call:name == 'clear' }, {
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_bytebuffer_clear', argTypes: [IrType:Ptr], args: [aRecv]));
					return '0';
				});
				if({ call:name == 'toString' }, {
					local String is dst: b:nextTmp();
					b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_bytebuffer_to_string', argTypes: [IrType:Ptr], args: [aRecv]));
					b:emitClaimPool(val: dst);
					return dst;
				});
				if({ call:name == 'push' }, {
					local NamedArg is na0: call:args:get(index: 0);
					local String is bv: b:castIfNeeded(val: b:lowerExpr(expr: na0:value), fromTy: b:irTypeFor(specType: na0:value:resolvedType), toTy: IrType:I64);
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_bytebuffer_push', argTypes: [IrType:Ptr, IrType:I64], args: [aRecv, bv]));
					return '0';
				});
				if({ call:name == 'appendString' }, {
					local NamedArg is na0: call:args:get(index: 0);
					local String is sv: b:lowerExpr(expr: na0:value);
					local String is cstr: b:nextTmp();
					b:emit(inst: IrInst:IrCall(dst: cstr, hasDst: true, retType: IrType:Ptr, callee: 'spec_buf_to_cstring', argTypes: [IrType:Ptr], args: [sv]));
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_bytebuffer_append_string', argTypes: [IrType:Ptr, IrType:Ptr], args: [aRecv, cstr]));
					return '0';
				});
				if({ call:name == 'get' }, {
					local NamedArg is na0: call:args:get(index: 0);
					local String is idxV: b:lowerExpr(expr: na0:value);
					local String is defV: '0';
					if({ call:args:length() >= 2 }, {
						local NamedArg is na1: call:args:get(index: 1);
						defV: b:castIfNeeded(val: b:lowerExpr(expr: na1:value), fromTy: b:irTypeFor(specType: na1:value:resolvedType), toTy: IrType:I64);
					});
					local String is errV: 'null';
					if({ call:args:length() >= 3 }, {
						local NamedArg is na2: call:args:get(index: 2);
						errV: b:lowerExpr(expr: na2:value);
					});
					local String is dst: b:nextTmp();
					b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_bytebuffer_get', argTypes: [IrType:Ptr, IrType:I64, IrType:I64, IrType:Ptr], args: [aRecv, idxV, defV, errV]));
					if({ b:irTypeFor(specType: expr:resolvedType) == IrType:Ptr }, {
						return b:castIfNeeded(val: dst, fromTy: IrType:I64, toTy: IrType:Ptr);
					});
					return dst;
				});
				if({ call:name == 'set' }, {
					local NamedArg is na0: call:args:get(index: 0);
					local NamedArg is na1: call:args:get(index: 1);
					local String is idxV: b:lowerExpr(expr: na0:value);
					local String is iv: b:castIfNeeded(val: b:lowerExpr(expr: na1:value), fromTy: b:irTypeFor(specType: na1:value:resolvedType), toTy: IrType:I64);
					local String is errV: 'null';
					if({ call:args:length() >= 3 }, {
						local NamedArg is na2: call:args:get(index: 2);
						errV: b:lowerExpr(expr: na2:value);
					});
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_bytebuffer_set', argTypes: [IrType:Ptr, IrType:I64, IrType:I64, IrType:Ptr], args: [aRecv, idxV, iv, errV]));
					return '0';
				});
				if({ call:name == 'pop' }, {
					local String is defV: '0';
					if({ call:args:length() >= 1 }, {
						local NamedArg is na0: call:args:get(index: 0);
						defV: b:castIfNeeded(val: b:lowerExpr(expr: na0:value), fromTy: b:irTypeFor(specType: na0:value:resolvedType), toTy: IrType:I64);
					});
					local String is errV: 'null';
					if({ call:args:length() >= 2 }, {
						local NamedArg is na1: call:args:get(index: 1);
						errV: b:lowerExpr(expr: na1:value);
					});
					local String is dst: b:nextTmp();
					b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_bytebuffer_pop', argTypes: [IrType:Ptr, IrType:I64, IrType:Ptr], args: [aRecv, defV, errV]));
					if({ b:irTypeFor(specType: expr:resolvedType) == IrType:Ptr }, {
						return b:castIfNeeded(val: dst, fromTy: IrType:I64, toTy: IrType:Ptr);
					});
					return dst;
				});
			});
			# Generic List of T -> SpecVec*
			if({ call:name == 'length' }, {
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_vec_length', argTypes: [IrType:Ptr], args: [aRecv]));
				return dst;
			});
			if({ call:name == 'isEmpty' }, {
				local String is lenV: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: lenV, hasDst: true, retType: IrType:I64, callee: 'spec_vec_length', argTypes: [IrType:Ptr], args: [aRecv]));
				local String is zeroV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: zeroV, value: 0));
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:Cmp(dst: dst, op: '==', lhs: lenV, rhs: zeroV, ty: IrType:I64));
				return dst;
			});
			if({ call:name == 'clear' }, {
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_vec_clear', argTypes: [IrType:Ptr], args: [aRecv]));
				return '0';
			});
			if({ call:name == 'push' }, {
				local NamedArg is na0: call:args:get(index: 0);
				local String is iv: b:castIfNeeded(val: b:lowerExpr(expr: na0:value), fromTy: b:irTypeFor(specType: na0:value:resolvedType), toTy: IrType:Ptr);
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_vec_push', argTypes: [IrType:Ptr, IrType:Ptr], args: [aRecv, iv]));
				return '0';
			});
			if({ call:name == 'get' }, {
				local NamedArg is na0: call:args:get(index: 0);
				local String is idxV: b:lowerExpr(expr: na0:value);
				local String is defV: 'null';
				if({ call:args:length() >= 2 }, {
					local NamedArg is na1: call:args:get(index: 1);
					defV: b:castIfNeeded(val: b:lowerExpr(expr: na1:value), fromTy: b:irTypeFor(specType: na1:value:resolvedType), toTy: IrType:Ptr);
				});
				local String is errV: 'null';
				if({ call:args:length() >= 3 }, {
					local NamedArg is na2: call:args:get(index: 2);
					errV: b:lowerExpr(expr: na2:value);
				});
				local String is raw: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'spec_vec_get', argTypes: [IrType:Ptr, IrType:I64, IrType:Ptr, IrType:Ptr], args: [aRecv, idxV, defV, errV]));
				local IrType is retTy: b:irTypeFor(specType: expr:resolvedType);
				if({ retTy != IrType:Ptr && retTy != IrType:Void }, {
					return b:castIfNeeded(val: raw, fromTy: IrType:Ptr, toTy: retTy);
				});
				return raw;
			});
			if({ call:name == 'set' }, {
				local NamedArg is na0: call:args:get(index: 0);
				local NamedArg is na1: call:args:get(index: 1);
				local String is idxV: b:lowerExpr(expr: na0:value);
				local String is iv: b:castIfNeeded(val: b:lowerExpr(expr: na1:value), fromTy: b:irTypeFor(specType: na1:value:resolvedType), toTy: IrType:Ptr);
				local String is errV: 'null';
				if({ call:args:length() >= 3 }, {
					local NamedArg is na2: call:args:get(index: 2);
					errV: b:lowerExpr(expr: na2:value);
				});
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_vec_set', argTypes: [IrType:Ptr, IrType:I64, IrType:Ptr, IrType:Ptr], args: [aRecv, idxV, iv, errV]));
				return '0';
			});
			if({ call:name == 'pop' }, {
				local String is defV: 'null';
				if({ call:args:length() >= 1 }, {
					local NamedArg is na0: call:args:get(index: 0);
					defV: b:castIfNeeded(val: b:lowerExpr(expr: na0:value), fromTy: b:irTypeFor(specType: na0:value:resolvedType), toTy: IrType:Ptr);
				});
				local String is errV: 'null';
				if({ call:args:length() >= 2 }, {
					local NamedArg is na1: call:args:get(index: 1);
					errV: b:lowerExpr(expr: na1:value);
				});
				local String is raw: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'spec_vec_pop', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: [aRecv, defV, errV]));
				local IrType is retTy: b:irTypeFor(specType: expr:resolvedType);
				if({ retTy != IrType:Ptr && retTy != IrType:Void }, {
					return b:castIfNeeded(val: raw, fromTy: IrType:Ptr, toTy: retTy);
				});
				return raw;
			});
		});
		local String is res: '0';
		match(on: call:name, when: [
			'length': {
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_array_length', argTypes: [IrType:Ptr], args: [aRecv]));
				res: dst;
			},
			'clear': {
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_array_clear', argTypes: [IrType:Ptr], args: [aRecv]));
			},
			'isEmpty': {
				local String is lenV: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: lenV, hasDst: true, retType: IrType:I64, callee: 'spec_array_length', argTypes: [IrType:Ptr], args: [aRecv]));
				local String is zeroV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: zeroV, value: 0));
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:Cmp(dst: dst, op: '==', lhs: lenV, rhs: zeroV, ty: IrType:I64));
				res: dst;
			},
			'add': {
				local NamedArg is na0: call:args:get(index: 0);
				local Expression is ivExpr: na0:value;
				local String is ivTyName: ivExpr:resolvedType;
				local String is iv: b:lowerExpr(expr: ivExpr);
				local Boolean is isArrLit: match(on: ivExpr, when: [
					Expression:ArrayLit: local Function of Boolean(Array of Expression is items){ return true; },
					else: { false }
				]);
				local Boolean is isArrArg: isArrLit && (ivTyName == 'Array' || ivTyName:startsWith(prefix: 'Array of ') || ivTyName:startsWith(prefix: 'Array:'));
				if({ isArrArg }, {
					local String is lenV: b:nextTmp();
					b:emit(inst: IrInst:IrCall(dst: lenV, hasDst: true, retType: IrType:I64, callee: 'spec_array_length', argTypes: [IrType:Ptr], args: [iv]));
					local String is idxSlot: '%aadd_i_' . (b:nextTmp());
					idxSlot: '%aadd_i_' . (b:tmpCounter as String);
					b:emit(inst: IrInst:Alloca(slot: idxSlot, ty: IrType:I64));
					local String is zeroV: b:nextTmp();
					b:emit(inst: IrInst:ConstInt(dst: zeroV, value: 0));
					b:emit(inst: IrInst:Store(slot: idxSlot, val: zeroV, ty: IrType:I64));
					local String is hdrLbl: b:nextLabel(prefix: 'aadd_hdr');
					local String is bodyLbl: b:nextLabel(prefix: 'aadd_body');
					local String is endLbl: b:nextLabel(prefix: 'aadd_end');
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
					local String is elemV: b:nextTmp();
					b:emit(inst: IrInst:IrCall(dst: elemV, hasDst: true, retType: IrType:Ptr, callee: 'spec_array_get', argTypes: [IrType:Ptr, IrType:I64], args: [iv, curI]));
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_array_add_object', argTypes: [IrType:Ptr, IrType:Ptr], args: [aRecv, elemV]));
					local String is oneV: b:nextTmp();
					b:emit(inst: IrInst:ConstInt(dst: oneV, value: 1));
					local String is nextI: b:nextTmp();
					b:emit(inst: IrInst:BinOp(dst: nextI, op: '+', lhs: curI, rhs: oneV, ty: IrType:I64));
					b:emit(inst: IrInst:Store(slot: idxSlot, val: nextI, ty: IrType:I64));
					b:terminate(inst: IrInst:Br(target: hdrLbl));
					local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
					b:switchBlock(blk: endBlk);
				}, {
					local IrType is ity: b:irTypeFor(specType: ivTyName);
					local String is ip: b:castIfNeeded(val: iv, fromTy: ity, toTy: IrType:Ptr);
					local String is addCallee: 'spec_array_add';
					if({ b:isArcSpecType(specType: ivTyName) }, {
						addCallee: 'spec_array_add_object';
					});
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: addCallee, argTypes: [IrType:Ptr, IrType:Ptr], args: [aRecv, ip]));
				});
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
				local String is ip: b:castIfNeeded(val: iv, fromTy: ity, toTy: IrType:Ptr);
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
			},
			'join': {
				local NamedArg is na0: call:args:get(index: 0);
				local String is sepV: b:lowerExpr(expr: na0:value);
				local String is lenV: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: lenV, hasDst: true, retType: IrType:I64, callee: 'spec_array_length', argTypes: [IrType:Ptr], args: [aRecv]));
				local String is emptyStr: b:nextTmp();
				local Int is emptyId: b:mod:internStringLiteral(value: '');
				b:emit(inst: IrInst:ConstString(dst: emptyStr, strId: emptyId));
				local String is outSlot: '%join_out_' . (b:nextTmp());
				outSlot: '%join_out_' . (b:tmpCounter as String);
				b:emit(inst: IrInst:Alloca(slot: outSlot, ty: IrType:Ptr));
				b:emit(inst: IrInst:Store(slot: outSlot, val: emptyStr, ty: IrType:Ptr));
				local String is idxSlot: '%join_i_' . (b:nextTmp());
				idxSlot: '%join_i_' . (b:tmpCounter as String);
				b:emit(inst: IrInst:Alloca(slot: idxSlot, ty: IrType:I64));
				local String is zeroV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: zeroV, value: 0));
				b:emit(inst: IrInst:Store(slot: idxSlot, val: zeroV, ty: IrType:I64));

				local String is hdrLbl: b:nextLabel(prefix: 'join_hdr');
				local String is bodyLbl: b:nextLabel(prefix: 'join_body');
				local String is sepLbl: b:nextLabel(prefix: 'join_sep');
				local String is catLbl: b:nextLabel(prefix: 'join_cat');
				local String is endLbl: b:nextLabel(prefix: 'join_end');
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
				local String is gtZ: b:nextTmp();
				b:emit(inst: IrInst:Cmp(dst: gtZ, op: '>', lhs: curI, rhs: zeroV, ty: IrType:I64));
				b:terminate(inst: IrInst:CondBr(cond: gtZ, thenLabel: sepLbl, elseLabel: catLbl));

				local IrBlock is sepBlk: b:curFn:addBlock(label: sepLbl);
				b:switchBlock(blk: sepBlk);
				local String is curOut1: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: curOut1, slot: outSlot, ty: IrType:Ptr));
				local String is withSep: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: withSep, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_concat', argTypes: [IrType:Ptr, IrType:Ptr], args: [curOut1, sepV]));
				b:emit(inst: IrInst:Store(slot: outSlot, val: withSep, ty: IrType:Ptr));
				b:terminate(inst: IrInst:Br(target: catLbl));

				local IrBlock is catBlk: b:curFn:addBlock(label: catLbl);
				b:switchBlock(blk: catBlk);
				local String is curOut2: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: curOut2, slot: outSlot, ty: IrType:Ptr));
				local String is elemV: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: elemV, hasDst: true, retType: IrType:Ptr, callee: 'spec_array_get', argTypes: [IrType:Ptr, IrType:I64], args: [aRecv, curI]));
				local String is nextOut: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: nextOut, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_concat', argTypes: [IrType:Ptr, IrType:Ptr], args: [curOut2, elemV]));
				b:emit(inst: IrInst:Store(slot: outSlot, val: nextOut, ty: IrType:Ptr));
				local String is oneV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: oneV, value: 1));
				local String is nextI: b:nextTmp();
				b:emit(inst: IrInst:BinOp(dst: nextI, op: '+', lhs: curI, rhs: oneV, ty: IrType:I64));
				b:emit(inst: IrInst:Store(slot: idxSlot, val: nextI, ty: IrType:I64));
				b:terminate(inst: IrInst:Br(target: hdrLbl));

				local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
				b:switchBlock(blk: endBlk);
				local String is finalOut: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: finalOut, slot: outSlot, ty: IrType:Ptr));
				res: finalOut;
			},
			['any', 'count', 'filter', 'map']: {
				local NamedArg is na0: call:args:get(index: 0);
				local String is recvType: call:target:resolvedType;
				local IrType is elemTy: IrType:Ptr;
				if({ recvType:startsWith(prefix: 'Array:') }, {
					elemTy: b:irTypeFor(specType: recvType:substring(start: 6, end: recvType:length()));
				}, {
					if({ recvType:startsWith(prefix: 'Array of ') }, {
						elemTy: b:irTypeFor(specType: recvType:substring(start: 9, end: recvType:length()));
					});
				});
				local IrType is outElemTy: IrType:Ptr;
				local String is exprResType: expr:resolvedType;
				if({ exprResType:startsWith(prefix: 'Array:') }, {
					outElemTy: b:irTypeFor(specType: exprResType:substring(start: 6, end: exprResType:length()));
				}, {
					if({ exprResType:startsWith(prefix: 'Array of ') }, {
						outElemTy: b:irTypeFor(specType: exprResType:substring(start: 9, end: exprResType:length()));
					});
				});
				match(on: na0:value, when: [
					Expression:AnonFn: local Function(Type is rt, Array of Parameter is fparams, Array of Statement is _fb){
						if({ fparams:length() >= 1 }, {
							local Parameter is p0: fparams:get(index: 0);
							local Type is p0t: p0:paramType;
							elemTy: b:irTypeFor(specType: p0t:name);
						});
						if({ rt:name != '' && rt:name != 'Void' }, {
							outElemTy: b:irTypeFor(specType: rt:name);
						});
					}
				], default: {});
				if({ elemTy == IrType:Void }, { elemTy: IrType:Ptr; });
				if({ outElemTy == IrType:Void }, { outElemTy: IrType:Ptr; });

				local String is cObj: b:lowerExpr(expr: na0:value);
				local String is fnPtrAddr: b:nextTmp();
				b:emit(inst: IrInst:FieldPtr(dst: fnPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 0));
				local String is fnPtrVal: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: fnPtrVal, slot: fnPtrAddr, ty: IrType:Ptr));
				local String is envPtrAddr: b:nextTmp();
				b:emit(inst: IrInst:FieldPtr(dst: envPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 1));
				local String is envVal: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: envVal, slot: envPtrAddr, ty: IrType:Ptr));

				local String is lenV: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: lenV, hasDst: true, retType: IrType:I64, callee: 'spec_array_length', argTypes: [IrType:Ptr], args: [aRecv]));

				local String is accSlot: '';
				local String is outArr: '';
				if({ call:name == 'any' }, {
					accSlot: '%aany_r_' . (b:nextTmp());
					accSlot: '%aany_r_' . (b:tmpCounter as String);
					b:emit(inst: IrInst:Alloca(slot: accSlot, ty: IrType:I1));
					local String is fV: b:nextTmp();
					b:emit(inst: IrInst:ConstBool(dst: fV, value: false));
					b:emit(inst: IrInst:Store(slot: accSlot, val: fV, ty: IrType:I1));
				});
				if({ call:name == 'count' }, {
					accSlot: '%acnt_r_' . (b:nextTmp());
					accSlot: '%acnt_r_' . (b:tmpCounter as String);
					b:emit(inst: IrInst:Alloca(slot: accSlot, ty: IrType:I64));
					local String is zV: b:nextTmp();
					b:emit(inst: IrInst:ConstInt(dst: zV, value: 0));
					b:emit(inst: IrInst:Store(slot: accSlot, val: zV, ty: IrType:I64));
				});
				if({ call:name == 'filter' }, {
					local String is newCallee: 'spec_array_new';
					if({ elemTy == IrType:Ptr }, { newCallee: 'spec_array_new_object'; });
					outArr: b:nextTmp();
					b:emit(inst: IrInst:IrCall(dst: outArr, hasDst: true, retType: IrType:Ptr, callee: newCallee, argTypes: [], args: []));
					b:emitClaimPool(val: outArr);
				});
				if({ call:name == 'map' }, {
					local String is newCallee: 'spec_array_new';
					if({ outElemTy == IrType:Ptr }, { newCallee: 'spec_array_new_object'; });
					outArr: b:nextTmp();
					b:emit(inst: IrInst:IrCall(dst: outArr, hasDst: true, retType: IrType:Ptr, callee: newCallee, argTypes: [], args: []));
					b:emitClaimPool(val: outArr);
				});

				local String is idxSlot: '%acmb_i_' . (b:nextTmp());
				idxSlot: '%acmb_i_' . (b:tmpCounter as String);
				b:emit(inst: IrInst:Alloca(slot: idxSlot, ty: IrType:I64));
				local String is zeroV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: zeroV, value: 0));
				b:emit(inst: IrInst:Store(slot: idxSlot, val: zeroV, ty: IrType:I64));

				local String is hdrLbl: b:nextLabel(prefix: 'acmb_hdr');
				local String is bodyLbl: b:nextLabel(prefix: 'acmb_body');
				local String is stepLbl: b:nextLabel(prefix: 'acmb_step');
				local String is endLbl: b:nextLabel(prefix: 'acmb_end');
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
				local String is elemV: b:castIfNeeded(val: raw, fromTy: IrType:Ptr, toTy: elemTy);

				if({ call:name == 'map' }, {
					local String is mRes: b:nextTmp();
					b:emit(inst: IrInst:IndirectCall(dst: mRes, hasDst: true, retType: outElemTy, fnPtr: fnPtrVal, argTypes: [IrType:Ptr, elemTy], args: [envVal, elemV]));
					local String is mPtr: b:castIfNeeded(val: mRes, fromTy: outElemTy, toTy: IrType:Ptr);
					local String is addCallee: 'spec_array_add';
					if({ outElemTy == IrType:Ptr }, { addCallee: 'spec_array_add_object'; });
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: addCallee, argTypes: [IrType:Ptr, IrType:Ptr], args: [outArr, mPtr]));
					b:terminate(inst: IrInst:Br(target: stepLbl));
				}, {
					local String is pRes: b:nextTmp();
					b:emit(inst: IrInst:IndirectCall(dst: pRes, hasDst: true, retType: IrType:I1, fnPtr: fnPtrVal, argTypes: [IrType:Ptr, elemTy], args: [envVal, elemV]));
					local String is hitLbl: b:nextLabel(prefix: 'acmb_hit');
					b:terminate(inst: IrInst:CondBr(cond: pRes, thenLabel: hitLbl, elseLabel: stepLbl));
					local IrBlock is hitBlk: b:curFn:addBlock(label: hitLbl);
					b:switchBlock(blk: hitBlk);
					if({ call:name == 'any' }, {
						local String is tV: b:nextTmp();
						b:emit(inst: IrInst:ConstBool(dst: tV, value: true));
						b:emit(inst: IrInst:Store(slot: accSlot, val: tV, ty: IrType:I1));
						b:terminate(inst: IrInst:Br(target: endLbl));
					});
					if({ call:name == 'count' }, {
						local String is curC: b:nextTmp();
						b:emit(inst: IrInst:Load(dst: curC, slot: accSlot, ty: IrType:I64));
						local String is oneC: b:nextTmp();
						b:emit(inst: IrInst:ConstInt(dst: oneC, value: 1));
						local String is nxtC: b:nextTmp();
						b:emit(inst: IrInst:BinOp(dst: nxtC, op: '+', lhs: curC, rhs: oneC, ty: IrType:I64));
						b:emit(inst: IrInst:Store(slot: accSlot, val: nxtC, ty: IrType:I64));
						b:terminate(inst: IrInst:Br(target: stepLbl));
					});
					if({ call:name == 'filter' }, {
						local String is addCallee: 'spec_array_add';
						if({ elemTy == IrType:Ptr }, { addCallee: 'spec_array_add_object'; });
						b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: addCallee, argTypes: [IrType:Ptr, IrType:Ptr], args: [outArr, raw]));
						b:terminate(inst: IrInst:Br(target: stepLbl));
					});
				});

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
				if({ call:name == 'any' }, {
					res: b:nextTmp();
					b:emit(inst: IrInst:Load(dst: res, slot: accSlot, ty: IrType:I1));
				});
				if({ call:name == 'count' }, {
					res: b:nextTmp();
					b:emit(inst: IrInst:Load(dst: res, slot: accSlot, ty: IrType:I64));
				});
				if({ call:name == 'filter' || call:name == 'map' }, {
					res: outArr;
				});
			},
			'fold': {
				local NamedArg is na0: call:args:get(index: 0);
				local NamedArg is na1: call:args:get(index: 1);
				local String is recvType: call:target:resolvedType;
				local IrType is elemTy: IrType:Ptr;
				if({ recvType:startsWith(prefix: 'Array:') }, {
					elemTy: b:irTypeFor(specType: recvType:substring(start: 6, end: recvType:length()));
				}, {
					if({ recvType:startsWith(prefix: 'Array of ') }, {
						elemTy: b:irTypeFor(specType: recvType:substring(start: 9, end: recvType:length()));
					});
				});
				local IrType is initTy: b:irTypeFor(specType: na0:value:resolvedType);
				local IrType is accTy: initTy;
				match(on: na1:value, when: [
					Expression:AnonFn: local Function(Type is rt, Array of Parameter is fparams, Array of Statement is _fb){
						if({ fparams:length() >= 1 }, {
							local Parameter is p0: fparams:get(index: 0);
							local Type is p0t: p0:paramType;
							accTy: b:irTypeFor(specType: p0t:name);
						});
						if({ fparams:length() >= 2 }, {
							local Parameter is p1: fparams:get(index: 1);
							local Type is p1t: p1:paramType;
							elemTy: b:irTypeFor(specType: p1t:name);
						});
						if({ rt:name != '' && rt:name != 'Void' }, {
							accTy: b:irTypeFor(specType: rt:name);
						});
					}
				], default: {});
				if({ elemTy == IrType:Void }, { elemTy: IrType:Ptr; });
				if({ accTy == IrType:Void }, { accTy: IrType:Ptr; });

				local String is initRaw: b:lowerExpr(expr: na0:value);
				local String is initV: b:castIfNeeded(val: initRaw, fromTy: initTy, toTy: accTy);
				local String is cObj: b:lowerExpr(expr: na1:value);
				local String is fnPtrAddr: b:nextTmp();
				b:emit(inst: IrInst:FieldPtr(dst: fnPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 0));
				local String is fnPtrVal: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: fnPtrVal, slot: fnPtrAddr, ty: IrType:Ptr));
				local String is envPtrAddr: b:nextTmp();
				b:emit(inst: IrInst:FieldPtr(dst: envPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 1));
				local String is envVal: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: envVal, slot: envPtrAddr, ty: IrType:Ptr));

				local String is lenV: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: lenV, hasDst: true, retType: IrType:I64, callee: 'spec_array_length', argTypes: [IrType:Ptr], args: [aRecv]));

				local String is accSlot: '%afld_a_' . (b:nextTmp());
				accSlot: '%afld_a_' . (b:tmpCounter as String);
				b:emit(inst: IrInst:Alloca(slot: accSlot, ty: accTy));
				b:emit(inst: IrInst:Store(slot: accSlot, val: initV, ty: accTy));

				local String is idxSlot: '%afld_i_' . (b:nextTmp());
				idxSlot: '%afld_i_' . (b:tmpCounter as String);
				b:emit(inst: IrInst:Alloca(slot: idxSlot, ty: IrType:I64));
				local String is zeroV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: zeroV, value: 0));
				b:emit(inst: IrInst:Store(slot: idxSlot, val: zeroV, ty: IrType:I64));

				local String is hdrLbl: b:nextLabel(prefix: 'afld_hdr');
				local String is bodyLbl: b:nextLabel(prefix: 'afld_body');
				local String is endLbl: b:nextLabel(prefix: 'afld_end');
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
				local String is elemV: b:castIfNeeded(val: raw, fromTy: IrType:Ptr, toTy: elemTy);
				local String is curAcc: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: curAcc, slot: accSlot, ty: accTy));
				local String is nextAcc: b:nextTmp();
				b:emit(inst: IrInst:IndirectCall(dst: nextAcc, hasDst: true, retType: accTy, fnPtr: fnPtrVal, argTypes: [IrType:Ptr, accTy, elemTy], args: [envVal, curAcc, elemV]));
				b:emit(inst: IrInst:Store(slot: accSlot, val: nextAcc, ty: accTy));
				local String is oneV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: oneV, value: 1));
				local String is nextI: b:nextTmp();
				b:emit(inst: IrInst:BinOp(dst: nextI, op: '+', lhs: curI, rhs: oneV, ty: IrType:I64));
				b:emit(inst: IrInst:Store(slot: idxSlot, val: nextI, ty: IrType:I64));
				b:terminate(inst: IrInst:Br(target: hdrLbl));

				local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
				b:switchBlock(blk: endBlk);
				local String is finalAcc: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: finalAcc, slot: accSlot, ty: accTy));
				local IrType is retTy: b:irTypeFor(specType: expr:resolvedType);
				if({ retTy != IrType:Void && retTy != accTy }, {
					res: b:castIfNeeded(val: finalAcc, fromTy: accTy, toTy: retTy);
				}, {
					res: finalAcc;
				});
			}
		]);
		return res;
	}
}
