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
			['toInt', 'toFloat', 'sqrt', 'cbrt', 'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'exp', 'log', 'log2', 'log10']: { ok: argc >= 1; },
			['atan2', 'pow', 'random']: { ok: argc >= 2; },
			'fma': { ok: argc >= 3; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		local String is res: '0';
		match(on: nm, when: [
			'toInt': {
				local String is v: self:lowerArg(b: b, call: call, idx: 0);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCast(dst: dst, val: v, fromType: IrType:F64, toType: IrType:I64));
				res: dst;
			},
			'toFloat': {
				local String is v: self:lowerArg(b: b, call: call, idx: 0);
				local String is dst: b:nextTmp();
				b:emit(inst: IrInst:IrCast(dst: dst, val: v, fromType: IrType:I64, toType: IrType:F64));
				res: dst;
			},
			'sqrt': {
				local String is v: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'sqrt', argTypes: [IrType:F64], args: [v]);
			},
			'fma': {
				local String is a: self:lowerArg(b: b, call: call, idx: 0);
				local String is bArg: self:lowerArg(b: b, call: call, idx: 1);
				local String is c: self:lowerArg(b: b, call: call, idx: 2);
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'fma', argTypes: [IrType:F64, IrType:F64, IrType:F64], args: [a, bArg, c]);
			},
			['atan2', 'pow', 'random']: {
				local String is x: self:lowerArg(b: b, call: call, idx: 0);
				local String is y: self:lowerArg(b: b, call: call, idx: 1);
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'spec_math_' . nm, argTypes: [IrType:F64, IrType:F64], args: [x, y]);
			},
			else: {
				local String is v: self:lowerArg(b: b, call: call, idx: 0);
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: 'spec_math_' . nm, argTypes: [IrType:F64], args: [v]);
			}
		]);
		return res;
	}
}
