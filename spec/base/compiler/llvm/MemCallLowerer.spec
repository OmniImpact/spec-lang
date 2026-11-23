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
		if({ !:isFloorTarget(call: call, domain: 'Mem') }, { return false; });
		local Int is argc: call:args:length();
		local Boolean is ok: false;
		match(on: call:name, when: [
			['init', 'classRegistryAddr', 'classRegistryCount', 'heldRegistryAddr', 'slabAlloc', 'isMultithreaded']: { ok: true; },
			['alloc', 'free', 'slabFree', 'vmAlloc', 'cstrLen', 'objToAddr', 'addrToObj', 'retainAddr', 'releaseAddr', 'claimPoolAddr', 'internStr', 'panic', 'floatToBits', 'bitsToFloat', 'atomicLoadI32', 'atomicLoadI64', 'callConstruct', 'cstrToStr', 'typeNameOf', 'tlsGetI64']: { ok: true; },
			['realloc', 'vmFree', 'strFromBytes', 'loadI64', 'loadI32', 'loadByte', 'loadPtr', 'loadF64', 'atomicStoreI32', 'atomicAddI32', 'atomicSubI32', 'atomicStoreI64', 'atomicAddI64', 'callDestroy', 'tlsSetI64', 'randomBytes']: { ok: argc >= 2; },
			['copy', 'move', 'set', 'cmp', 'vmRealloc', 'storeI64', 'storeI32', 'storeByte', 'storePtr', 'storeF64', 'atomicCasI64']: { ok: argc >= 3; }
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
				local String is n: :lowerNamedArg(b: b, call: call, argName: 'bytes', posIdx: 0, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_alloc', argTypes: Array([IrType:I64]), args: Array([n]));
			},
			'realloc': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is n: :lowerNamedArg(b: b, call: call, argName: 'bytes', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_realloc', argTypes: Array([IrType:I64, IrType:I64]), args: Array([p, n]));
			},
			'free': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_free', argTypes: Array([IrType:I64]), args: Array([p]));
			},
			'slabAlloc': {
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_slab_alloc', argTypes: Array(), args: Array());
			},
			'slabFree': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_slab_free', argTypes: Array([IrType:I64]), args: Array([p]));
			},
			'vmAlloc': {
				local String is n: :lowerNamedArg(b: b, call: call, argName: 'bytes', posIdx: 0, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_vm_alloc', argTypes: Array([IrType:I64]), args: Array([n]));
			},
			'vmFree': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is n: :lowerNamedArg(b: b, call: call, argName: 'bytes', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_vm_free', argTypes: Array([IrType:I64, IrType:I64]), args: Array([p, n]));
			},
			'vmRealloc': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is o: :lowerNamedArg(b: b, call: call, argName: 'oldBytes', posIdx: 1, defVal: '0');
				local String is n: :lowerNamedArg(b: b, call: call, argName: 'newBytes', posIdx: 2, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_vm_realloc', argTypes: Array([IrType:I64, IrType:I64, IrType:I64]), args: Array([p, o, n]));
			},
			'isMultithreaded': {
				res: :emitSysCall(b: b, retType: IrType:I1, callee: '__spec_mem_is_multithreaded', argTypes: Array(), args: Array());
			},
			'randomBytes': {
				local String is d: :lowerNamedArg(b: b, call: call, argName: 'dstAddr', posIdx: 0, defVal: '0');
				local String is n: :lowerNamedArg(b: b, call: call, argName: 'len', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: 'spec_pal_random_bytes', argTypes: Array([IrType:I64, IrType:I64]), args: Array([d, n]));
			},
			'copy': {
				local String is d: :lowerNamedArg(b: b, call: call, argName: 'dst', posIdx: 0, defVal: '0');
				local String is s: :lowerNamedArg(b: b, call: call, argName: 'src', posIdx: 1, defVal: '0');
				local String is n: :lowerNamedArg(b: b, call: call, argName: 'bytes', posIdx: 2, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_copy', argTypes: Array([IrType:I64, IrType:I64, IrType:I64]), args: Array([d, s, n]));
			},
			'move': {
				local String is d: :lowerNamedArg(b: b, call: call, argName: 'dst', posIdx: 0, defVal: '0');
				local String is s: :lowerNamedArg(b: b, call: call, argName: 'src', posIdx: 1, defVal: '0');
				local String is n: :lowerNamedArg(b: b, call: call, argName: 'bytes', posIdx: 2, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_move', argTypes: Array([IrType:I64, IrType:I64, IrType:I64]), args: Array([d, s, n]));
			},
			'set': {
				local String is d: :lowerNamedArg(b: b, call: call, argName: 'dst', posIdx: 0, defVal: '0');
				local String is v: :lowerNamedArg(b: b, call: call, argName: 'byteVal', posIdx: 1, defVal: '0');
				local String is n: :lowerNamedArg(b: b, call: call, argName: 'bytes', posIdx: 2, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_set', argTypes: Array([IrType:I64, IrType:I64, IrType:I64]), args: Array([d, v, n]));
			},
			'cmp': {
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'a', posIdx: 0, defVal: '0');
				local String is bArg: :lowerNamedArg(b: b, call: call, argName: 'b', posIdx: 1, defVal: '0');
				local String is n: :lowerNamedArg(b: b, call: call, argName: 'bytes', posIdx: 2, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_cmp', argTypes: Array([IrType:I64, IrType:I64, IrType:I64]), args: Array([a, bArg, n]));
			},
			'cstrLen': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'cstrAddr', posIdx: 0, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_cstr_len', argTypes: Array([IrType:I64]), args: Array([p]));
			},
			'loadI64': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: :lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_load_i64', argTypes: Array([IrType:I64, IrType:I64]), args: Array([p, off]));
			},
			'storeI64': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: :lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				local String is v: :lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 2, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_store_i64', argTypes: Array([IrType:I64, IrType:I64, IrType:I64]), args: Array([p, off, v]));
			},
			'loadI32': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: :lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_load_i32', argTypes: Array([IrType:I64, IrType:I64]), args: Array([p, off]));
			},
			'storeI32': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: :lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				local String is v: :lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 2, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_store_i32', argTypes: Array([IrType:I64, IrType:I64, IrType:I64]), args: Array([p, off, v]));
			},
			'loadByte': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: :lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_load_byte', argTypes: Array([IrType:I64, IrType:I64]), args: Array([p, off]));
			},
			'storeByte': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: :lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				local String is v: :lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 2, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_store_byte', argTypes: Array([IrType:I64, IrType:I64, IrType:I64]), args: Array([p, off, v]));
			},
			'loadPtr': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: :lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				local String is rawPtr: :emitSysCall(b: b, retType: IrType:Ptr, callee: '__spec_mem_load_ptr', argTypes: Array([IrType:I64, IrType:I64]), args: Array([p, off]));
				res: b:castIfNeeded(val: rawPtr, fromTy: IrType:Ptr, toTy: b:irTypeFor(specType: expr:resolvedType));
			},
			'storePtr': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: :lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				local String is vp: :lowerArgAsPtr(b: b, call: call, argName: 'val', posIdx: 2);
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_store_ptr', argTypes: Array([IrType:I64, IrType:I64, IrType:Ptr]), args: Array([p, off, vp]));
			},
			'loadF64': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: :lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:F64, callee: '__spec_mem_load_f64', argTypes: Array([IrType:I64, IrType:I64]), args: Array([p, off]));
			},
			'storeF64': {
				local String is p: :lowerNamedArg(b: b, call: call, argName: 'ptr', posIdx: 0, defVal: '0');
				local String is off: :lowerNamedArg(b: b, call: call, argName: 'byteOffset', posIdx: 1, defVal: '0');
				local String is v: :lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 2, defVal: '0.0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_store_f64', argTypes: Array([IrType:I64, IrType:I64, IrType:F64]), args: Array([p, off, v]));
			},
			'objToAddr': {
				local String is vp: :lowerArgAsPtr(b: b, call: call, argName: 'obj', posIdx: 0);
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_obj_to_addr', argTypes: Array([IrType:Ptr]), args: Array([vp]));
			},
			'addrToObj': {
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				local String is rawPtr: :emitSysCall(b: b, retType: IrType:Ptr, callee: '__spec_mem_addr_to_obj', argTypes: Array([IrType:I64]), args: Array([a]));
				res: b:castIfNeeded(val: rawPtr, fromTy: IrType:Ptr, toTy: b:irTypeFor(specType: expr:resolvedType));
			},
			'retainAddr': {
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'objAddr', posIdx: 0, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_retain_addr', argTypes: Array([IrType:I64]), args: Array([a]));
			},
			'releaseAddr': {
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'objAddr', posIdx: 0, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_release_addr', argTypes: Array([IrType:I64]), args: Array([a]));
			},
			'claimPoolAddr': {
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'objAddr', posIdx: 0, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_claim_pool_addr', argTypes: Array([IrType:I64]), args: Array([a]));
			},
			'strFromBytes': {
				local String is src: :lowerNamedArg(b: b, call: call, argName: 'srcAddr', posIdx: 0, defVal: '0');
				local String is n: :lowerNamedArg(b: b, call: call, argName: 'len', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Ptr, callee: '__spec_mem_str_from_bytes', argTypes: Array([IrType:I64, IrType:I64]), args: Array([src, n]));
				b:emitClaimPool(val: res);
			},
			'internStr': {
				local String is sp: :lowerArgAsPtr(b: b, call: call, argName: 's', posIdx: 0);
				res: :emitSysCall(b: b, retType: IrType:Ptr, callee: '__spec_mem_intern_str', argTypes: Array([IrType:Ptr]), args: Array([sp]));
			},
			'panic': {
				local String is sp: :lowerArgAsPtr(b: b, call: call, argName: 'msg', posIdx: 0);
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_panic', argTypes: Array([IrType:Ptr]), args: Array([sp]));
			},
			'floatToBits': {
				local String is v: :lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 0, defVal: '0.0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_float_to_bits', argTypes: Array([IrType:F64]), args: Array([v]));
			},
			'bitsToFloat': {
				local String is bits: :lowerNamedArg(b: b, call: call, argName: 'bits', posIdx: 0, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:F64, callee: '__spec_mem_bits_to_float', argTypes: Array([IrType:I64]), args: Array([bits]));
			},
			'atomicLoadI32': {
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_atomic_load_i32', argTypes: Array([IrType:I64]), args: Array([a]));
			},
			'atomicStoreI32': {
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				local String is v: :lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_atomic_store_i32', argTypes: Array([IrType:I64, IrType:I64]), args: Array([a, v]));
			},
			'atomicAddI32': {
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				local String is d: :lowerNamedArg(b: b, call: call, argName: 'delta', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_atomic_add_i32', argTypes: Array([IrType:I64, IrType:I64]), args: Array([a, d]));
			},
			'atomicSubI32': {
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				local String is d: :lowerNamedArg(b: b, call: call, argName: 'delta', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_atomic_sub_i32', argTypes: Array([IrType:I64, IrType:I64]), args: Array([a, d]));
			},
			'atomicLoadI64': {
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_atomic_load_i64', argTypes: Array([IrType:I64]), args: Array([a]));
			},
			'atomicStoreI64': {
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				local String is v: :lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_atomic_store_i64', argTypes: Array([IrType:I64, IrType:I64]), args: Array([a, v]));
			},
			'atomicAddI64': {
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				local String is d: :lowerNamedArg(b: b, call: call, argName: 'delta', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_atomic_add_i64', argTypes: Array([IrType:I64, IrType:I64]), args: Array([a, d]));
			},
			'atomicCasI64': {
				local String is a: :lowerNamedArg(b: b, call: call, argName: 'addr', posIdx: 0, defVal: '0');
				local String is exp: :lowerNamedArg(b: b, call: call, argName: 'expected', posIdx: 1, defVal: '0');
				local String is des: :lowerNamedArg(b: b, call: call, argName: 'desired', posIdx: 2, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I1, callee: '__spec_mem_atomic_cas_i64', argTypes: Array([IrType:I64, IrType:I64, IrType:I64]), args: Array([a, exp, des]));
			},
			'callDestroy': {
				local String is fn: :lowerNamedArg(b: b, call: call, argName: 'fnPtr', posIdx: 0, defVal: '0');
				local String is obj: :lowerNamedArg(b: b, call: call, argName: 'objPtr', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_call_destroy', argTypes: Array([IrType:I64, IrType:I64]), args: Array([fn, obj]));
			},
			'callConstruct': {
				local String is fn: :lowerNamedArg(b: b, call: call, argName: 'fnAddr', posIdx: 0, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Ptr, callee: '__spec_mem_call_construct', argTypes: Array([IrType:I64]), args: Array([fn]));
			},
			'classRegistryAddr': {
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_class_reg_addr', argTypes: Array(), args: Array());
			},
			'classRegistryCount': {
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_class_reg_count', argTypes: Array(), args: Array());
			},
			'heldRegistryAddr': {
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_held_reg_addr', argTypes: Array(), args: Array());
			},
			'cstrToStr': {
				local String is ca: :lowerNamedArg(b: b, call: call, argName: 'cstrAddr', posIdx: 0, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Ptr, callee: '__spec_mem_cstr_to_str', argTypes: Array([IrType:I64]), args: Array([ca]));
			},
			'typeNameOf': {
				local String is op: :lowerArgAsPtr(b: b, call: call, argName: 'obj', posIdx: 0);
				res: :emitSysCall(b: b, retType: IrType:Ptr, callee: 'spec_type_name', argTypes: Array([IrType:Ptr]), args: Array([op]));
			},
			'tlsGetI64': {
				local String is sl: :lowerNamedArg(b: b, call: call, argName: 'slot', posIdx: 0, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:I64, callee: '__spec_mem_tls_get_i64', argTypes: Array([IrType:I64]), args: Array([sl]));
			},
			'tlsSetI64': {
				local String is sl: :lowerNamedArg(b: b, call: call, argName: 'slot', posIdx: 0, defVal: '0');
				local String is v: :lowerNamedArg(b: b, call: call, argName: 'val', posIdx: 1, defVal: '0');
				res: :emitSysCall(b: b, retType: IrType:Void, callee: '__spec_mem_tls_set_i64', argTypes: Array([IrType:I64, IrType:I64]), args: Array([sl, v]));
			}
		]);
		return res;
	}
}
