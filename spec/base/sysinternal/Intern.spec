#! Package base:sysinternal
#! Pure-Spec unmanaged floor for the lock-free concurrent string intern table.
##
## Table layout (24-byte header + capacity * 8-byte atomic bucket array):
##   offset  0: capacity (i64)
##   offset  8: mask     (i64 = capacity - 1)
##   offset 16: count    (i64)
##   offset 24: buckets  (capacity * i64 entry addresses)
##
## Entry layout (24 bytes):
##   offset  0: sAddr    (i64 address of immortal SpecBuf String)
##   offset  8: hash     (i64 FNV-1a 64-bit hash)
##   offset 16: next     (i64 address of next entry or 0)
##
## Global state layout (16 bytes at stateAddr):
##   offset  0: tableAddr (atomic i64)
##   offset  8: spinlock  (atomic i64: 0 = unlocked, 1 = locked)

Class is Intern{
	replace [String] is namespace: ['base', 'sysinternal'];

	replace [[String]] is using: [
		['base', 'sysinternal', as Mem()],
		['base', 'sysinternal', as Conditional()],
		['base', 'sysinternal', as Loops()]
	];

	Function of Int is hashBytes(Int is cstrAddr, Int is len){
		local Int is h: 1469598103934665603;
		local Int is i: 0;
		while({ i < len }, {
			local Int is b: Mem:loadByte(ptr: cstrAddr, byteOffset: i);
			h: (h ^ b) * 1099511628211;
			i: i + 1;
		});
		return h;
	}

	Function of Boolean is bytesEqual(Int is sAddr, Int is cstrAddr, Int is len){
		if({ sAddr == 0 }, { return false; });
		local Int is bLen: Mem:loadI64(ptr: sAddr, byteOffset: 8);
		if({ bLen != len }, { return false; });
		if({ len == 0 }, { return true; });
		local Int is dataAddr: Mem:loadI64(ptr: sAddr, byteOffset: 0);
		return Mem:cmp(a: dataAddr, b: cstrAddr, bytes: len) == 0;
	}

	Function of Int is newTable(Int is cap){
		local Int is tbl: Mem:alloc(bytes: 24 + (cap * 8));
		Mem:storeI64(ptr: tbl, byteOffset: 0, val: cap);
		Mem:storeI64(ptr: tbl, byteOffset: 8, val: cap - 1);
		Mem:storeI64(ptr: tbl, byteOffset: 16, val: 0);
		return tbl;
	}

	Function of Int is resizeTable(Int is oldTbl){
		local Int is oldCap: Mem:loadI64(ptr: oldTbl, byteOffset: 0);
		local Int is newCap: oldCap * 2;
		local Int is newMask: newCap - 1;
		local Int is newTbl: :newTable(cap: newCap);
		Mem:storeI64(ptr: newTbl, byteOffset: 16, val: Mem:loadI64(ptr: oldTbl, byteOffset: 16));
		local Int is i: 0;
		while({ i < oldCap }, {
			local Int is curr: Mem:atomicLoadI64(addr: oldTbl + 24 + (i * 8));
			while({ curr != 0 }, {
				local Int is eh: Mem:loadI64(ptr: curr, byteOffset: 8);
				local Int is nb: eh & newMask;
				local Int is ne: Mem:alloc(bytes: 24);
				Mem:storeI64(ptr: ne, byteOffset: 0, val: Mem:loadI64(ptr: curr, byteOffset: 0));
				Mem:storeI64(ptr: ne, byteOffset: 8, val: eh);
				local Int is head: Mem:atomicLoadI64(addr: newTbl + 24 + (nb * 8));
				Mem:storeI64(ptr: ne, byteOffset: 16, val: head);
				Mem:atomicStoreI64(addr: newTbl + 24 + (nb * 8), val: ne);
				curr: Mem:loadI64(ptr: curr, byteOffset: 16);
			});
			i: i + 1;
		});
		return newTbl;
	}

	Function of Int is internCstr(Int is cstrAddr, Int is stateAddr){
		local Int is n: if({ cstrAddr != 0 }, { Mem:cstrLen(cstrAddr: cstrAddr) }, { 0 });
		local Int is h: :hashBytes(cstrAddr: cstrAddr, len: n);
		local Int is tbl: Mem:atomicLoadI64(addr: stateAddr);
		if({ tbl != 0 }, {
			local Int is mask: Mem:loadI64(ptr: tbl, byteOffset: 8);
			local Int is b: h & mask;
			local Int is e: Mem:atomicLoadI64(addr: tbl + 24 + (b * 8));
			while({ e != 0 }, {
				if({ Mem:loadI64(ptr: e, byteOffset: 8) == h }, {
					local Int is sAddr: Mem:loadI64(ptr: e, byteOffset: 0);
					if({ :bytesEqual(sAddr: sAddr, cstrAddr: cstrAddr, len: n) }, {
						return sAddr;
					});
				});
				e: Mem:loadI64(ptr: e, byteOffset: 16);
			});
		});

		while({ !Mem:atomicCasI64(addr: stateAddr + 8, expected: 0, desired: 1) }, {
		});
		tbl: Mem:atomicLoadI64(addr: stateAddr);
		if({ tbl == 0 }, {
			tbl: :newTable(cap: 256);
			Mem:atomicStoreI64(addr: stateAddr, val: tbl);
		});
		local Int is mask2: Mem:loadI64(ptr: tbl, byteOffset: 8);
		local Int is b2: h & mask2;
		local Int is e2: Mem:atomicLoadI64(addr: tbl + 24 + (b2 * 8));
		while({ e2 != 0 }, {
			if({ Mem:loadI64(ptr: e2, byteOffset: 8) == h }, {
				local Int is sAddr2: Mem:loadI64(ptr: e2, byteOffset: 0);
				if({ :bytesEqual(sAddr: sAddr2, cstrAddr: cstrAddr, len: n) }, {
					Mem:atomicStoreI64(addr: stateAddr + 8, val: 0);
					return sAddr2;
				});
			});
			e2: Mem:loadI64(ptr: e2, byteOffset: 16);
		});

		local Int is count: Mem:loadI64(ptr: tbl, byteOffset: 16);
		local Int is cap: Mem:loadI64(ptr: tbl, byteOffset: 0);
		if({ count >= cap }, {
			tbl: :resizeTable(oldTbl: tbl);
			Mem:atomicStoreI64(addr: stateAddr, val: tbl);
			mask2: Mem:loadI64(ptr: tbl, byteOffset: 8);
			b2: h & mask2;
			count: Mem:loadI64(ptr: tbl, byteOffset: 16);
		});

		local String is sObj: Mem:strFromBytes(srcAddr: cstrAddr, len: n);
		local Int is newSAddr: Mem:objToAddr(obj: sObj);
		local Int is hdrAddr: newSAddr - 16;
		local Int is oldFlags: Mem:atomicLoadI32(addr: hdrAddr + 4);
		Mem:atomicStoreI32(addr: hdrAddr + 4, val: oldFlags | 1);
		local Int is ne: Mem:alloc(bytes: 24);
		Mem:storeI64(ptr: ne, byteOffset: 0, val: newSAddr);
		Mem:storeI64(ptr: ne, byteOffset: 8, val: h);
		local Int is head: Mem:atomicLoadI64(addr: tbl + 24 + (b2 * 8));
		Mem:storeI64(ptr: ne, byteOffset: 16, val: head);
		Mem:atomicStoreI64(addr: tbl + 24 + (b2 * 8), val: ne);
		Mem:storeI64(ptr: tbl, byteOffset: 16, val: count + 1);
		Mem:atomicStoreI64(addr: stateAddr + 8, val: 0);
		return newSAddr;
	}
}
