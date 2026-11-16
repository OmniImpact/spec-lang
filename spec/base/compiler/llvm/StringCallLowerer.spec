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
		['base', 'compiler', 'ir', IrBlock],
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
		local String is nm: call:name;
		local Boolean is isBuf: (call:bareProvider == 'Buf' || call:bareProvider:endsWith(suffix: ':Buf'));
		local Boolean is isStrIdent: false;
		match(on: call:target, when: [
			Expression:Ident: local Function(String is tn){
				if({ tn == 'Buf' }, { isBuf: true; });
				if({ tn == 'String' }, { isStrIdent: true; });
			},
			Expression:Path: local Function(Array of String is segs){
				if({ segs:length() > 0 && segs:get(index: segs:length() - 1, default: '') == 'Buf' }, { isBuf: true; });
			}
		], default: {});
		if({ isBuf }, {
			if({ nm == 'init' || nm == 'bufLength' || nm == 'bufGetByte' || nm == 'bufCountByte' || nm == 'bufAppendBuf' || nm == 'intern' || nm == 'stringCopy' || nm == 'stringIndexOf' || nm == 'stringIndexOfFrom' || nm == 'stringSubstring' }, { return true; });
		});
		if({ isStrIdent && nm == 'fromCharCode' && call:args:length() >= 1 }, { return true; });
		if({ isStrIdent && nm == 'newline' && call:args:length() == 0 }, { return true; });
		if({ nm == 'toBase' && call:target:resolvedType == 'Int' }, { return true; });
		if({ call:target:resolvedType != 'String' }, { return false; });
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: nm, when: [
			['length', 'isEmpty']: { ok: true; },
			['contains', 'startsWith', 'endsWith', 'indexOf', 'charAt', 'byteAt']: { ok: argc >= 1; },
			['substring', 'indexOfFrom']: { ok: argc >= 2; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		local Boolean is isBuf: (call:bareProvider == 'Buf' || call:bareProvider:endsWith(suffix: ':Buf'));
		match(on: call:target, when: [
			Expression:Ident: local Function(String is tn){
				if({ tn == 'Buf' }, { isBuf: true; });
			},
			Expression:Path: local Function(Array of String is segs){
				if({ segs:length() > 0 && segs:get(index: segs:length() - 1, default: '') == 'Buf' }, { isBuf: true; });
			}
		], default: {});
		if({ nm == 'newline' }, {
			local Int is sidNl: b:mod:internStringLiteral(value: "\n");
			local String is dstNl: b:nextTmp();
			b:emit(inst: IrInst:ConstString(dst: dstNl, strId: sidNl));
			return dstNl;
		});
		if({ nm == 'toBase' && call:target:resolvedType == 'Int' }, {
			local String is iv: b:lowerExpr(expr: call:target);
			local String is baseV: '10';
			local String is digV: '0';
			if({ call:args:length() >= 1 }, {
				local NamedArg is na0: call:args:get(index: 0);
				if({ na0:name == 'digits' }, { digV: b:lowerExpr(expr: na0:value); }, { baseV: b:lowerExpr(expr: na0:value); });
			});
			if({ call:args:length() >= 2 }, {
				local NamedArg is na1: call:args:get(index: 1);
				if({ na1:name == 'base' }, { baseV: b:lowerExpr(expr: na1:value); }, { digV: b:lowerExpr(expr: na1:value); });
			});
			local String is dst: b:nextTmp();
			b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_int_to_base', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [iv, baseV, digV]));
			b:emitClaimPool(val: dst);
			return dst;
		});
		if({ isBuf }, {
			if({ nm == 'init' }, { return 'null'; });
			local NamedArg is ba0: call:args:get(index: 0);
			local String is bufArg: b:lowerExpr(expr: ba0:value);
			if({ nm == 'bufLength' }, {
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_string_length', argTypes: [IrType:Ptr], args: [bufArg]));
				return dst;
			});
			if({ nm == 'stringCopy' }, {
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_copy', argTypes: [IrType:Ptr], args: [bufArg]));
				b:emitClaimPool(val: dst);
				return dst;
			});
			if({ nm == 'intern' }, {
				local String is cstr: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: cstr, hasDst: true, retType: IrType:Ptr, callee: 'spec_buf_to_cstring', argTypes: [IrType:Ptr], args: [bufArg]));
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_intern', argTypes: [IrType:Ptr], args: [cstr]));
				return dst;
			});
			if({ nm == 'bufAppendBuf' }, {
				local NamedArg is ba1: call:args:get(index: 1);
				local String is srcArg: b:lowerExpr(expr: ba1:value);
				b:emit(inst: IrInst:IrCall(dst: '', hasDst: false, retType: IrType:Void, callee: 'spec_buf_append_buf', argTypes: [IrType:Ptr, IrType:Ptr], args: [bufArg, srcArg]));
				return '0';
			});
			if({ nm == 'bufCountByte' }, {
				local NamedArg is ba1: call:args:get(index: 1);
				local String is byteArg: b:lowerExpr(expr: ba1:value);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_buf_count_byte', argTypes: [IrType:Ptr, IrType:I64], args: [bufArg, byteArg]));
				return dst;
			});
			if({ nm == 'bufGetByte' }, {
				local NamedArg is ba1: call:args:get(index: 1);
				local NamedArg is ba2: call:args:get(index: 2);
				local String is idxArg: b:lowerExpr(expr: ba1:value);
				local String is defArg: b:lowerExpr(expr: ba2:value);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_buf_get_byte', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [bufArg, idxArg, defArg]));
				return dst;
			});
			if({ nm == 'stringIndexOf' }, {
				local NamedArg is ba1: call:args:get(index: 1);
				local NamedArg is ba2: call:args:get(index: 2);
				local String is ndlArg: b:lowerExpr(expr: ba1:value);
				local String is defArg: b:lowerExpr(expr: ba2:value);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_string_index_of', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64], args: [bufArg, ndlArg, defArg]));
				return dst;
			});
			if({ nm == 'stringIndexOfFrom' }, {
				local NamedArg is ba1: call:args:get(index: 1);
				local NamedArg is ba2: call:args:get(index: 2);
				local NamedArg is ba3: call:args:get(index: 3);
				local String is ndlArg: b:lowerExpr(expr: ba1:value);
				local String is fromArg: b:lowerExpr(expr: ba2:value);
				local String is defArg: b:lowerExpr(expr: ba3:value);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_string_index_of_from', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64, IrType:I64], args: [bufArg, ndlArg, fromArg, defArg]));
				return dst;
			});
			if({ nm == 'stringSubstring' }, {
				local NamedArg is ba1: call:args:get(index: 1);
				local NamedArg is ba2: call:args:get(index: 2);
				local String is stArg: b:lowerExpr(expr: ba1:value);
				local String is enArg: b:lowerExpr(expr: ba2:value);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_substring', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [bufArg, stArg, enArg]));
				b:emitClaimPool(val: dst);
				return dst;
			});
		});
		if({ nm == 'fromCharCode' }, {
			local NamedArg is na0: call:args:get(index: 0);
			local String is codeVal: b:lowerExpr(expr: na0:value);
			local String is dst: b:nextTmp();
			b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_from_char_code', argTypes: [IrType:I64], args: [codeVal]));
			b:emitClaimPool(val: dst);
			return dst;
		});
		local String is sRecv: b:lowerExpr(expr: call:target);
		local String is res: '0';
		match(on: call:name, when: [
			'length': {
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_string_length', argTypes: [IrType:Ptr], args: [sRecv]));
				res: dst;
			},
			'isEmpty': {
				local String is lenTmp: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: lenTmp, hasDst: true, retType: IrType:I64, callee: 'spec_string_length', argTypes: [IrType:Ptr], args: [sRecv]));
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:Cmp(dst: dst, op: '==', lhs: lenTmp, rhs: '0', ty: IrType:I64));
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
			'indexOf': {
				local NamedArg is na0: call:args:get(index: 0);
				local String is needle: b:lowerExpr(expr: na0:value);
				local String is defVal: '-1';
				if({ call:args:length() >= 2 }, {
					local NamedArg is na1: call:args:get(index: 1);
					defVal: b:lowerExpr(expr: na1:value);
				});
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_string_index_of', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64], args: [sRecv, needle, defVal]));
				res: dst;
			},
			'indexOfFrom': {
				local NamedArg is na0: call:args:get(index: 0);
				local NamedArg is na1: call:args:get(index: 1);
				local String is needle: b:lowerExpr(expr: na0:value);
				local String is fromIdx: b:lowerExpr(expr: na1:value);
				local String is defVal: '-1';
				if({ call:args:length() >= 3 }, {
					local NamedArg is na2: call:args:get(index: 2);
					defVal: b:lowerExpr(expr: na2:value);
				});
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_string_index_of_from', argTypes: [IrType:Ptr, IrType:Ptr, IrType:I64, IrType:I64], args: [sRecv, needle, fromIdx, defVal]));
				res: dst;
			},
			'byteAt': {
				local NamedArg is na0: call:args:get(index: 0);
				local String is idxVal: b:lowerExpr(expr: na0:value);
				local String is defVal: '-1';
				if({ call:args:length() >= 2 }, {
					local NamedArg is na1: call:args:get(index: 1);
					defVal: b:lowerExpr(expr: na1:value);
				});
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: dst, hasDst: true, retType: IrType:I64, callee: 'spec_buf_get_byte', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [sRecv, idxVal, defVal]));
				res: dst;
			},
			'charAt': {
				local NamedArg is na0: call:args:get(index: 0);
				local String is idxVal: b:lowerExpr(expr: na0:value);
				local String is defVal: 'null';
				if({ call:args:length() >= 2 }, {
					local NamedArg is na1: call:args:get(index: 1);
					defVal: b:lowerExpr(expr: na1:value);
				}, {
					local Int is sid: b:mod:internStringLiteral(value: '');
					defVal: b:nextTmp();
					b:emit(inst: IrInst:ConstString(dst: defVal, strId: sid));
				});
				local String is byteVal: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: byteVal, hasDst: true, retType: IrType:I64, callee: 'spec_buf_get_byte', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [sRecv, idxVal, '-1']));
				local String is isOob: b:nextTmp();
				b:emit(inst: IrInst:Cmp(dst: isOob, op: '<', lhs: byteVal, rhs: '0', ty: IrType:I64));
				local String is _ctmp: b:nextTmp();
				local String is chSlot: '%charat_' . (b:tmpCounter as String);
				b:emit(inst: IrInst:Alloca(slot: chSlot, ty: IrType:Ptr));
				local String is oobLbl: b:nextLabel(prefix: 'charat_oob');
				local String is okLbl: b:nextLabel(prefix: 'charat_ok');
				local String is endLbl: b:nextLabel(prefix: 'charat_end');
				b:terminate(inst: IrInst:CondBr(cond: isOob, thenLabel: oobLbl, elseLabel: okLbl));

				local IrBlock is oobBlk: b:curFn:addBlock(label: oobLbl);
				b:switchBlock(blk: oobBlk);
				b:emit(inst: IrInst:Store(slot: chSlot, val: defVal, ty: IrType:Ptr));
				b:terminate(inst: IrInst:Br(target: endLbl));

				local IrBlock is okBlk: b:curFn:addBlock(label: okLbl);
				b:switchBlock(blk: okBlk);
				local String is chVal: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: chVal, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_from_char_code', argTypes: [IrType:I64], args: [byteVal]));
				b:emitClaimPool(val: chVal);
				b:emit(inst: IrInst:Store(slot: chSlot, val: chVal, ty: IrType:Ptr));
				b:terminate(inst: IrInst:Br(target: endLbl));

				local IrBlock is endBlk: b:curFn:addBlock(label: endLbl);
				b:switchBlock(blk: endBlk);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:Load(dst: dst, slot: chSlot, ty: IrType:Ptr));
				res: dst;
			},
			'startsWith': {
				local NamedArg is na0: call:args:get(index: 0);
				local String is pfx: b:lowerExpr(expr: na0:value);
				local String is slen: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: slen, hasDst: true, retType: IrType:I64, callee: 'spec_string_length', argTypes: [IrType:Ptr], args: [sRecv]));
				local String is plen: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: plen, hasDst: true, retType: IrType:I64, callee: 'spec_string_length', argTypes: [IrType:Ptr], args: [pfx]));
				local String is sub: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: sub, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_substring', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [sRecv, '0', plen]));
				local String is eq: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: eq, hasDst: true, retType: IrType:I1, callee: 'spec_string_equals', argTypes: [IrType:Ptr, IrType:Ptr], args: [sub, pfx]));
				local String is lenOk: b:nextTmp();
				b:emit(inst: IrInst:Cmp(dst: lenOk, op: '>=', lhs: slen, rhs: plen, ty: IrType:I64));
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:BinOp(dst: dst, op: '&', lhs: lenOk, rhs: eq, ty: IrType:I1));
				res: dst;
			},
			'endsWith': {
				local NamedArg is na0: call:args:get(index: 0);
				local String is sfx: b:lowerExpr(expr: na0:value);
				local String is slen: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: slen, hasDst: true, retType: IrType:I64, callee: 'spec_string_length', argTypes: [IrType:Ptr], args: [sRecv]));
				local String is xlen: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: xlen, hasDst: true, retType: IrType:I64, callee: 'spec_string_length', argTypes: [IrType:Ptr], args: [sfx]));
				local String is startIdx: b:nextTmp();
				b:emit(inst: IrInst:BinOp(dst: startIdx, op: '-', lhs: slen, rhs: xlen, ty: IrType:I64));
				local String is sub: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: sub, hasDst: true, retType: IrType:Ptr, callee: 'spec_string_substring', argTypes: [IrType:Ptr, IrType:I64, IrType:I64], args: [sRecv, startIdx, slen]));
				local String is eq: b:nextTmp();
				b:emit(inst: IrInst:IrCall(dst: eq, hasDst: true, retType: IrType:I1, callee: 'spec_string_equals', argTypes: [IrType:Ptr, IrType:Ptr], args: [sub, sfx]));
				local String is lenOk: b:nextTmp();
				b:emit(inst: IrInst:Cmp(dst: lenOk, op: '>=', lhs: slen, rhs: xlen, ty: IrType:I64));
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:BinOp(dst: dst, op: '&', lhs: lenOk, rhs: eq, ty: IrType:I1));
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
