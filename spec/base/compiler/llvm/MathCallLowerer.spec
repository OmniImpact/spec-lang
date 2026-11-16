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
		if({ !self:isFloorTarget(call: call, domain: 'Math') }, { return false; });
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: call:name, when: [
			'init': { ok: true; },
			'fast_random': { ok: true; },
			['fast_random_seed', 'math_to_int', 'math_to_float', 'math_sqrt', 'math_cbrt', 'math_sin', 'math_cos', 'math_tan', 'math_asin', 'math_acos', 'math_atan', 'math_exp', 'math_log', 'math_log2', 'math_log10']: { ok: argc >= 1; },
			['math_atan2', 'math_pow']: { ok: argc >= 2; },
			'math_fma': { ok: argc >= 3; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		local String is res: '0';
		match(on: nm, when: [
			'init': { res: 'null'; },
			'fast_random': {
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'spec_math_random', argTypes: [IrType:F64, IrType:F64], args: ['0.0', '1.0']);
			},
			'fast_random_seed': {
				local String is _s: self:lowerNamedArg(b: b, call: call, argName: 'seed', posIdx: 0, defVal: '0');
				res: '0';
			},
			'math_to_int': {
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'v', posIdx: 0, defVal: '0.0');
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCast(dst: dst, val: v, fromType: IrType:F64, toType: IrType:I64));
				res: dst;
			},
			'math_to_float': {
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'v', posIdx: 0, defVal: '0');
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCast(dst: dst, val: v, fromType: IrType:I64, toType: IrType:F64));
				res: dst;
			},
			'math_sqrt': {
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'v', posIdx: 0, defVal: '0.0');
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'sqrt', argTypes: [IrType:F64], args: [v]);
			},
			'math_fma': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'a', posIdx: 0, defVal: '0.0');
				local String is bArg: self:lowerNamedArg(b: b, call: call, argName: 'b', posIdx: 1, defVal: '0.0');
				local String is c: self:lowerNamedArg(b: b, call: call, argName: 'c', posIdx: 2, defVal: '0.0');
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'fma', argTypes: [IrType:F64, IrType:F64, IrType:F64], args: [a, bArg, c]);
			},
			'math_atan2': {
				local String is y: self:lowerNamedArg(b: b, call: call, argName: 'y', posIdx: 0, defVal: '0.0');
				local String is x: self:lowerNamedArg(b: b, call: call, argName: 'x', posIdx: 1, defVal: '0.0');
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'spec_math_atan2', argTypes: [IrType:F64, IrType:F64], args: [y, x]);
			},
			'math_pow': {
				local String is x: self:lowerNamedArg(b: b, call: call, argName: 'base', posIdx: 0, defVal: '0.0');
				local String is y: self:lowerNamedArg(b: b, call: call, argName: 'exp', posIdx: 1, defVal: '0.0');
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'spec_math_pow', argTypes: [IrType:F64, IrType:F64], args: [x, y]);
			},
			else: {
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'v', posIdx: 0, defVal: '0.0');
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'spec_' . nm, argTypes: [IrType:F64], args: [v]);
			}
		]);
		return res;
	}
}
