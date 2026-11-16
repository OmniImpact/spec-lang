#! Package base:compiler:llvm
#! Lowers Math sysinternal calls to Spec IR.

Class of SysinternalCallLowerer is MathCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', SysinternalCallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(){
		return;
	}

	replace Function of String is name(){
		return 'MathCallLowerer';
	}

	replace Function of Int is order(){
		return 43;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		local String is r: self:receiverName(call: call);
		if({ r != '' && r != 'Math' }, { return false; });
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: call:name, when: [
			'init': { ok: r == 'Math'; },
			['fastRandom', 'fast_random', 'random']: { ok: true; },
			['fastRandomSeed']: { ok: argc >= 1; },
			['toInt', 'math_to_int', 'toFloat', 'math_to_float', 'sqrt', 'math_sqrt', 'cbrt', 'math_cbrt', 'sin', 'math_sin', 'cos', 'math_cos', 'tan', 'math_tan', 'asin', 'math_asin', 'acos', 'math_acos', 'atan', 'math_atan', 'exp', 'math_exp', 'log', 'math_log', 'log2', 'math_log2', 'log10', 'math_log10', 'round', 'ceil', 'floor', 'abs']: { ok: argc >= 1; },
			['atan2', 'math_atan2', 'pow', 'math_pow', 'min', 'max']: { ok: argc >= 2; },
			['fma', 'math_fma']: { ok: argc >= 3; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		local String is res: '0';
		match(on: nm, when: [
			'init': { res: 'null'; },
			['fastRandom', 'fast_random']: {
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'spec_math_random', argTypes: [IrType:F64, IrType:F64], args: ['0.0', '1.0']);
			},
			'fastRandomSeed': {
				local String is _unused: self:lowerArg(b: b, call: call, idx: 0);
				res: '0';
			},
			['round', 'ceil', 'floor']: {
				local NamedArg is na0: call:args:get(index: 0);
				local String is v: b:castIfNeeded(val: b:lowerExpr(expr: na0:value), fromTy: b:irTypeFor(specType: na0:value:resolvedType), toTy: IrType:F64);
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: nm, argTypes: [IrType:F64], args: [v]);
			},
			'abs': {
				local NamedArg is na0: call:args:get(index: 0);
				local String is v: b:castIfNeeded(val: b:lowerExpr(expr: na0:value), fromTy: b:irTypeFor(specType: na0:value:resolvedType), toTy: IrType:F64);
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'fabs', argTypes: [IrType:F64], args: [v]);
			},
			'min': {
				local NamedArg is na0: call:args:get(index: 0);
				local NamedArg is na1: call:args:get(index: 1);
				local String is x: b:castIfNeeded(val: b:lowerExpr(expr: na0:value), fromTy: b:irTypeFor(specType: na0:value:resolvedType), toTy: IrType:F64);
				local String is y: b:castIfNeeded(val: b:lowerExpr(expr: na1:value), fromTy: b:irTypeFor(specType: na1:value:resolvedType), toTy: IrType:F64);
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'fmin', argTypes: [IrType:F64, IrType:F64], args: [x, y]);
			},
			'max': {
				local NamedArg is na0: call:args:get(index: 0);
				local NamedArg is na1: call:args:get(index: 1);
				local String is x: b:castIfNeeded(val: b:lowerExpr(expr: na0:value), fromTy: b:irTypeFor(specType: na0:value:resolvedType), toTy: IrType:F64);
				local String is y: b:castIfNeeded(val: b:lowerExpr(expr: na1:value), fromTy: b:irTypeFor(specType: na1:value:resolvedType), toTy: IrType:F64);
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'fmax', argTypes: [IrType:F64, IrType:F64], args: [x, y]);
			},
			['toInt', 'math_to_int']: {
				local String is v: self:lowerArg(b: b, call: call, idx: 0);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCast(dst: dst, val: v, fromType: IrType:F64, toType: IrType:I64));
				res: dst;
			},
			['toFloat', 'math_to_float']: {
				local String is v: self:lowerArg(b: b, call: call, idx: 0);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCast(dst: dst, val: v, fromType: IrType:I64, toType: IrType:F64));
				res: dst;
			},
			['sqrt', 'math_sqrt']: {
				local String is v: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'sqrt', argTypes: [IrType:F64], args: [v]);
			},
			['fma', 'math_fma']: {
				local String is a: self:lowerArg(b: b, call: call, idx: 0);
				local String is bArg: self:lowerArg(b: b, call: call, idx: 1);
				local String is c: self:lowerArg(b: b, call: call, idx: 2);
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'fma', argTypes: [IrType:F64, IrType:F64, IrType:F64], args: [a, bArg, c]);
			},
			['atan2', 'pow']: {
				local String is x: self:lowerArg(b: b, call: call, idx: 0);
				local String is y: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'spec_math_' . nm, argTypes: [IrType:F64, IrType:F64], args: [x, y]);
			},
			['math_atan2', 'math_pow']: {
				local String is x: self:lowerArg(b: b, call: call, idx: 0);
				local String is y: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'spec_' . nm, argTypes: [IrType:F64, IrType:F64], args: [x, y]);
			},
			'random': {
				if({ call:args:length() >= 2 }, {
					local String is x: self:lowerArg(b: b, call: call, idx: 0);
					local String is y: self:lowerArg(b: b, call: call, idx: 1);
					res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'spec_math_random', argTypes: [IrType:F64, IrType:F64], args: [x, y]);
				}, {
					res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'spec_math_random', argTypes: [IrType:F64, IrType:F64], args: ['0.0', '1.0']);
				});
			},
			else: {
				local String is v: self:lowerArg(b: b, call: call, idx: 0);
				local String is cal: 'spec_math_' . nm;
				if({ nm:startsWith(prefix: 'math_') }, { cal: 'spec_' . nm; });
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: cal, argTypes: [IrType:F64], args: [v]);
			}
		]);
		return res;
	}
}
