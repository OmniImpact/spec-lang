#! Package base:sysinternal
#! Pure-Spec unmanaged floor for general raw heap allocation (alloc/realloc/free).
##
## Routes <= 4 KiB allocations through Slab (64 KiB cartons) and > 4 KiB
## allocations directly through OS virtual memory (Mem:vmAlloc / vmRealloc / vmFree).
##
## HeapHeader (16 bytes preceding returned pointer):
##   offset 0: totalBytes (i64 = 16 + requestedBytes)
##   offset 8: kind       (i64: 0 = Slab slot, 1 = OS VM mapping)

Class is Heap{
	namespace: ['base', 'sysinternal'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', as Mem()],
		['base', 'sysinternal', as Conditional()],
		['base', 'sysinternal', as Slab()]
	];

	Function of Int is allocMem(Int is bytes){
		local Int is req: if({ bytes <= 0 }, { 1 }, { bytes });
		local Int is total: 16 + req;
		local Int is cls: Slab:classForSize(totalBytes: total);
		if({ cls >= 0 }, {
			local Int is h: Slab:allocSlot(cls: cls);
			Mem:storeI64(ptr: h, byteOffset: 0, val: total);
			Mem:storeI64(ptr: h, byteOffset: 8, val: 0);
			return h + 16;
		});
		local Int is vh: base:sysinternal:Mem:vmAlloc(bytes: total);
		Mem:storeI64(ptr: vh, byteOffset: 0, val: total);
		Mem:storeI64(ptr: vh, byteOffset: 8, val: 1);
		return vh + 16;
	}

	Function is freeMem(Int is ptr){
		if({ ptr == 0 }, { return; });
		local Int is h: ptr - 16;
		local Int is kind: Mem:loadI64(ptr: h, byteOffset: 8);
		if({ kind == 0 }, {
			Slab:freeSlot(slotAddr: h);
			return;
		});
		local Int is total: Mem:loadI64(ptr: h, byteOffset: 0);
		base:sysinternal:Mem:vmFree(ptr: h, bytes: total);
	}

	Function of Int is reallocMem(Int is ptr, Int is bytes){
		if({ ptr == 0 }, {
			return self:allocMem(bytes: bytes);
		});
		local Int is req: if({ bytes <= 0 }, { 1 }, { bytes });
		local Int is newTotal: 16 + req;
		local Int is h: ptr - 16;
		local Int is oldTotal: Mem:loadI64(ptr: h, byteOffset: 0);
		local Int is kind: Mem:loadI64(ptr: h, byteOffset: 8);
		if({ kind == 1 && newTotal > 4096 }, {
			local Int is nh: base:sysinternal:Mem:vmRealloc(ptr: h, oldBytes: oldTotal, newBytes: newTotal);
			Mem:storeI64(ptr: nh, byteOffset: 0, val: newTotal);
			return nh + 16;
		});
		local Int is np: self:allocMem(bytes: req);
		local Int is oldPayload: oldTotal - 16;
		local Int is cp: if({ oldPayload < req }, { oldPayload }, { req });
		if({ cp > 0 }, {
			Mem:copy(dst: np, src: ptr, bytes: cp);
		});
		self:freeMem(ptr: ptr);
		return np;
	}
}
