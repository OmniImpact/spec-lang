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
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Type],
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
		return 'MapCallLowerer';
	}

	replace Function of Int is order(){
		return 40;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		if({ call:name == 'init' }, {
			local Boolean is isMapCtor: false;
			match(on: call:target, when: [
				Expression:Ident: local Function(String is tn){
					# The bare template spelling (binding-era sources) and
					# the specialized instantiation's mangled spelling both
					# name a Map construction.
					if({ tn == 'Map' || b:specBaseMap:get(key: tn, default: '') == 'Map' }, { isMapCtor: true; });
				}
			], default: {});
			if({ isMapCtor }, { return true; });
		});
		local String is recvType: call:target:resolvedType;
		if({ recvType != 'Map' && !recvType:startsWith(prefix: 'Map of ') && !recvType:startsWith(prefix: 'Map:') }, {
			return false;
		});
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: call:name, when: [
			['length', 'keys']: { ok: true; },
			['has', 'get', 'getString', 'getFloat', 'remove', 'each', 'any', 'count', 'filter']: { ok: argc >= 1; },
			'set': { ok: argc >= 2; }
		]);
		return ok;
	}

	local Function of String is keySuffix(String is recvType, String is kSpecType){
		if({ kSpecType == 'Int' || kSpecType == 'Boolean' || recvType:startsWith(prefix: 'Map of Int to ') || recvType:startsWith(prefix: 'Map:Int:') || recvType:startsWith(prefix: 'Map of Boolean to ') || recvType:startsWith(prefix: 'Map:Boolean:') }, { return 'Int'; });
		if({ kSpecType == 'Float' || recvType:startsWith(prefix: 'Map of Float to ') || recvType:startsWith(prefix: 'Map:Float:') }, { return 'Flt'; });
		if({ kSpecType == 'String' || kSpecType == 'K' || kSpecType == 'Any' || recvType == 'Map' || recvType:startsWith(prefix: 'Map of String to ') || recvType:startsWith(prefix: 'Map:String:') || recvType:startsWith(prefix: 'Map of K ') || recvType:startsWith(prefix: 'Map:K:') || recvType:startsWith(prefix: 'Map of Any to ') || recvType:startsWith(prefix: 'Map:Any:') }, { return ''; });
		return 'Obj';
	}

	local Function of IrType is keyIrType(String is kSuf){
		if({ kSuf == 'Int' }, { return IrType:I64; });
		if({ kSuf == 'Flt' }, { return IrType:F64; });
		return IrType:Ptr;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		if({ call:name == 'init' }, {
			local String is dst: b:nextTmp();
			local String is resTy: expr:resolvedType;
			local Int is kk: 0;
			local Int is vk: 0;
			# A mangled instantiation's kinds are its own type arguments.
			local Boolean is argsDone: false;
			if({ b:specBaseMap:get(key: resTy, default: '') == 'Map' && b:specClassArgsMap:has(key: resTy) }, {
				local Array of Type is mArgs: b:specClassArgsMap:get(key: resTy, default: []);
				if({ mArgs:length() >= 1 }, { kk: b:mapKeyKindFor(specType: mArgs:get(index: 0, default: Type:init(name: '')):name); });
				if({ mArgs:length() >= 2 }, {
					local String is vArg: mArgs:get(index: 1, default: Type:init(name: '')):name;
					if({ b:isArcSpecType(specType: vArg) || vArg == 'Any' }, { vk: 1; });
				});
				argsDone: true;
			});
			if({ !argsDone }, {
				if({ resTy:startsWith(prefix: 'Map of Int to ') || resTy:startsWith(prefix: 'Map:Int:') || resTy:startsWith(prefix: 'Map of Boolean to ') || resTy:startsWith(prefix: 'Map:Boolean:') }, { kk: 1; });
				if({ resTy:startsWith(prefix: 'Map of Float to ') || resTy:startsWith(prefix: 'Map:Float:') }, { kk: 2; });
				if({ kk == 0 && resTy != 'Map' && resTy != '' && !resTy:startsWith(prefix: 'Map of String to ') && !resTy:startsWith(prefix: 'Map:String:') && !resTy:startsWith(prefix: 'Map of Any to ') && !resTy:startsWith(prefix: 'Map:Any:') }, { kk: 3; });
				if({ kk == 0 && (resTy == 'Map' || resTy == '') && b:expectedMapKeyType != '' }, {
					local String is ek: b:expectedMapKeyType;
					if({ ek == 'Int' || ek == 'Boolean' }, { kk: 1; });
					if({ ek == 'Float' }, { kk: 2; });
					if({ kk == 0 && ek != 'String' && ek != 'Any' }, { kk: 3; });
				});
			});
			if({ !argsDone }, {
				local Int is toIdx: resTy:indexOf(search: ' to ', default: -1);
				if({ toIdx >= 0 }, {
					local String is vSpec: resTy:substring(start: toIdx + 4, end: resTy:length());
					if({ b:isArcSpecType(specType: vSpec) || vSpec == 'Any' }, { vk: 1; });
				}, {
					if({ resTy:startsWith(prefix: 'Map:') }, {
						local String is afterMap: resTy:substring(start: 4, end: resTy:length());
						local Int is cIdx: afterMap:indexOf(search: ':', default: -1);
						if({ cIdx >= 0 }, {
							local String is vSpec2: afterMap:substring(start: cIdx + 1, end: afterMap:length());
							if({ b:isArcSpecType(specType: vSpec2) || vSpec2 == 'Any' }, { vk: 1; });
						});
					}, {
						if({ (resTy == 'Map' || resTy == '') && b:expectedMapValType != '' }, {
							if({ b:isArcSpecType(specType: b:expectedMapValType) || b:expectedMapValType == 'Any' }, { vk: 1; });
						});
					});
				});
			});
			if({ kk != 0 || vk != 0 }, {
				if({ kk == 0 && vk == 1 }, {
					b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapNewObject', argTypes: [], args: []));
				}, {
					local String is kkV: b:nextTmp();
					b:emit(inst: IrInst:ConstInt(dst: kkV, value: kk));
					local String is vkV: b:nextTmp();
					b:emit(inst: IrInst:ConstInt(dst: vkV, value: vk));
					b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapNewTyped', argTypes: [IrType:I64, IrType:I64], args: [kkV, vkV]));
				});
			}, {
				local String is kkV0: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: kkV0, value: 0));
				local String is vkV0: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: vkV0, value: 0));
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapNewTyped', argTypes: [IrType:I64, IrType:I64], args: [kkV0, vkV0]));
			});
			b:emitClaimPool(val: dst);
			return dst;
		});
		local String is mRecv: b:lowerExpr(expr: call:target);
		local String is res: '0';
		match(on: call:name, when: [
			'length': {
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'HashTable_mapLength', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', mRecv]));
				res: dst;
			},
			'keys': {
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapKeys', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', mRecv]));
				res: dst;
			},
			'remove': {
				local NamedArg is na0: call:args:get(index: 0);
				local Expression is kvExpr: na0:value;
				local String is kSuf: :keySuffix(recvType: call:target:resolvedType, kSpecType: kvExpr:resolvedType);
				local IrType is kArgTy: :keyIrType(kSuf: kSuf);
				local IrType is kty: b:irTypeFor(specType: kvExpr:resolvedType);
				local String is kv: b:castIfNeeded(val: b:lowerExpr(expr: kvExpr), fromTy: kty, toTy: kArgTy);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I1, callee: 'HashTable_mapRemove' . kSuf, argTypes: [IrType:Ptr, IrType:Ptr, kArgTy], args: ['null', mRecv, kv]));
				res: dst;
			},
			'has': {
				local NamedArg is na0: call:args:get(index: 0);
				local Expression is kvExpr: na0:value;
				local String is kSuf: :keySuffix(recvType: call:target:resolvedType, kSpecType: kvExpr:resolvedType);
				local IrType is kArgTy: :keyIrType(kSuf: kSuf);
				local IrType is kty: b:irTypeFor(specType: kvExpr:resolvedType);
				local String is kv: b:castIfNeeded(val: b:lowerExpr(expr: kvExpr), fromTy: kty, toTy: kArgTy);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I1, callee: 'HashTable_mapHas' . kSuf, argTypes: [IrType:Ptr, IrType:Ptr, kArgTy], args: ['null', mRecv, kv]));
				res: dst;
			},
			'set': {
				local NamedArg is na0: call:args:get(index: 0);
				local NamedArg is na1: call:args:get(index: 1);
				local Expression is kvExpr: na0:value;
				local String is kSuf: :keySuffix(recvType: call:target:resolvedType, kSpecType: kvExpr:resolvedType);
				local IrType is kArgTy: :keyIrType(kSuf: kSuf);
				local IrType is kty: b:irTypeFor(specType: kvExpr:resolvedType);
				local String is kv: b:castIfNeeded(val: b:lowerExpr(expr: kvExpr), fromTy: kty, toTy: kArgTy);
				local Expression is vvExpr: na1:value;
				local String is vv: b:lowerExpr(expr: vvExpr);
				local IrType is vty: b:irTypeFor(specType: vvExpr:resolvedType);
				local String is vp: b:castIfNeeded(val: vv, fromTy: vty, toTy: IrType:Ptr);
				local String is setCallee: 'HashTable_mapSet' . kSuf . 'Any';
				if({ b:isArcSpecType(specType: vvExpr:resolvedType) }, {
					setCallee: 'HashTable_mapSet' . kSuf;
				});
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: setCallee, argTypes: [IrType:Ptr, IrType:Ptr, kArgTy, IrType:Ptr], args: ['null', mRecv, kv, vp]));
			},
			['get', 'getString', 'getFloat']: {
				local NamedArg is na0: call:args:get(index: 0);
				local Expression is kvExpr: na0:value;
				local String is kSuf: :keySuffix(recvType: call:target:resolvedType, kSpecType: kvExpr:resolvedType);
				local IrType is kArgTy: :keyIrType(kSuf: kSuf);
				local IrType is kty: b:irTypeFor(specType: kvExpr:resolvedType);
				local String is kv: b:castIfNeeded(val: b:lowerExpr(expr: kvExpr), fromTy: kty, toTy: kArgTy);
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
				}, {
					if({ call:name == 'getString' || expr:resolvedType == 'String' }, {
						defV: b:nextTmp();
						local Int is esid: b:mod:internStringLiteral(value: '');
						b:emit(inst: IrInst:ConstString(dst: defV, strId: esid));
					});
				});
				local String is raw: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: raw, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapGet' . kSuf, argTypes: [IrType:Ptr, IrType:Ptr, kArgTy, IrType:Ptr], args: ['null', mRecv, kv, defV]));
				local IrType is mrTy: b:irTypeFor(specType: expr:resolvedType);
				if({ mrTy != IrType:Ptr && mrTy != IrType:Void }, {
					local String is casted: b:nextTmp();
					b:emit(inst: IrInst:IrCast(dst: casted, val: raw, fromType: IrType:Ptr, toType: mrTy));
					res: casted;
				}, {
					res: raw;
				});
			},
			['each', 'any', 'count', 'filter']: {
				local NamedArg is na0: call:args:get(index: 0);
				local IrType is kTy: IrType:Ptr;
				local IrType is vTy: IrType:Ptr;
				match(on: na0:value, when: [
					Expression:AnonFn: local Function(Type is _rt, Array of Parameter is fparams, Array of Statement is _fb){
						if({ fparams:length() >= 1 }, {
							local Parameter is p0: fparams:get(index: 0);
							kTy: b:irTypeFor(specType: p0:paramType:name);
							if({ kTy == IrType:Void }, { kTy: IrType:Ptr; });
						});
						if({ fparams:length() >= 2 }, {
							local Parameter is p1: fparams:get(index: 1);
							vTy: b:irTypeFor(specType: p1:paramType:name);
							if({ vTy == IrType:Void }, { vTy: IrType:Ptr; });
						});
					}
				], default: {});
				local String is cObj: b:lowerExpr(expr: na0:value);
				local String is fnPtrAddr: b:nextTmp();
				b:emit(inst: IrInst:FieldPtr(dst: fnPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 0));
				local String is fnPtrVal: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: fnPtrVal, slot: fnPtrAddr, ty: IrType:Ptr));
				local String is envPtrAddr: b:nextTmp();
				b:emit(inst: IrInst:FieldPtr(dst: envPtrAddr, objPtr: cObj, structName: 'SpecClosure', fieldIndex: 1));
				local String is envVal: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: envVal, slot: envPtrAddr, ty: IrType:Ptr));

				local String is keysArr: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: keysArr, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapKeys', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', mRecv]));
				local String is lenV: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: lenV, hasDst: true, retType: IrType:I64, callee: 'Vector_vecLength', argTypes: [IrType:Ptr, IrType:Ptr], args: ['null', keysArr]));

				local String is accSlot: '';
				local String is outMap: '';
				if({ call:name == 'any' }, {
					accSlot: '%many_r_' . (b:nextTmp());
					accSlot: '%many_r_' . (b:tmpCounter as String);
					b:emit(inst: IrInst:Alloca(slot: accSlot, ty: IrType:I1));
					local String is fV: b:nextTmp();
					b:emit(inst: IrInst:ConstBool(dst: fV, value: false));
					b:emit(inst: IrInst:Store(slot: accSlot, val: fV, ty: IrType:I1));
				});
				if({ call:name == 'count' }, {
					accSlot: '%mcnt_r_' . (b:nextTmp());
					accSlot: '%mcnt_r_' . (b:tmpCounter as String);
					b:emit(inst: IrInst:Alloca(slot: accSlot, ty: IrType:I64));
					local String is zV: b:nextTmp();
					b:emit(inst: IrInst:ConstInt(dst: zV, value: 0));
					b:emit(inst: IrInst:Store(slot: accSlot, val: zV, ty: IrType:I64));
				});
				local String is kSuf: :keySuffix(recvType: call:target:resolvedType, kSpecType: '');
				local IrType is kArgTy: :keyIrType(kSuf: kSuf);
				if({ call:name == 'filter' }, {
					outMap: b:nextTmp();
					if({ kSuf != '' }, {
						local Int is kk: 3;
						if({ kSuf == 'Int' }, { kk: 1; });
						if({ kSuf == 'Flt' }, { kk: 2; });
						local String is kkV: b:nextTmp();
						b:emit(inst: IrInst:ConstInt(dst: kkV, value: kk));
						local String is vkV: b:nextTmp();
						b:emit(inst: IrInst:ConstInt(dst: vkV, value: 0));
						b:emit(inst: IrInst:IrCall(dst: outMap, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapNewTyped', argTypes: [IrType:I64, IrType:I64], args: [kkV, vkV]));
					}, {
						local String is kkV0: b:nextTmp();
						b:emit(inst: IrInst:ConstInt(dst: kkV0, value: 0));
						local String is vkV0: b:nextTmp();
						b:emit(inst: IrInst:ConstInt(dst: vkV0, value: 0));
						b:emit(inst: IrInst:IrCall(dst: outMap, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapNewTyped', argTypes: [IrType:I64, IrType:I64], args: [kkV0, vkV0]));
					});
					b:emitClaimPool(val: outMap);
				});

				local String is idxSlot: '%meach_i_' . (b:nextTmp());
				idxSlot: '%meach_i_' . (b:tmpCounter as String);
				b:emit(inst: IrInst:Alloca(slot: idxSlot, ty: IrType:I64));
				local String is zeroV: b:nextTmp();
				b:emit(inst: IrInst:ConstInt(dst: zeroV, value: 0));
				b:emit(inst: IrInst:Store(slot: idxSlot, val: zeroV, ty: IrType:I64));

				local String is hdrLbl: b:nextLabel(prefix: 'meach_hdr');
				local String is bodyLbl: b:nextLabel(prefix: 'meach_body');
				local String is endLbl: b:nextLabel(prefix: 'meach_end');
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
				local String is rawK: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: rawK, hasDst: true, retType: IrType:Ptr, callee: 'Vector_vecGetChecked', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64], args: ['null', keysArr, curI]));
				local String is kCast: b:castIfNeeded(val: rawK, fromTy: IrType:Ptr, toTy: kArgTy);
				local String is rawV: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: rawV, hasDst: true, retType: IrType:Ptr, callee: 'HashTable_mapGet' . kSuf, argTypes: [IrType:Ptr, IrType:Ptr, kArgTy, IrType:Ptr], args: ['null', mRecv, kCast, 'null']));
				local String is kVal: b:castIfNeeded(val: rawK, fromTy: IrType:Ptr, toTy: kTy);
				local String is vVal: b:castIfNeeded(val: rawV, fromTy: IrType:Ptr, toTy: vTy);

				local String is stepLbl: b:nextLabel(prefix: 'meach_step');
				if({ call:name == 'each' }, {
					b:emit(inst: IrInst:IndirectCall(dst: '', hasDst: false, retType: IrType:Void, fnPtr: fnPtrVal, argTypes: [IrType:Ptr, kTy, vTy], args: [envVal, kVal, vVal]));
					b:terminate(inst: IrInst:Br(target: stepLbl));
				}, {
					local String is pRes: b:nextTmp();
					b:emit(inst: IrInst:IndirectCall(dst: pRes, hasDst: true, retType: IrType:I1, fnPtr: fnPtrVal, argTypes: [IrType:Ptr, kTy, vTy], args: [envVal, kVal, vVal]));
					local String is hitLbl: b:nextLabel(prefix: 'meach_hit');
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
						b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'HashTable_mapSet' . kSuf . 'Any', argTypes: [IrType:Ptr, IrType:Ptr, kArgTy, IrType:Ptr], args: ['null', outMap, kCast, rawV]));
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
				if({ call:name == 'filter' }, {
					res: outMap;
				});
			}
		]);
		return res;
	}
}
