#! Package base:compiler:llvm
#! Lowers base:sysinternal:Simd calls to portable LLVM `<4 x double>` runtime helpers.

Class of SysinternalCallLowerer is SimdCallLowerer{
	replace [String] is namespace: ['base', 'compiler', 'llvm'];

	replace [[String]] is using: [
		['base', 'compiler', 'llvm', SysinternalCallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ir', IrType],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(){
		return;
	}

	replace Function of String is name(){
		return 'SimdCallLowerer';
	}

	replace Function of Int is order(){
		return 44;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		if({ !:isFloorTarget(call: call, domain: 'Simd') }, { return false; });
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: call:name, when: [
			'init': { ok: true; },
			['loadF64', 'fill4', 'dot4']: { ok: argc >= 2; },
			['storeF64', 'add4', 'sub4', 'mul4', 'scale4']: { ok: argc >= 3; },
			['fma4', 'clamp4']: { ok: argc >= 4; }
		]);
		return ok;
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is nm: call:name;
		local String is res: '0';
		match(on: nm, when: [
			'init': { res: 'null'; },
			'loadF64': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: :lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:F64, callee: 'spec_simd_load_f64', argTypes: [IrType:I64, IrType:I64], args: [p, off]);
			},
			'storeF64': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: :lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				local String is v: :lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 2, defVal: '0.0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: 'spec_simd_store_f64', argTypes: [IrType:I64, IrType:I64, IrType:F64], args: [p, off, v]);
			},
			'fill4': {
				local String is d: :lowerNamedArg(b: b, call: call, argName: 'dst', posIdx: 0, defVal: '0');
				local String is v: :lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 1, defVal: '0.0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: 'spec_simd_fill4', argTypes: [IrType:I64, IrType:F64], args: [d, v]);
			},
			'add4': {
				local String is d: :lowerNamedArg(b: b, call: call, argName: 'dst', posIdx: 0, defVal: '0');
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'a', posIdx: 1, defVal: '0');
				local String is bArg: :lowerNamedArg(b: b, call: call, argName: 'b', posIdx: 2, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: 'spec_simd_add4', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [d, a, bArg]);
			},
			'sub4': {
				local String is d: :lowerNamedArg(b: b, call: call, argName: 'dst', posIdx: 0, defVal: '0');
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'a', posIdx: 1, defVal: '0');
				local String is bArg: :lowerNamedArg(b: b, call: call, argName: 'b', posIdx: 2, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: 'spec_simd_sub4', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [d, a, bArg]);
			},
			'mul4': {
				local String is d: :lowerNamedArg(b: b, call: call, argName: 'dst', posIdx: 0, defVal: '0');
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'a', posIdx: 1, defVal: '0');
				local String is bArg: :lowerNamedArg(b: b, call: call, argName: 'b', posIdx: 2, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: 'spec_simd_mul4', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [d, a, bArg]);
			},
			'scale4': {
				local String is d: :lowerNamedArg(b: b, call: call, argName: 'dst', posIdx: 0, defVal: '0');
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'a', posIdx: 1, defVal: '0');
				local String is s: :lowerNamedArg(b: b, call: call, argName: 'scalar', posIdx: 2, defVal: '0.0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: 'spec_simd_scale4', argTypes: [IrType:I64, IrType:I64, IrType:F64], args: [d, a, s]);
			},
			'fma4': {
				local String is d: :lowerNamedArg(b: b, call: call, argName: 'dst', posIdx: 0, defVal: '0');
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'a', posIdx: 1, defVal: '0');
				local String is bArg: :lowerNamedArg(b: b, call: call, argName: 'b', posIdx: 2, defVal: '0');
				local String is c: :lowerNamedArg(b: b, call: call, argName: 'c', posIdx: 3, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: 'spec_simd_fma4', argTypes: [IrType:I64, IrType:I64, IrType:I64, IrType:I64], args: [d, a, bArg, c]);
			},
			'dot4': {
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'a', posIdx: 0, defVal: '0');
				local String is bArg: :lowerNamedArg(b: b, call: call, argName: 'b', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:F64, callee: 'spec_simd_dot4', argTypes: [IrType:I64, IrType:I64], args: [a, bArg]);
			},
			'clamp4': {
				local String is d: :lowerNamedArg(b: b, call: call, argName: 'dst', posIdx: 0, defVal: '0');
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'a', posIdx: 1, defVal: '0');
				local String is lo: :lowerNamedArg(b: b, call: call, argName: 'lo', posIdx: 2, defVal: '0.0');
				local String is hi: :lowerNamedArg(b: b, call: call, argName: 'hi', posIdx: 3, defVal: '1.0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: 'spec_simd_clamp4', argTypes: [IrType:I64, IrType:I64, IrType:F64, IrType:F64], args: [d, a, lo, hi]);
			}
		]);
		return res;
	}
}
