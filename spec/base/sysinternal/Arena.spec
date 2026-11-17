#! Package base:sysinternal
#! Pure-Spec unmanaged floor for bump-allocated object arenas.
##
## Arena layout (40 bytes):
##   offset  0: headChunk (i64 address of current chunk)
##   offset  8: chunkSize (i64 default chunk payload bytes)
##   offset 16: objList   (i64 address of i64[] tracked object addresses)
##   offset 24: objCount  (i64 number of tracked objects)
##   offset 32: objCap    (i64 capacity of objList)
##
## Chunk layout (24-byte header + payload):
##   offset  0: nextChunk (i64 address of previous chunk)
##   offset  8: used      (i64 bytes used in payload)
##   offset 16: cap       (i64 payload byte capacity)

Class is Arena{
	namespace: ['base', 'sysinternal'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', as Mem()],
		['base', 'sysinternal', as Conditional()],
		['base', 'sysinternal', as Loops()]
	];

	Function of Int is create(Int is defaultChunkBytes){
		local Int is csz: if({ defaultChunkBytes > 4096 }, { defaultChunkBytes }, { 65536 });
		local Int is a: Mem:alloc(bytes: 40);
		local Int is ch: base:sysinternal:Mem:vmAlloc(bytes: 24 + csz);
		Mem:storeI64(ptr: ch, byteOffset: 0, val: 0);
		Mem:storeI64(ptr: ch, byteOffset: 8, val: 0);
		Mem:storeI64(ptr: ch, byteOffset: 16, val: csz);
		Mem:storeI64(ptr: a, byteOffset: 0, val: ch);
		Mem:storeI64(ptr: a, byteOffset: 8, val: csz);
		Mem:storeI64(ptr: a, byteOffset: 16, val: 0);
		Mem:storeI64(ptr: a, byteOffset: 24, val: 0);
		Mem:storeI64(ptr: a, byteOffset: 32, val: 0);
		return a;
	}

	Function of Int is allocObj(Int is arenaAddr, Int is size, Int is destroyFn){
		local Int is rawTotal: 16 + if({ size > 0 }, { size }, { 8 });
		local Int is total: ((rawTotal + 7) >> 3) << 3;
		local Int is ch: Mem:loadI64(ptr: arenaAddr, byteOffset: 0);
		local Int is used: Mem:loadI64(ptr: ch, byteOffset: 8);
		local Int is cap: Mem:loadI64(ptr: ch, byteOffset: 16);
		if({ used + total > cap }, {
			local Int is defCsz: Mem:loadI64(ptr: arenaAddr, byteOffset: 8);
			local Int is ncsz: if({ total > defCsz }, { total }, { defCsz });
			local Int is nch: base:sysinternal:Mem:vmAlloc(bytes: 24 + ncsz);
			Mem:storeI64(ptr: nch, byteOffset: 0, val: ch);
			Mem:storeI64(ptr: nch, byteOffset: 8, val: 0);
			Mem:storeI64(ptr: nch, byteOffset: 16, val: ncsz);
			Mem:storeI64(ptr: arenaAddr, byteOffset: 0, val: nch);
			ch: nch;
			used: 0;
		});
		local Int is h: ch + 24 + used;
		Mem:storeI64(ptr: ch, byteOffset: 8, val: used + total);
		Mem:storeI32(ptr: h, byteOffset: 0, val: 1);
		Mem:storeI32(ptr: h, byteOffset: 4, val: 4);
		Mem:storeI64(ptr: h, byteOffset: 8, val: destroyFn);
		local Int is obj: h + 16;
		if({ destroyFn != 0 }, {
			local Int is cnt: Mem:loadI64(ptr: arenaAddr, byteOffset: 24);
			local Int is ocap: Mem:loadI64(ptr: arenaAddr, byteOffset: 32);
			if({ cnt == ocap }, {
				local Int is nocap: if({ ocap == 0 }, { 64 }, { ocap * 2 });
				local Int is olist: Mem:loadI64(ptr: arenaAddr, byteOffset: 16);
				local Int is nlist: Mem:realloc(ptr: olist, bytes: nocap * 8);
				Mem:storeI64(ptr: arenaAddr, byteOffset: 16, val: nlist);
				Mem:storeI64(ptr: arenaAddr, byteOffset: 32, val: nocap);
			});
			local Int is list: Mem:loadI64(ptr: arenaAddr, byteOffset: 16);
			Mem:storeI64(ptr: list, byteOffset: cnt * 8, val: obj);
			Mem:storeI64(ptr: arenaAddr, byteOffset: 24, val: cnt + 1);
		});
		return obj;
	}

	Function is reset(Int is arenaAddr){
		if({ arenaAddr == 0 }, { return; });
		local Int is list: Mem:loadI64(ptr: arenaAddr, byteOffset: 16);
		local Int is i: Mem:loadI64(ptr: arenaAddr, byteOffset: 24);
		while({ i > 0 }, {
			i: i - 1;
			local Int is obj: Mem:loadI64(ptr: list, byteOffset: i * 8);
			local Int is h: obj - 16;
			local Int is d: Mem:loadI64(ptr: h, byteOffset: 8);
			if({ d != 0 }, {
				Mem:storeI64(ptr: h, byteOffset: 8, val: 0);
				Mem:callDestroy(fnPtr: d, objPtr: obj);
			});
		});
		Mem:storeI64(ptr: arenaAddr, byteOffset: 24, val: 0);
		local Int is head: Mem:loadI64(ptr: arenaAddr, byteOffset: 0);
		if({ head != 0 }, {
			local Int is cur: Mem:loadI64(ptr: head, byteOffset: 0);
			while({ cur != 0 }, {
				local Int is nxt: Mem:loadI64(ptr: cur, byteOffset: 0);
				local Int is ccap: Mem:loadI64(ptr: cur, byteOffset: 16);
				base:sysinternal:Mem:vmFree(ptr: cur, bytes: 24 + ccap);
				cur: nxt;
			});
			Mem:storeI64(ptr: head, byteOffset: 0, val: 0);
			local Int is cap: Mem:loadI64(ptr: head, byteOffset: 16);
			local Int is used: Mem:loadI64(ptr: head, byteOffset: 8);
			if({ used > 0 && used <= cap }, {
				Mem:set(dst: head + 24, byteVal: 0, bytes: used);
			});
			Mem:storeI64(ptr: head, byteOffset: 8, val: 0);
		});
	}

	Function is destroyArena(Int is arenaAddr){
		if({ arenaAddr == 0 }, { return; });
		self:reset(arenaAddr: arenaAddr);
		local Int is head: Mem:loadI64(ptr: arenaAddr, byteOffset: 0);
		if({ head != 0 }, {
			local Int is hcap: Mem:loadI64(ptr: head, byteOffset: 16);
			base:sysinternal:Mem:vmFree(ptr: head, bytes: 24 + hcap);
		});
		local Int is list: Mem:loadI64(ptr: arenaAddr, byteOffset: 16);
		if({ list != 0 }, { Mem:free(ptr: list); });
		Mem:free(ptr: arenaAddr);
	}
}
