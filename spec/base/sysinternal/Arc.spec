#! Package base:sysinternal
#! Pure-Spec unmanaged floor for Automated Reference Counting (ARC) and TLS small-object freelists.
##
## Compiled in unmanaged mode by IrBuilder (no automatic retain/release/pool instrumentation).
## SpecHeader layout (24 bytes preceding object pointer):
##   offset  0: ref_count (atomic i32)
##   offset  8: destroy   (i64 function pointer: void (*)(void*))
##   offset 16: sflags    (atomic i32: 1 = IMMORTAL, 2 = HASLEN, 4 = ARENA)
##   offset 20: slen      (i32: 0 = >64B, 1..4 = 16B..64B size class bucket + 1)
##
## TLS slots in @_spec_tls_i64:
##   slots  6..9:  freelist head pointer (SpecHeader address) for buckets 0..3
##   slots 10..13: freelist cached count for buckets 0..3

Class is Arc{
	namespace: ['base', 'sysinternal'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', as Mem()],
		['base', 'sysinternal', as Conditional()],
		['base', 'sysinternal', as Loops()]
	];

	Function of Int is allocObj(Int is size, Int is destroyFn){
		local Int is slenV: 0;
		local Int is allocSize: size;
		if({ size > 0 && size <= 64 }, {
			local Int is b: (size - 1) >> 4;
			slenV: b + 1;
			allocSize: slenV << 4;
			local Int is head: Mem:tlsGetI64(slot: 6 + b);
			if({ head != 0 }, {
				local Int is obj: head + 24;
				local Int is next: Mem:loadI64(ptr: obj, byteOffset: 0);
				Mem:tlsSetI64(slot: 6 + b, val: next);
				local Int is fc: Mem:tlsGetI64(slot: 10 + b);
				Mem:tlsSetI64(slot: 10 + b, val: fc - 1);
				Mem:set(dst: obj, byteVal: 0, bytes: allocSize);
				Mem:storeI32(ptr: head, byteOffset: 0, val: 1);
				Mem:storeI64(ptr: head, byteOffset: 8, val: destroyFn);
				Mem:storeI32(ptr: head, byteOffset: 16, val: 0);
				Mem:storeI32(ptr: head, byteOffset: 20, val: slenV);
				return obj;
			});
		});
		local Int is h: Mem:alloc(bytes: 24 + allocSize);
		Mem:storeI32(ptr: h, byteOffset: 0, val: 1);
		Mem:storeI64(ptr: h, byteOffset: 8, val: destroyFn);
		Mem:storeI32(ptr: h, byteOffset: 20, val: slenV);
		return h + 24;
	}

	Function of Int is retain(Int is objAddr){
		if({ objAddr == 0 }, { return 0; });
		local Int is h: objAddr - 24;
		local Int is sf: Mem:atomicLoadI32(addr: h + 16);
		if({ (sf & 1) != 0 }, { return objAddr; });
		Mem:atomicAddI32(addr: h, delta: 1);
		return objAddr;
	}

	Function is release(Int is objAddr){
		if({ objAddr == 0 }, { return; });
		local Int is h: objAddr - 24;
		local Int is sf: Mem:atomicLoadI32(addr: h + 16);
		if({ (sf & 1) != 0 }, { return; });
		local Int is rc: Mem:atomicLoadI32(addr: h);
		if({ rc == 0 }, {
			local Int is d0: Mem:loadI64(ptr: h, byteOffset: 8);
			Mem:storeI64(ptr: h, byteOffset: 8, val: 0);
			if({ d0 != 0 }, {
				Mem:callDestroy(fnPtr: d0, objPtr: objAddr);
			});
			return;
		});
		local Int is old: Mem:atomicSubI32(addr: h, delta: 1);
		if({ old == 1 }, {
			local Int is d: Mem:loadI64(ptr: h, byteOffset: 8);
			Mem:storeI64(ptr: h, byteOffset: 8, val: 0);
			if({ d != 0 }, {
				Mem:callDestroy(fnPtr: d, objPtr: objAddr);
			});
			local Int is sf2: Mem:atomicLoadI32(addr: h + 16);
			if({ (sf2 & 4) != 0 }, { return; });
			local Int is slen: Mem:loadI32(ptr: h, byteOffset: 20);
			if({ slen != 0 }, {
				local Int is b: slen - 1;
				if({ b >= 0 && b < 4 }, {
					local Int is fc: Mem:tlsGetI64(slot: 10 + b);
					if({ fc < 2048 }, {
						local Int is oldHead: Mem:tlsGetI64(slot: 6 + b);
						Mem:storeI64(ptr: objAddr, byteOffset: 0, val: oldHead);
						Mem:tlsSetI64(slot: 6 + b, val: h);
						Mem:tlsSetI64(slot: 10 + b, val: fc + 1);
						return;
					});
				});
			});
			Mem:free(ptr: h);
		});
	}

	Function is threadCleanup(){
		local Int is b: 0;
		while({ b < 4 }, {
			local Int is cur: Mem:tlsGetI64(slot: 6 + b);
			while({ cur != 0 }, {
				local Int is next: Mem:loadI64(ptr: cur + 24, byteOffset: 0);
				Mem:free(ptr: cur);
				cur: next;
			});
			Mem:tlsSetI64(slot: 6 + b, val: 0);
			Mem:tlsSetI64(slot: 10 + b, val: 0);
			b: b + 1;
		});
	}
}
