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
		local Boolean is isArrInit: false;
		match(on: call:target, when: [
			Expression:Ident: local Function(String is tn){
				if({ call:name == 'init' && tn == 'Array' }, { isArrInit: true; });
			}
		], default: {});
		if({ isArrInit }, { return true; });
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
				['length', 'clear', 'isEmpty', 'pop']: { ok: true; },
				['add', 'get', 'each', 'any', 'all', 'none', 'count', 'filter', 'map', 'removeAt']: { ok: argc >= 1; },
				['set', 'fold']: { ok: argc >= 2; }
			]);
		});
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		if({ call:name == 'init' }, {
			local String is dst: b:nextTmp();
			b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'Vector_vecNew', argTypes: [], args: []));
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
					b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'Vector_byteBufLength', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', aRecv]));
					return dst;
				});
				if({ call:name == 'isEmpty' }, {
					local String is lenV: b:nextTmp();
					b:emit(inst: IrInst:IrCall(dst: lenV, hasDst: true, retType: IrType:I64, callee: 'Vector_byteBufLength', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', aRecv]));
					local String is zeroV: b:nextTmp();
					b:emit(inst: IrInst:ConstInt(dst: zeroV, value: 0));
					local String is dst: b:nextTmp();
					b:emit(inst: IrInst:Cmp(dst: dst, op: '==', lhs: lenV, rhs: zeroV, ty: IrType:I64));
					return dst;
				});
				if({ call:name == 'clear' }, {
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Vector_byteBufClear', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', aRecv]));
					return '0';
				});
				if({ call:name == 'toString' }, {
					local String is dst: b:nextTmp();
					b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'Vector_byteBufToString', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', aRecv]));
					return dst;
				});
				if({ call:name == 'push' }, {
					local NamedArg is na0: call:args:get(index: 0);
					local String is bv: b:castIfNeeded(val: b:lowerExpr(expr: na0:value), fromTy: b:irTypeFor(specType: na0:value:resolvedType), toTy: IrType:I64);
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Vector_byteBufPush', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64], args: ['null', aRecv, bv]));
					return '0';
				});
				if({ call:name == 'appendString' }, {
					local NamedArg is na0: call:args:get(index: 0);
					local String is sv: b:lowerExpr(expr: na0:value);
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Vector_byteBufAppendString', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', aRecv, sv]));
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
					b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'Vector_byteBufGet', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64, IrType:I64, IrType:Ptr], args: ['null', aRecv, idxV, defV, errV]));
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
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Vector_byteBufSet', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64, IrType:I64, IrType:Ptr], args: ['null', aRecv, idxV, iv, errV]));
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
					b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'Vector_byteBufPop', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64, IrType:Ptr], args: ['null', aRecv, defV, errV]));
					if({ b:irTypeFor(specType: expr:resolvedType) == IrType:Ptr }, {
						return b:castIfNeeded(val: dst, fromTy: IrType:I64, toTy: IrType:Ptr);
					});
					return dst;
				});
			});
			# Generic List of T -> SpecArray* via Vector
			if({ call:name == 'length' }, {
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'Vector_vecLength', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', aRecv]));
				return dst;
			});
			if({ call:name == 'isEmpty' }, {
				local String is lenV: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: lenV, hasDst: true, retType: IrType:I64, callee: 'Vector_vecLength', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', aRecv]));
				local String is zeroV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: zeroV, value: 0));
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:Cmp(dst: dst, op: '==', lhs: lenV, rhs: zeroV, ty: IrType:I64));
				return dst;
			});
			if({ call:name == 'clear' }, {
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Vector_vecClear', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', aRecv]));
				return '0';
			});
			if({ call:name == 'push' }, {
				local NamedArg is na0: call:args:get(index: 0);
				local String is iv: b:castIfNeeded(val: b:lowerExpr(expr: na0:value), fromTy: b:irTypeFor(specType: na0:value:resolvedType), toTy: IrType:Ptr);
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Vector_vecAdd', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', aRecv, iv]));
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
				b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'Vector_vecGet', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64, IrType:Ptr, IrType:Ptr], args: ['null', aRecv, idxV, defV, errV]));
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
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Vector_vecSet', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64, IrType:Ptr, IrType:Ptr], args: ['null', aRecv, idxV, iv, errV]));
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
				b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'Vector_vecPop', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', aRecv, defV, errV]));
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
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'Vector_vecLength', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', aRecv]));
				res: dst;
			},
			'clear': {
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Vector_vecClear', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', aRecv]));
			},
			'isEmpty': {
				local String is lenV: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: lenV, hasDst: true, retType: IrType:I64, callee: 'Vector_vecLength', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', aRecv]));
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
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Vector_vecAddArray', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', aRecv, iv]));
				}, {
					local IrType is ity: b:irTypeFor(specType: ivTyName);
					local String is ip: b:castIfNeeded(val: iv, fromTy: ity, toTy: IrType:Ptr);
					local String is addCallee: 'Vector_vecAdd';
					if({ b:isArcSpecType(specType: ivTyName) }, {
						addCallee: 'Vector_vecAddObject';
					});
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: addCallee, argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', aRecv, ip]));
				});
			},
			'get': {
				local NamedArg is na0: call:args:get(index: 0);
				local String is idxV: b:lowerExpr(expr: na0:value);
				local String is raw: b:nextTmp();
				if({ call:args:length() >= 2 }, {
					local NamedArg is na1: call:args:get(index: 1);
					local IrType is dty: b:irTypeFor(specType: na1:value:resolvedType);
					local String is defV: b:castIfNeeded(val: b:lowerExpr(expr: na1:value), fromTy: dty, toTy: IrType:Ptr);
					b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'Vector_vecGetAt', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64, IrType:Ptr], args: ['null', aRecv, idxV, defV]));
				}, {
					b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'Vector_vecGetChecked', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64], args: ['null', aRecv, idxV]));
				});
				local IrType is grTy: b:irTypeFor(specType: expr:resolvedType);
				if({ grTy != IrType:Ptr && grTy != IrType:Void }, {
					local String is casted: b:nextTmp();
					b:emit(inst: IrInst:IrCast(dst: casted, val: raw, fromType: IrType:Ptr, toType: grTy));
					res: casted;
				}, {
					res: raw;
				});
			},
			'pop': {
				local String is defV: 'null';
				if({ call:args:length() >= 1 }, {
					local NamedArg is na0: call:args:get(index: 0);
					defV: b:castIfNeeded(val: b:lowerExpr(expr: na0:value), fromTy: b:irTypeFor(specType: na0:value:resolvedType), toTy: IrType:Ptr);
				});
				local String is raw: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'Vector_vecPopLast', argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', aRecv, defV]));
				local IrType is prTy: b:irTypeFor(specType: expr:resolvedType);
				res: b:castIfNeeded(val: raw, fromTy: IrType:Ptr, toTy: prTy);
			},
			'removeAt': {
				local NamedArg is na0: call:args:get(index: 0);
				local String is idxV: b:lowerExpr(expr: na0:value);
				local String is defV: 'null';
				if({ call:args:length() >= 2 }, {
					local NamedArg is na1: call:args:get(index: 1);
					defV: b:castIfNeeded(val: b:lowerExpr(expr: na1:value), fromTy: b:irTypeFor(specType: na1:value:resolvedType), toTy: IrType:Ptr);
				});
				local String is raw: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'Vector_vecRemoveAt', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64, IrType:Ptr], args: ['null', aRecv, idxV, defV]));
				local IrType is rrTy: b:irTypeFor(specType: expr:resolvedType);
				res: b:castIfNeeded(val: raw, fromTy: IrType:Ptr, toTy: rrTy);
			},
			'set': {
				local NamedArg is na0: call:args:get(index: 0);
				local NamedArg is na1: call:args:get(index: 1);
				local String is idxV: b:lowerExpr(expr: na0:value);
				local Expression is ivExpr: na1:value;
				local String is iv: b:lowerExpr(expr: ivExpr);
				local IrType is ity: b:irTypeFor(specType: ivExpr:resolvedType);
				local String is ip: b:castIfNeeded(val: iv, fromTy: ity, toTy: IrType:Ptr);
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'Vector_vecSetAt', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64, IrType:Ptr], args: ['null', aRecv, idxV, ip]));
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
				b:emit(inst: IrInst:IrCall(dst: lenV, hasDst: true, retType: IrType:I64, callee: 'Vector_vecLength', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', aRecv]));
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
				b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'Vector_vecGetChecked', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64], args: ['null', aRecv, curI]));
				local String is elemV: raw;
				if({ elemTy != IrType:Ptr }, {
					elemV: b:nextTmp();
					b:emit(inst: IrInst:IrCast(dst: elemV, val: raw, fromType: IrType:Ptr, toType: elemTy));
				});
				b:emit(inst: IrInst:IndirectCall(dst: '', hasDst: false, retType: IrType:Void, fnPtr: fnPtrVal, argTypes: [IrType:Ptr, elemTy], args: [envVal, elemV]));
				b:emitCheckUnwindAfterCall(callee: '__indirect__');
				local String is oneV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: oneV, value: 1));
				local String is nextI: b:nextTmp();
				b:emit(inst: IrInst:BinOp(dst: nextI, op: '+', lhs: curI, rhs: oneV, ty: IrType:I64));
				b:emit(inst: IrInst:Store(slot: idxSlot, val: nextI, ty: IrType:I64));
				b:terminate(inst: IrInst:Br(target: hdrLbl));

				local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
				b:switchBlock(blk: endBlk);
			},
			['any', 'all', 'none', 'count', 'filter', 'map']: {
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
				b:emit(inst: IrInst:IrCall(dst: lenV, hasDst: true, retType: IrType:I64, callee: 'Vector_vecLength', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', aRecv]));

				local String is accSlot: '';
				local String is outArr: '';
				if({ call:name == 'any' || call:name == 'all' || call:name == 'none' }, {
					accSlot: '%aany_r_' . (b:nextTmp());
					accSlot: '%aany_r_' . (b:tmpCounter as String);
					b:emit(inst: IrInst:Alloca(slot: accSlot, ty: IrType:I1));
					local String is initB: b:nextTmp();
					b:emit(inst: IrInst:ConstBool(dst: initB, value: call:name != 'any'));
					b:emit(inst: IrInst:Store(slot: accSlot, val: initB, ty: IrType:I1));
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
					local String is newCallee: 'Vector_vecNew';
					if({ elemTy == IrType:Ptr }, { newCallee: 'Vector_vecNewObject'; });
					outArr: b:nextTmp();
					b:emit(inst: IrInst:IrCall(dst: outArr, hasDst: true, retType: IrType:Ptr, callee: newCallee, argTypes: [], args: []));
					b:emitClaimPool(val: outArr);
				});
				if({ call:name == 'map' }, {
					local String is newCallee: 'Vector_vecNew';
					if({ outElemTy == IrType:Ptr }, { newCallee: 'Vector_vecNewObject'; });
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
				b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'Vector_vecGetChecked', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64], args: ['null', aRecv, curI]));
				local String is elemV: b:castIfNeeded(val: raw, fromTy: IrType:Ptr, toTy: elemTy);

				if({ call:name == 'map' }, {
					local String is mRes: b:nextTmp();
					b:emit(inst: IrInst:IndirectCall(dst: mRes, hasDst: true, retType: outElemTy, fnPtr: fnPtrVal, argTypes: [IrType:Ptr, elemTy], args: [envVal, elemV]));
					local String is mPtr: b:castIfNeeded(val: mRes, fromTy: outElemTy, toTy: IrType:Ptr);
					local String is addCallee: 'Vector_vecAdd';
					if({ outElemTy == IrType:Ptr }, { addCallee: 'Vector_vecAddObject'; });
					b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: addCallee, argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', outArr, mPtr]));
					b:terminate(inst: IrInst:Br(target: stepLbl));
				}, {
					local String is pRes: b:nextTmp();
					b:emit(inst: IrInst:IndirectCall(dst: pRes, hasDst: true, retType: IrType:I1, fnPtr: fnPtrVal, argTypes: [IrType:Ptr, elemTy], args: [envVal, elemV]));
					local String is hitLbl: b:nextLabel(prefix: 'acmb_hit');
					if({ call:name == 'all' }, {
						b:terminate(inst: IrInst:CondBr(cond: pRes, thenLabel: stepLbl, elseLabel: hitLbl));
					}, {
						b:terminate(inst: IrInst:CondBr(cond: pRes, thenLabel: hitLbl, elseLabel: stepLbl));
					});
					local IrBlock is hitBlk: b:curFn:addBlock(label: hitLbl);
					b:switchBlock(blk: hitBlk);
					if({ call:name == 'any' || call:name == 'all' || call:name == 'none' }, {
						local String is bV: b:nextTmp();
						b:emit(inst: IrInst:ConstBool(dst: bV, value: call:name == 'any'));
						b:emit(inst: IrInst:Store(slot: accSlot, val: bV, ty: IrType:I1));
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
						local String is addCallee: 'Vector_vecAdd';
						if({ elemTy == IrType:Ptr }, { addCallee: 'Vector_vecAddObject'; });
						b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: addCallee, argTypes: [IrType:Ptr, IrType:Ptr, IrType:Ptr], args: ['null', outArr, raw]));
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
				if({ call:name == 'any' || call:name == 'all' || call:name == 'none' }, {
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
				b:emit(inst: IrInst:IrCall(dst: lenV, hasDst: true, retType: IrType:I64, callee: 'Vector_vecLength', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', aRecv]));

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
				b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'Vector_vecGetChecked', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64], args: ['null', aRecv, curI]));
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
