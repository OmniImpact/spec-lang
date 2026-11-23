#! Package base:compiler:llvm
#! Lowers data-optimal methods on the Byte primitive directly to native i8 IR.
#! Byte shares UInt8's zero-overhead 1-byte native representation while providing
#! convenience methods for binary data, bit manipulation, and ASCII classification.

Class of CallLowerer is ByteCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', CallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ast', Primitive],
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(){
		return;
	}

	replace Function of String is name(){
		return 'ByteCallLowerer';
	}

	replace Function of Int is order(){
		return 35;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		return call:target:getResolvedTypeNode():primitive() == Primitive:BYTE;
	}

	local Function of String is constI8(IrBuilder is b, Int is v){
		local String is tmp: b:nextTmp();
		b:emit(inst: IrInst:ConstIntTy(dst: tmp, value: v, ty: IrType:I8));
		return tmp;
	}

	local Function of String is inRange(IrBuilder is b, String is val, Int is lo, Int is hi){
		local String is cLo: :constI8(b: b, v: lo);
		local String is cHi: :constI8(b: b, v: hi);
		local String is geLo: b:nextTmp();
		b:emit(inst: IrInst:Cmp(dst: geLo, op: 'u>=', lhs: val, rhs: cLo, ty: IrType:I8));
		local String is leHi: b:nextTmp();
		b:emit(inst: IrInst:Cmp(dst: leHi, op: 'u<=', lhs: val, rhs: cHi, ty: IrType:I8));
		local String is res: b:nextTmp();
		b:emit(inst: IrInst:BinOp(dst: res, op: '&', lhs: geLo, rhs: leHi, ty: IrType:I1));
		return res;
	}

	local Function of String is eqI8(IrBuilder is b, String is val, Int is k){
		local String is ck: :constI8(b: b, v: k);
		local String is res: b:nextTmp();
		b:emit(inst: IrInst:Cmp(dst: res, op: '==', lhs: val, rhs: ck, ty: IrType:I8));
		return res;
	}

	local Function of String is addTermI64(IrBuilder is b, String is acc, String is condI1, String is valI64){
		local String is c64: b:castIfNeededUnsigned(val: condI1, fromTy: IrType:I1, toTy: IrType:I64);
		local String is prod: b:nextTmp();
		b:emit(inst: IrInst:BinOp(dst: prod, op: '*', lhs: c64, rhs: valI64, ty: IrType:I64));
		local String is sum: b:nextTmp();
		b:emit(inst: IrInst:BinOp(dst: sum, op: '+', lhs: acc, rhs: prod, ty: IrType:I64));
		return sum;
	}

	local Function of String is addTermI8(IrBuilder is b, String is acc, String is condI1, String is valI8){
		local String is c8: b:castIfNeededUnsigned(val: condI1, fromTy: IrType:I1, toTy: IrType:I8);
		local String is prod: b:nextTmp();
		b:emit(inst: IrInst:BinOp(dst: prod, op: '*', lhs: c8, rhs: valI8, ty: IrType:I8));
		local String is sum: b:nextTmp();
		b:emit(inst: IrInst:BinOp(dst: sum, op: '+', lhs: acc, rhs: prod, ty: IrType:I8));
		return sum;
	}

	local Function of String is lowerArgI8(IrBuilder is b, CallData is call){
		if({ call:args:length() == 0 }, {
			return :constI8(b: b, v: 0);
		});
		local NamedArg is na0: call:args:get(index: 0);
		local String is raw: b:lowerExpr(expr: na0:value);
		local IrType is aTy: b:irTypeForNode(t: na0:value:getResolvedTypeNode());
		return b:castIfNeededUnsigned(val: raw, fromTy: aTy, toTy: IrType:I8);
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is bv: b:lowerExpr(expr: call:target);
		local String is m: call:name;

		if({ m == 'toUInt8' }, {
			return bv;
		});
		if({ m == 'toInt' }, {
			return b:castIfNeededUnsigned(val: bv, fromTy: IrType:I8, toTy: IrType:I64);
		});
		if({ m == 'toHex' }, {
			local String is i64v: b:castIfNeededUnsigned(val: bv, fromTy: IrType:I8, toTy: IrType:I64);
			local String is base16: b:nextTmp();
			b:emit(inst: IrInst:ConstInt(dst: base16, value: 16));
			local String is digits2: b:nextTmp();
			b:emit(inst: IrInst:ConstInt(dst: digits2, value: 2));
			local String is dstH: b:nextTmp();
			b:emit(inst: IrInst:IrCall(dst: dstH, hasDst: true, retType: IrType:Ptr, callee: 'Str_intToBase', argTypes: [IrType:Ptr, IrType:I64, IrType:I64, IrType:I64], args: ['null', i64v, base16, digits2]));
			return dstH;
		});
		if({ m == 'highNibble' }, {
			local String is c4: :constI8(b: b, v: 4);
			local String is res: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: res, op: '>>>', lhs: bv, rhs: c4, ty: IrType:I8));
			return res;
		});
		if({ m == 'lowNibble' }, {
			local String is c15: :constI8(b: b, v: 15);
			local String is res: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: res, op: '&', lhs: bv, rhs: c15, ty: IrType:I8));
			return res;
		});
		if({ m == 'bit' }, {
			local String is idx: :lowerArgI8(b: b, call: call);
			local String is sh: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: sh, op: '>>>', lhs: bv, rhs: idx, ty: IrType:I8));
			local String is c1: :constI8(b: b, v: 1);
			local String is masked: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: masked, op: '&', lhs: sh, rhs: c1, ty: IrType:I8));
			local String is c0: :constI8(b: b, v: 0);
			local String is res: b:nextTmp();
			b:emit(inst: IrInst:Cmp(dst: res, op: '!=', lhs: masked, rhs: c0, ty: IrType:I8));
			return res;
		});
		if({ m == 'setBit' || m == 'clearBit' || m == 'toggleBit' }, {
			local String is idx: :lowerArgI8(b: b, call: call);
			local String is c1: :constI8(b: b, v: 1);
			local String is mask: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: mask, op: '<<', lhs: c1, rhs: idx, ty: IrType:I8));
			if({ m == 'setBit' }, {
				local String is res: b:nextTmp();
				b:emit(inst: IrInst:BinOp(dst: res, op: '|', lhs: bv, rhs: mask, ty: IrType:I8));
				return res;
			});
			if({ m == 'clearBit' }, {
				local String is inv: b:nextTmp();
				b:emit(inst: IrInst:UnaryOp(dst: inv, op: '~', operand: mask, ty: IrType:I8));
				local String is res: b:nextTmp();
				b:emit(inst: IrInst:BinOp(dst: res, op: '&', lhs: bv, rhs: inv, ty: IrType:I8));
				return res;
			});
			local String is res: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: res, op: '^', lhs: bv, rhs: mask, ty: IrType:I8));
			return res;
		});
		if({ m == 'rotateLeft' || m == 'rotateRight' }, {
			local String is rawN: :lowerArgI8(b: b, call: call);
			local String is c7: :constI8(b: b, v: 7);
			local String is n: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: n, op: '&', lhs: rawN, rhs: c7, ty: IrType:I8));
			local String is c8: :constI8(b: b, v: 8);
			local String is diff: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: diff, op: '-', lhs: c8, rhs: n, ty: IrType:I8));
			local String is comp: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: comp, op: '&', lhs: diff, rhs: c7, ty: IrType:I8));
			local String is p1: b:nextTmp();
			local String is p2: b:nextTmp();
			if({ m == 'rotateLeft' }, {
				b:emit(inst: IrInst:BinOp(dst: p1, op: '<<', lhs: bv, rhs: n, ty: IrType:I8));
				b:emit(inst: IrInst:BinOp(dst: p2, op: '>>>', lhs: bv, rhs: comp, ty: IrType:I8));
			}, {
				b:emit(inst: IrInst:BinOp(dst: p1, op: '>>>', lhs: bv, rhs: n, ty: IrType:I8));
				b:emit(inst: IrInst:BinOp(dst: p2, op: '<<', lhs: bv, rhs: comp, ty: IrType:I8));
			});
			local String is res: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: res, op: '|', lhs: p1, rhs: p2, ty: IrType:I8));
			return res;
		});
		if({ m == 'isAscii' }, {
			local String is c128: :constI8(b: b, v: 128);
			local String is res: b:nextTmp();
			b:emit(inst: IrInst:Cmp(dst: res, op: 'u<', lhs: bv, rhs: c128, ty: IrType:I8));
			return res;
		});
		if({ m == 'isDigit' }, {
			return :inRange(b: b, val: bv, lo: 48, hi: 57);
		});
		if({ m == 'isAlpha' }, {
			local String is up: :inRange(b: b, val: bv, lo: 65, hi: 90);
			local String is lo: :inRange(b: b, val: bv, lo: 97, hi: 122);
			local String is res: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: res, op: '|', lhs: up, rhs: lo, ty: IrType:I1));
			return res;
		});
		if({ m == 'isAlphaNum' }, {
			local String is up: :inRange(b: b, val: bv, lo: 65, hi: 90);
			local String is lo: :inRange(b: b, val: bv, lo: 97, hi: 122);
			local String is dg: :inRange(b: b, val: bv, lo: 48, hi: 57);
			local String is a: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: a, op: '|', lhs: up, rhs: lo, ty: IrType:I1));
			local String is res: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: res, op: '|', lhs: a, rhs: dg, ty: IrType:I1));
			return res;
		});
		if({ m == 'isHexDigit' }, {
			local String is dg: :inRange(b: b, val: bv, lo: 48, hi: 57);
			local String is up: :inRange(b: b, val: bv, lo: 65, hi: 70);
			local String is lo: :inRange(b: b, val: bv, lo: 97, hi: 102);
			local String is a: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: a, op: '|', lhs: dg, rhs: up, ty: IrType:I1));
			local String is res: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: res, op: '|', lhs: a, rhs: lo, ty: IrType:I1));
			return res;
		});
		if({ m == 'isWhitespace' }, {
			local String is c32: :constI8(b: b, v: 32);
			local String is c9: :constI8(b: b, v: 9);
			local String is c10: :constI8(b: b, v: 10);
			local String is c13: :constI8(b: b, v: 13);
			local String is e1: b:nextTmp();
			b:emit(inst: IrInst:Cmp(dst: e1, op: '==', lhs: bv, rhs: c32, ty: IrType:I8));
			local String is e2: b:nextTmp();
			b:emit(inst: IrInst:Cmp(dst: e2, op: '==', lhs: bv, rhs: c9, ty: IrType:I8));
			local String is e3: b:nextTmp();
			b:emit(inst: IrInst:Cmp(dst: e3, op: '==', lhs: bv, rhs: c10, ty: IrType:I8));
			local String is e4: b:nextTmp();
			b:emit(inst: IrInst:Cmp(dst: e4, op: '==', lhs: bv, rhs: c13, ty: IrType:I8));
			local String is o1: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: o1, op: '|', lhs: e1, rhs: e2, ty: IrType:I1));
			local String is o2: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: o2, op: '|', lhs: e3, rhs: e4, ty: IrType:I1));
			local String is res: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: res, op: '|', lhs: o1, rhs: o2, ty: IrType:I1));
			return res;
		});
		if({ m == 'isPrintable' }, {
			return :inRange(b: b, val: bv, lo: 32, hi: 126);
		});
		if({ m == 'toUpper' || m == 'toLower' }, {
			local String is cond: if({ m == 'toUpper' }, { :inRange(b: b, val: bv, lo: 97, hi: 122) }, { :inRange(b: b, val: bv, lo: 65, hi: 90) });
			local String is condI8: b:castIfNeededUnsigned(val: cond, fromTy: IrType:I1, toTy: IrType:I8);
			local String is c32: :constI8(b: b, v: 32);
			local String is delta: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: delta, op: '*', lhs: condI8, rhs: c32, ty: IrType:I8));
			local String is res: b:nextTmp();
			local String is adjOp: if({ m == 'toUpper' }, { '-' }, { '+' });
			b:emit(inst: IrInst:BinOp(dst: res, op: adjOp, lhs: bv, rhs: delta, ty: IrType:I8));
			return res;
		});
		if({ m == 'isBase64' }, {
			local String is up: :inRange(b: b, val: bv, lo: 65, hi: 90);
			local String is lo: :inRange(b: b, val: bv, lo: 97, hi: 122);
			local String is dg: :inRange(b: b, val: bv, lo: 48, hi: 57);
			local String is pl: :eqI8(b: b, val: bv, k: 43);
			local String is sl: :eqI8(b: b, val: bv, k: 47);
			local String is o1: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: o1, op: '|', lhs: up, rhs: lo, ty: IrType:I1));
			local String is o2: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: o2, op: '|', lhs: dg, rhs: pl, ty: IrType:I1));
			local String is o3: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: o3, op: '|', lhs: o1, rhs: o2, ty: IrType:I1));
			local String is res: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: res, op: '|', lhs: o3, rhs: sl, ty: IrType:I1));
			return res;
		});
		if({ m == 'base64Value' }, {
			local String is up: :inRange(b: b, val: bv, lo: 65, hi: 90);
			local String is lo: :inRange(b: b, val: bv, lo: 97, hi: 122);
			local String is dg: :inRange(b: b, val: bv, lo: 48, hi: 57);
			local String is pl: :eqI8(b: b, val: bv, k: 43);
			local String is sl: :eqI8(b: b, val: bv, k: 47);
			local String is o1: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: o1, op: '|', lhs: up, rhs: lo, ty: IrType:I1));
			local String is o2: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: o2, op: '|', lhs: dg, rhs: pl, ty: IrType:I1));
			local String is o3: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: o3, op: '|', lhs: o1, rhs: o2, ty: IrType:I1));
			local String is valid: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: valid, op: '|', lhs: o3, rhs: sl, ty: IrType:I1));
			local String is invalid: b:nextTmp();
			b:emit(inst: IrInst:UnaryOp(dst: invalid, op: '!', operand: valid, ty: IrType:I1));

			local String is b64: b:castIfNeededUnsigned(val: bv, fromTy: IrType:I8, toTy: IrType:I64);
			local String is c65: b:nextTmp();
			b:emit(inst: IrInst:ConstInt(dst: c65, value: 65));
			local String is vUp: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: vUp, op: '-', lhs: b64, rhs: c65, ty: IrType:I64));
			local String is c71: b:nextTmp();
			b:emit(inst: IrInst:ConstInt(dst: c71, value: 71));
			local String is vLo: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: vLo, op: '-', lhs: b64, rhs: c71, ty: IrType:I64));
			local String is c4: b:nextTmp();
			b:emit(inst: IrInst:ConstInt(dst: c4, value: 4));
			local String is vDg: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: vDg, op: '+', lhs: b64, rhs: c4, ty: IrType:I64));
			local String is vPl: b:nextTmp();
			b:emit(inst: IrInst:ConstInt(dst: vPl, value: 62));
			local String is vSl: b:nextTmp();
			b:emit(inst: IrInst:ConstInt(dst: vSl, value: 63));
			local String is vInv: b:nextTmp();
			b:emit(inst: IrInst:ConstInt(dst: vInv, value: -1));
			local String is acc: b:nextTmp();
			b:emit(inst: IrInst:ConstInt(dst: acc, value: 0));
			acc: :addTermI64(b: b, acc: acc, condI1: up, valI64: vUp);
			acc: :addTermI64(b: b, acc: acc, condI1: lo, valI64: vLo);
			acc: :addTermI64(b: b, acc: acc, condI1: dg, valI64: vDg);
			acc: :addTermI64(b: b, acc: acc, condI1: pl, valI64: vPl);
			acc: :addTermI64(b: b, acc: acc, condI1: sl, valI64: vSl);
			acc: :addTermI64(b: b, acc: acc, condI1: invalid, valI64: vInv);
			return acc;
		});
		if({ m == 'toBase64Char' }, {
			local String is c63: :constI8(b: b, v: 63);
			local String is v: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: v, op: '&', lhs: bv, rhs: c63, ty: IrType:I8));
			local String is rUp: :inRange(b: b, val: v, lo: 0, hi: 25);
			local String is rLo: :inRange(b: b, val: v, lo: 26, hi: 51);
			local String is rDg: :inRange(b: b, val: v, lo: 52, hi: 61);
			local String is rPl: :eqI8(b: b, val: v, k: 62);
			local String is rSl: :eqI8(b: b, val: v, k: 63);

			local String is c65: :constI8(b: b, v: 65);
			local String is chUp: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: chUp, op: '+', lhs: v, rhs: c65, ty: IrType:I8));
			local String is c71: :constI8(b: b, v: 71);
			local String is chLo: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: chLo, op: '+', lhs: v, rhs: c71, ty: IrType:I8));
			local String is c4: :constI8(b: b, v: 4);
			local String is chDg: b:nextTmp();
			b:emit(inst: IrInst:BinOp(dst: chDg, op: '-', lhs: v, rhs: c4, ty: IrType:I8));
			local String is chPl: :constI8(b: b, v: 43);
			local String is chSl: :constI8(b: b, v: 47);

			local String is acc: :constI8(b: b, v: 0);
			acc: :addTermI8(b: b, acc: acc, condI1: rUp, valI8: chUp);
			acc: :addTermI8(b: b, acc: acc, condI1: rLo, valI8: chLo);
			acc: :addTermI8(b: b, acc: acc, condI1: rDg, valI8: chDg);
			acc: :addTermI8(b: b, acc: acc, condI1: rPl, valI8: chPl);
			acc: :addTermI8(b: b, acc: acc, condI1: rSl, valI8: chSl);
			return acc;
		});
		return bv;
	}
}
