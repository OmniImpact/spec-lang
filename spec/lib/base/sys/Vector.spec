#! Package base:sys
#! Pure-Spec implementation of dynamic pointer vectors (Array / List of T)
#! and byte buffers (List of Byte) over base:sys:Mem.
##
## SpecArray layout (56 bytes):
##   offset  0: _type_name (ptr C-string "Array", set by _spec_rt_alloc_kinded)
##   offset  8: _vtable    (ptr reserved class header slot)
##   offset 16: items      (i64 address of 8-byte slot buffer)
##   offset 24: length     (i64 element count)
##   offset 32: capacity   (i64 allocated slot count)
##   offset 40: elem_kind  (i32: 0 = primitive, 1 = ARC object)
##   offset 44: frozen     (i8:  0 = mutable, 1 = frozen)
##   offset 48: lock       (i64 atomic spinlock: 0 = unlocked, 1 = locked)
##
## SpecByteBuffer layout (40 bytes):
##   offset  0: _type_name (ptr C-string "ByteBuf", set by _spec_rt_alloc_kinded)
##   offset  8: _vtable    (ptr reserved class header slot)
##   offset 16: data       (i64 address of byte buffer)
##   offset 24: length     (i64 byte count)
##   offset 32: capacity   (i64 allocated byte capacity)

Class is Vector{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Mem()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	local Function is lockVec(Int is addr){
		while({ !Mem:atomicCasI64(addr: addr + 48, expected: 0, desired: 1) }, {
		});
	}

	local Function is unlockVec(Int is addr){
		Mem:atomicStoreI64(addr: addr + 48, val: 0);
	}

	## Allocates a new primitive-element SpecArray (elem_kind = 0).
	Function of Any is newVec(){
		local Int is aAddr: Mem:allocArcKind(bytes: 56, kind: 2);
		return Mem:addrToObj(addr: aAddr);
	}

	## Allocates a new ARC-element SpecArray (elem_kind = 1).
	Function of Any is newVecObject(){
		local Int is aAddr: Mem:allocArcKind(bytes: 56, kind: 2);
		Mem:storeI32(ptr: aAddr, byteOffset: 40, val: 1);
		return Mem:addrToObj(addr: aAddr);
	}

	## Allocates a new empty SpecArray with the same elem_kind as [v].
	Function of Any is newVecLike(Any is v){
		local Int is vAddr: Mem:objToAddr(obj: v);
		if({ vAddr != 0 && Mem:loadI32(ptr: vAddr, byteOffset: 40) == 1 }, {
			return :newVecObject();
		});
		return :newVec();
	}

	## Bootstrap-ratchet stub until _spec_rt_alloc_kinded no longer references it.
	Function is byteBufDestroy(){
	}

	## Destroys this vector, releasing any ARC elements and freeing its backing array.
	Function is vecDestroy(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return; });
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 16);
		if({ items != 0 }, {
			local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 40);
			if({ kind == 1 }, {
				local Int is len: Mem:loadI64(ptr: addr, byteOffset: 24);
				local Int is i: 0;
				while({ i < len }, {
					local Int is it: Mem:loadI64(ptr: items, byteOffset: i * 8);
					if({ it != 0 }, { Mem:releaseAddr(objAddr: it); });
					i: i + 1;
				});
			});
			Mem:free(ptr: items);
			Mem:storeI64(ptr: addr, byteOffset: 16, val: 0);
		});
	}

	## Number of elements held by the vector [v].
	Function of Int is vecLength(Any is v){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return 0; });
		if({ Mem:loadByte(ptr: addr, byteOffset: 44) != 0 }, {
			return Mem:loadI64(ptr: addr, byteOffset: 24);
		});
		:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 24);
		:unlockVec(addr: addr);
		return len;
	}

	## Item at [idx] in vector [v], or [def] when out of bounds.
	Function of Any is vecGetAt(Any is v, Int is idx, Any is def){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return def; });
		local Boolean is isFrozen: Mem:loadByte(ptr: addr, byteOffset: 44) != 0;
		if({ !isFrozen }, { :lockVec(addr: addr); });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 24);
		if({ idx < 0 || idx >= len }, {
			if({ !isFrozen }, { :unlockVec(addr: addr); });
			return def;
		});
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 16);
		local Int is valAddr: Mem:loadI64(ptr: items, byteOffset: idx * 8);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 40);
		if({ kind == 1 && valAddr != 0 }, {
			Mem:retainAddr(objAddr: valAddr);
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		if({ !isFrozen }, { :unlockVec(addr: addr); });
		return Mem:addrToObj(addr: valAddr);
	}

	## Item at [idx] in vector [v]; panics when out of bounds.
	Function of Any is vecGetChecked(Any is v, Int is idx){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, {
			Mem:panic(msg: 'Null pointer access on uninitialized Array');
			return Mem:addrToObj(addr: 0);
		});
		local Boolean is isFrozen: Mem:loadByte(ptr: addr, byteOffset: 44) != 0;
		if({ !isFrozen }, { :lockVec(addr: addr); });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 24);
		if({ idx < 0 || idx >= len }, {
			if({ !isFrozen }, { :unlockVec(addr: addr); });
			Mem:panic(msg: 'Array index out of bounds: index ' . (idx as String) . ' for length ' . (len as String));
			return Mem:addrToObj(addr: 0);
		});
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 16);
		local Int is valAddr: Mem:loadI64(ptr: items, byteOffset: idx * 8);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 40);
		if({ kind == 1 && valAddr != 0 }, {
			Mem:retainAddr(objAddr: valAddr);
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		if({ !isFrozen }, { :unlockVec(addr: addr); });
		return Mem:addrToObj(addr: valAddr);
	}

	## Overwrites item at [idx] in vector [v].
	Function is vecSetAt(Any is v, Int is idx, Any is item){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, {
			Mem:panic(msg: 'Null pointer access on uninitialized Array');
			return;
		});
		if({ Mem:loadByte(ptr: addr, byteOffset: 44) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return;
		});
		:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 24);
		if({ idx < 0 || idx >= len }, {
			:unlockVec(addr: addr);
			Mem:panic(msg: 'Array assignment index out of bounds: index ' . (idx as String) . ' for length ' . (len as String));
			return;
		});
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 16);
		local Int is itemAddr: Mem:objToAddr(obj: item);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 40);
		local Int is oldAddr: 0;
		if({ kind == 1 }, {
			if({ itemAddr != 0 }, { Mem:retainAddr(objAddr: itemAddr); });
			oldAddr: Mem:loadI64(ptr: items, byteOffset: idx * 8);
		});
		Mem:storeI64(ptr: items, byteOffset: idx * 8, val: itemAddr);
		:unlockVec(addr: addr);
		if({ kind == 1 && oldAddr != 0 }, {
			Mem:releaseAddr(objAddr: oldAddr);
		});
	}

	## Appends [item] to vector [v].
	Function is vecAdd(Any is v, Any is item){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return; });
		if({ Mem:loadByte(ptr: addr, byteOffset: 44) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return;
		});
		:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 24);
		local Int is cap: Mem:loadI64(ptr: addr, byteOffset: 32);
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 16);
		if({ len >= cap }, {
			local Int is ncap: if({ cap == 0 }, { 8 }, { cap * 2 });
			items: Mem:realloc(ptr: items, bytes: ncap * 8);
			Mem:storeI64(ptr: addr, byteOffset: 16, val: items);
			Mem:storeI64(ptr: addr, byteOffset: 32, val: ncap);
		});
		local Int is itemAddr: Mem:objToAddr(obj: item);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 40);
		if({ kind == 1 && itemAddr != 0 }, {
			Mem:retainAddr(objAddr: itemAddr);
		});
		Mem:storeI64(ptr: items, byteOffset: len * 8, val: itemAddr);
		Mem:storeI64(ptr: addr, byteOffset: 24, val: len + 1);
		:unlockVec(addr: addr);
	}

	## Marks vector [v] as holding ARC objects and appends [item].
	Function is vecAddObject(Any is v, Any is item){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return; });
		if({ Mem:loadI32(ptr: addr, byteOffset: 40) == 0 }, {
			Mem:storeI32(ptr: addr, byteOffset: 40, val: 1);
		});
		:vecAdd(v: v, item: item);
	}

	## Appends all elements of [other] into [v].
	Function is vecAddArray(Any is v, Any is other){
		local Int is aAddr: Mem:objToAddr(obj: v);
		local Int is oAddr: Mem:objToAddr(obj: other);
		if({ aAddr == 0 || oAddr == 0 }, { return; });
		if({ Mem:loadByte(ptr: aAddr, byteOffset: 44) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return;
		});
		if({ aAddr == oAddr }, {
			:lockVec(addr: aAddr);
			local Int is n: Mem:loadI64(ptr: aAddr, byteOffset: 24);
			local Int is cap: Mem:loadI64(ptr: aAddr, byteOffset: 32);
			local Int is items: Mem:loadI64(ptr: aAddr, byteOffset: 16);
			if({ n + n > cap }, {
				local Int is ncap: if({ cap == 0 }, { 8 }, { cap * 2 });
				while({ ncap < n + n }, { ncap: ncap * 2; });
				items: Mem:realloc(ptr: items, bytes: ncap * 8);
				Mem:storeI64(ptr: aAddr, byteOffset: 16, val: items);
				Mem:storeI64(ptr: aAddr, byteOffset: 32, val: ncap);
			});
			local Int is kind: Mem:loadI32(ptr: aAddr, byteOffset: 40);
			local Int is i: 0;
			while({ i < n }, {
				local Int is it: Mem:loadI64(ptr: items, byteOffset: i * 8);
				if({ kind == 1 && it != 0 }, { Mem:retainAddr(objAddr: it); });
				Mem:storeI64(ptr: items, byteOffset: (n + i) * 8, val: it);
				i: i + 1;
			});
			Mem:storeI64(ptr: aAddr, byteOffset: 24, val: n + n);
			:unlockVec(addr: aAddr);
			return;
		});
		if({ aAddr < oAddr }, {
			:lockVec(addr: aAddr);
			:lockVec(addr: oAddr);
		}, {
			:lockVec(addr: oAddr);
			:lockVec(addr: aAddr);
		});
		local Int is aLen: Mem:loadI64(ptr: aAddr, byteOffset: 24);
		local Int is oLen: Mem:loadI64(ptr: oAddr, byteOffset: 24);
		local Int is aCap: Mem:loadI64(ptr: aAddr, byteOffset: 32);
		local Int is aItems: Mem:loadI64(ptr: aAddr, byteOffset: 16);
		local Int is oItems: Mem:loadI64(ptr: oAddr, byteOffset: 16);
		if({ aLen + oLen > aCap }, {
			local Int is ncap2: if({ aCap == 0 }, { 8 }, { aCap * 2 });
			while({ ncap2 < aLen + oLen }, { ncap2: ncap2 * 2; });
			aItems: Mem:realloc(ptr: aItems, bytes: ncap2 * 8);
			Mem:storeI64(ptr: aAddr, byteOffset: 16, val: aItems);
			Mem:storeI64(ptr: aAddr, byteOffset: 32, val: ncap2);
		});
		local Int is aKind: Mem:loadI32(ptr: aAddr, byteOffset: 40);
		local Int is j: 0;
		while({ j < oLen }, {
			local Int is oit: Mem:loadI64(ptr: oItems, byteOffset: j * 8);
			if({ aKind == 1 && oit != 0 }, { Mem:retainAddr(objAddr: oit); });
			Mem:storeI64(ptr: aItems, byteOffset: (aLen + j) * 8, val: oit);
			j: j + 1;
		});
		Mem:storeI64(ptr: aAddr, byteOffset: 24, val: aLen + oLen);
		:unlockVec(addr: aAddr);
		:unlockVec(addr: oAddr);
	}

	## Removes and returns the last element of [v], panicking when empty.
	Function of Any is vecPopChecked(Any is v){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, {
			Mem:panic(msg: 'Array pop on empty array');
			return Mem:addrToObj(addr: 0);
		});
		if({ Mem:loadByte(ptr: addr, byteOffset: 44) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return Mem:addrToObj(addr: 0);
		});
		:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 24);
		if({ len == 0 }, {
			:unlockVec(addr: addr);
			Mem:panic(msg: 'Array pop on empty array');
			return Mem:addrToObj(addr: 0);
		});
		local Int is newLen: len - 1;
		Mem:storeI64(ptr: addr, byteOffset: 24, val: newLen);
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 16);
		local Int is valAddr: Mem:loadI64(ptr: items, byteOffset: newLen * 8);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 40);
		if({ kind == 1 && valAddr != 0 }, {
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		:unlockVec(addr: addr);
		return Mem:addrToObj(addr: valAddr);
	}

	## Removes and returns the element at [idx] from [v], panicking if out of bounds.
	Function of Any is vecRemoveAtChecked(Any is v, Int is idx){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, {
			Mem:panic(msg: 'Array index out of bounds');
			return Mem:addrToObj(addr: 0);
		});
		if({ Mem:loadByte(ptr: addr, byteOffset: 44) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return Mem:addrToObj(addr: 0);
		});
		:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 24);
		if({ idx < 0 || idx >= len }, {
			:unlockVec(addr: addr);
			Mem:panic(msg: 'Array index out of bounds: index ' . (idx as String) . ' for length ' . (len as String));
			return Mem:addrToObj(addr: 0);
		});
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 16);
		local Int is valAddr: Mem:loadI64(ptr: items, byteOffset: idx * 8);
		local Int is tailCount: len - idx - 1;
		if({ tailCount > 0 }, {
			Mem:move(dst: items + (idx * 8), src: items + ((idx + 1) * 8), bytes: tailCount * 8);
		});
		Mem:storeI64(ptr: addr, byteOffset: 24, val: len - 1);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 40);
		if({ kind == 1 && valAddr != 0 }, {
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		:unlockVec(addr: addr);
		return Mem:addrToObj(addr: valAddr);
	}

	## Removes and returns the last element of [v], or [def] when empty.
	Function of Any is vecPopLast(Any is v, Any is def){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return def; });
		if({ Mem:loadByte(ptr: addr, byteOffset: 44) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return def;
		});
		:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 24);
		if({ len == 0 }, {
			:unlockVec(addr: addr);
			return def;
		});
		local Int is newLen: len - 1;
		Mem:storeI64(ptr: addr, byteOffset: 24, val: newLen);
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 16);
		local Int is valAddr: Mem:loadI64(ptr: items, byteOffset: newLen * 8);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 40);
		if({ kind == 1 && valAddr != 0 }, {
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		:unlockVec(addr: addr);
		return Mem:addrToObj(addr: valAddr);
	}

	## Removes and returns the element at [idx] from [v], shifting trailing elements.
	Function of Any is vecRemoveAt(Any is v, Int is idx, Any is def){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return def; });
		if({ Mem:loadByte(ptr: addr, byteOffset: 44) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return def;
		});
		:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 24);
		if({ idx < 0 || idx >= len }, {
			:unlockVec(addr: addr);
			return def;
		});
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 16);
		local Int is valAddr: Mem:loadI64(ptr: items, byteOffset: idx * 8);
		local Int is tailCount: len - idx - 1;
		if({ tailCount > 0 }, {
			Mem:move(dst: items + (idx * 8), src: items + ((idx + 1) * 8), bytes: tailCount * 8);
		});
		Mem:storeI64(ptr: addr, byteOffset: 24, val: len - 1);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 40);
		if({ kind == 1 && valAddr != 0 }, {
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		:unlockVec(addr: addr);
		return Mem:addrToObj(addr: valAddr);
	}

	## Removes all elements from vector [v].
	Function is vecClear(Any is v){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return; });
		if({ Mem:loadByte(ptr: addr, byteOffset: 44) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return;
		});
		:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 24);
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 16);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 40);
		Mem:storeI64(ptr: addr, byteOffset: 16, val: 0);
		Mem:storeI64(ptr: addr, byteOffset: 24, val: 0);
		Mem:storeI64(ptr: addr, byteOffset: 32, val: 0);
		:unlockVec(addr: addr);
		if({ items != 0 }, {
			if({ kind == 1 }, {
				local Int is i: 0;
				while({ i < len }, {
					local Int is elem: Mem:loadI64(ptr: items, byteOffset: i * 8);
					if({ elem != 0 }, {
						Mem:releaseAddr(objAddr: elem);
					});
					i: i + 1;
				});
			});
			Mem:free(ptr: items);
		});
	}

	## Marks vector [v] as frozen (immutable).
	Function is vecFreeze(Any is v){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return; });
		:lockVec(addr: addr);
		Mem:storeByte(ptr: addr, byteOffset: 44, val: 1);
		:unlockVec(addr: addr);
	}
}
