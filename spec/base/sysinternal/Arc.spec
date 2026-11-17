#! Package base:sysinternal
#! Pure-Spec unmanaged floor for Automated Reference Counting (ARC) and TLS small-object freelists.
##
## Compiled in unmanaged mode by IrBuilder (no automatic retain/release/pool instrumentation).
## SpecHeader layout (16 bytes preceding object pointer):
##   offset  0: ref_count  (atomic i32)
##   offset  4: flags_slen (i32: low 16 bits = sflags [1=IMMORTAL, 2=HASLEN, 4=ARENA],
##                              high 16 bits = slen [0 = >64B, 1..4 = 16B..64B bucket + 1])
##   offset  8: destroy    (i64 function pointer: void (*)(void*))
##
## TLS slots in @_spec_tls_i64:
##   slots  6..9:  freelist head pointer (SpecHeader address) for buckets 0..3
##   slots 10..13: freelist cached count for buckets 0..3

Class is Arc{
	namespace: ['base', 'sysinternal'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', as Mem()],
		['base', 'sysinternal', as Conditional()],
		['base', 'sysinternal', as Loops()],
		['base', 'sysinternal', as Slab()]
	];

	Function of Int is allocObj(Int is size, Int is destroyFn){
		local Int is cls: Slab:classForPayload(payloadSize: size);
		if({ cls >= 0 }, {
			local Int is sh: Slab:allocObj(cls: cls);
			Mem:storeI32(ptr: sh, byteOffset: 0, val: 1);
			Mem:storeI32(ptr: sh, byteOffset: 4, val: (cls + 1) << 16);
			Mem:storeI64(ptr: sh, byteOffset: 8, val: destroyFn);
			return sh + 16;
		});
		local Int is h: Mem:alloc(bytes: 16 + size);
		Mem:storeI32(ptr: h, byteOffset: 0, val: 1);
		Mem:storeI32(ptr: h, byteOffset: 4, val: 0);
		Mem:storeI64(ptr: h, byteOffset: 8, val: destroyFn);
		return h + 16;
	}

	Function of Int is retain(Int is objAddr){
		if({ objAddr == 0 }, { return 0; });
		local Int is h: objAddr - 16;
		local Int is sf: Mem:atomicLoadI32(addr: h + 4);
		if({ (sf & 1) != 0 }, { return objAddr; });
		Mem:atomicAddI32(addr: h, delta: 1);
		return objAddr;
	}

	Function is destroyObj(Int is objAddr){
		local Int is h: objAddr - 16;
		local Int is d: Mem:loadI64(ptr: h, byteOffset: 8);
		Mem:storeI64(ptr: h, byteOffset: 8, val: 0);
		if({ d != 0 }, {
			Mem:callDestroy(fnPtr: d, objPtr: objAddr);
		});
		local Int is sf2: Mem:atomicLoadI32(addr: h + 4);
		if({ (sf2 & 4) != 0 }, { return; });
		local Int is slen: sf2 >> 16;
		if({ slen != 0 }, {
			Slab:freeSlot(hdrAddr: h);
			return;
		});
		Mem:free(ptr: h);
	}

	Function is release(Int is objAddr){
		if({ objAddr == 0 }, { return; });
		local Int is h: objAddr - 16;
		local Int is sf: Mem:atomicLoadI32(addr: h + 4);
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
			self:destroyObj(objAddr: objAddr);
		});
	}

	Function is threadCleanup(){
		Slab:threadCleanup();
	}
}
