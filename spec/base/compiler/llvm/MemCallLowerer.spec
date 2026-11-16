#! Package base:compiler:llvm
#! Lowers base:sysinternal:Mem and base:sys:Mem calls directly to LLVM IR intrinsics.

Class of SysinternalCallLowerer is MemCallLowerer{
	namespace: ['base', 'compiler', 'llvm'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'llvm', SysinternalCallLowerer],
		['base', 'compiler', 'llvm', IrBuilder],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ir', IrType],
		['base', 'compiler', 'ir', IrInst],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(){
		return;
	}

	replace Function of String is name(){
		return 'MemCallLowerer';
	}

	replace Function of Int is order(){
		return 41;
	}

	replace Function of Boolean is matches(IrBuilder is b, Expression is expr, CallData is call){
		if({ !self:isFloorTarget(call: call, domain: 'Mem') }, { return false; });
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: call:name, when: [
			'init': { ok: true; },
			['alloc', 'free', 'cstrLen', 'objToAddr', 'addrToObj', 'retainAddr', 'releaseAddr', 'claimPoolAddr', 'floatToBits', 'bitsToFloat', 'atomicLoadI32', 'atomicLoadI64']: { ok: argc >= 1; },
			['realloc', 'loadI64', 'loadI32', 'loadByte', 'loadPtr', 'loadF64', 'atomicStoreI32', 'atomicAddI32', 'atomicSubI32', 'atomicStoreI64', 'atomicAddI64', 'callDestroy']: { ok: argc >= 2; },
			['copy', 'move', 'set', 'cmp', 'storeI64', 'storeI32', 'storeByte', 'storePtr', 'storeF64', 'atomicCasI64']: { ok: argc >= 3; }
		]);
		return ok;
	}

	local Function of String is lowerArgAsPtr(IrBuilder is b, CallData is call, String is argName, Int is posIdx){
		local Int is i: 0;
		local Boolean is found: false;
		local Expression is valExpr: Expression:Unknown;
		while({ i < call:args:length() && !found }, {
			local NamedArg is na: call:args:get(index: i);
			if({ na:name == argName }, {
				valExpr: na:value;
				found: true;
			});
			i++;
		});
		if({ !found && posIdx >= 0 && posIdx < call:args:length() }, {
			local NamedArg is pna: call:args:get(index: posIdx);
			valExpr: pna:value;
			found: true;
		});
		if({ !found }, { return 'null'; });
		local String is raw: b:lowerExpr(expr: valExpr);
		local IrType is fromTy: b:irTypeFor(specType: valExpr:resolvedType);
		return b:castIfNeeded(val: raw, fromTy: fromTy, toTy: IrType:Ptr);
	}

	replace Function of String is lower(IrBuilder is b, Expression is expr, CallData is call){
		local String is res: '0';
		match(on: call:name, when: [
			'init': { res: 'null'; },
			'alloc': {
				local String is n: self:lowerNamedArg(b: b, call: call, argName: 'bytes', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_alloc', argTypes: [IrType:I64], args: [n]);
			},
			'realloc': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is n: self:lowerNamedArg(b: b, call: call, argName: 'bytes', posIdx: 1, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_realloc', argTypes: [IrType:I64, IrType:I64], args: [p, n]);
			},
			'free': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_free', argTypes: [IrType:I64], args: [p]);
			},
			'copy': {
				local String is d: self:lowerNamedArg(b: b, call: call, argName: 'dst', posIdx: 0, defVal: '0');
				local String is s: self:lowerNamedArg(b: b, call: call, argName: 'src', posIdx: 1, defVal: '0');
				local String is n: self:lowerNamedArg(b: b, call: call, argName: 'bytes', posIdx: 2, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_copy', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [d, s, n]);
			},
			'move': {
				local String is d: self:lowerNamedArg(b: b, call: call, argName: 'dst', posIdx: 0, defVal: '0');
				local String is s: self:lowerNamedArg(b: b, call: call, argName: 'src', posIdx: 1, defVal: '0');
				local String is n: self:lowerNamedArg(b: b, call: call, argName: 'bytes', posIdx: 2, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_move', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [d, s, n]);
			},
			'set': {
				local String is d: self:lowerNamedArg(b: b, call: call, argName: 'dst', posIdx: 0, defVal: '0');
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'byteVal', posIdx: 1, defVal: '0');
				local String is n: self:lowerNamedArg(b: b, call: call, argName: 'bytes', posIdx: 2, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_set', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [d, v, n]);
			},
			'cmp': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'a', posIdx: 0, defVal: '0');
				local String is bArg: self:lowerNamedArg(b: b, call: call, argName: 'b', posIdx: 1, defVal: '0');
				local String is n: self:lowerNamedArg(b: b, call: call, argName: 'bytes', posIdx: 2, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_cmp', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [a, bArg, n]);
			},
			'cstrLen': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'cstrAddr', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_cstr_len', argTypes: [IrType:I64], args: [p]);
			},
			'loadI64': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: self:lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_load_i64', argTypes: [IrType:I64, IrType:I64], args: [p, off]);
			},
			'storeI64': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: self:lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 2, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_store_i64', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [p, off, v]);
			},
			'loadI32': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: self:lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_load_i32', argTypes: [IrType:I64, IrType:I64], args: [p, off]);
			},
			'storeI32': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: self:lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 2, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_store_i32', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [p, off, v]);
			},
			'loadByte': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: self:lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_load_byte', argTypes: [IrType:I64, IrType:I64], args: [p, off]);
			},
			'storeByte': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: self:lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 2, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_store_byte', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [p, off, v]);
			},
			'loadPtr': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: self:lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				local String is rawPtr: self:emitSysCall(b: b, retType: IrType:Ptr, callee: '__spec_mem_load_ptr', argTypes: [IrType:I64, IrType:I64], args: [p, off]);
				res: b:castIfNeeded(val: rawPtr, fromTy: IrType:Ptr, toTy: b:irTypeFor(specType: expr:resolvedType));
			},
			'storePtr': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: self:lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				local String is vp: self:lowerArgAsPtr(b: b, call: call, argName: 'val', posIdx: 2);
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_store_ptr', argTypes: [IrType:I64, IrType:I64, IrType:Ptr], args: [p, off, vp]);
			},
			'loadF64': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: self:lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: '__spec_mem_load_f64', argTypes: [IrType:I64, IrType:I64], args: [p, off]);
			},
			'storeF64': {
				local String is p: self:lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: self:lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 2, defVal: '0.0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_store_f64', argTypes: [IrType:I64, IrType:I64, IrType:F64], args: [p, off, v]);
			},
			'objToAddr': {
				local String is vp: self:lowerArgAsPtr(b: b, call: call, argName: 'obj', posIdx: 0);
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_obj_to_addr', argTypes: [IrType:Ptr], args: [vp]);
			},
			'addrToObj': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				local String is rawPtr: self:emitSysCall(b: b, retType: IrType:Ptr, callee: '__spec_mem_addr_to_obj', argTypes: [IrType:I64], args: [a]);
				res: b:castIfNeeded(val: rawPtr, fromTy: IrType:Ptr, toTy: b:irTypeFor(specType: expr:resolvedType));
			},
			'retainAddr': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'objAddr', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_retain_addr', argTypes: [IrType:I64], args: [a]);
			},
			'releaseAddr': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'objAddr', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_release_addr', argTypes: [IrType:I64], args: [a]);
			},
			'claimPoolAddr': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'objAddr', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_claim_pool_addr', argTypes: [IrType:I64], args: [a]);
			},
			'floatToBits': {
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 0, defVal: '0.0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_float_to_bits', argTypes: [IrType:F64], args: [v]);
			},
			'bitsToFloat': {
				local String is bits: self:lowerNamedArg(b: b, call: call, argName: 'bits', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:F64, callee: '__spec_mem_bits_to_float', argTypes: [IrType:I64], args: [bits]);
			},
			'atomicLoadI32': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_atomic_load_i32', argTypes: [IrType:I64], args: [a]);
			},
			'atomicStoreI32': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 1, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_atomic_store_i32', argTypes: [IrType:I64, IrType:I64], args: [a, v]);
			},
			'atomicAddI32': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				local String is d: self:lowerNamedArg(b: b, call: call, argName: 'delta', posIdx: 1, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_atomic_add_i32', argTypes: [IrType:I64, IrType:I64], args: [a, d]);
			},
			'atomicSubI32': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				local String is d: self:lowerNamedArg(b: b, call: call, argName: 'delta', posIdx: 1, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_atomic_sub_i32', argTypes: [IrType:I64, IrType:I64], args: [a, d]);
			},
			'atomicLoadI64': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_atomic_load_i64', argTypes: [IrType:I64], args: [a]);
			},
			'atomicStoreI64': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				local String is v: self:lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 1, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_atomic_store_i64', argTypes: [IrType:I64, IrType:I64], args: [a, v]);
			},
			'atomicAddI64': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				local String is d: self:lowerNamedArg(b: b, call: call, argName: 'delta', posIdx: 1, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_atomic_add_i64', argTypes: [IrType:I64, IrType:I64], args: [a, d]);
			},
			'atomicCasI64': {
				local String is a: self:lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				local String is exp: self:lowerNamedArg(b: b, call: call, argName: 'expected', posIdx: 1, defVal: '0');
				local String is des: self:lowerNamedArg(b: b, call: call, argName: 'desired', posIdx: 2, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:I1, callee: '__spec_mem_atomic_cas_i64', argTypes: [IrType:I64, IrType:I64, IrType:I64], args: [a, exp, des]);
			},
			'callDestroy': {
				local String is fn: self:lowerNamedArg(b: b, call: call, argName: 'fnPtr', posIdx: 0, defVal: '0');
				local String is obj: self:lowerNamedArg(b: b, call: call, argName: 'objPtr', posIdx: 1, defVal: '0');
				res: self:emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_call_destroy', argTypes: [IrType:I64, IrType:I64], args: [fn, obj]);
			}
		]);
		return res;
	}
}
