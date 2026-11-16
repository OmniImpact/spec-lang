#! Package base:sys
#! Pure-Spec implementation of dynamic pointer vectors (Array / List of T)
#! and byte buffers (List of Byte) over base:sys:Mem.
##
## SpecArray layout (40 bytes):
##   offset  0: items     (i64 address of 8-byte slot buffer)
##   offset  8: length    (i64 element count)
##   offset 16: capacity  (i64 allocated slot count)
##   offset 24: elem_kind (i32: 0 = primitive, 1 = ARC object)
##   offset 28: frozen    (i8:  0 = mutable, 1 = frozen)
##   offset 32: lock      (i64 atomic spinlock: 0 = unlocked, 1 = locked)
##
## SpecByteBuffer layout (24 bytes):
##   offset  0: data      (i64 address of byte buffer)
##   offset  8: length    (i64 byte count)
##   offset 16: capacity  (i64 allocated byte capacity)

Class is Vector{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Mem()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	local Function is lockVec(Int is addr){
		while({ !Mem:atomicCasI64(addr: addr + 32, expected: 0, desired: 1) }, {
		});
	}

	local Function is unlockVec(Int is addr){
		Mem:atomicStoreI64(addr: addr + 32, val: 0);
	}

	local Function is notifyError(Function is error, String is msg){
		local Int is errAddr: Mem:objToAddr(obj: error);
		if({ errAddr != 0 }, {
			if({ Mem:loadI64(ptr: errAddr, byteOffset: 0) != 0 }, {
				error(msg);
			});
		});
	}

	## Number of elements held by the vector [v].
	Function of Int is vecLength(Any is v){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return 0; });
		if({ Mem:loadByte(ptr: addr, byteOffset: 28) != 0 }, {
			return Mem:loadI64(ptr: addr, byteOffset: 8);
		});
		self:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		self:unlockVec(addr: addr);
		return len;
	}

	## Item at [idx] in vector [v], or [def] when out of bounds.
	Function of Any is vecGetAt(Any is v, Int is idx, Any is def){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return def; });
		local Boolean is isFrozen: Mem:loadByte(ptr: addr, byteOffset: 28) != 0;
		if({ !isFrozen }, { self:lockVec(addr: addr); });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			if({ !isFrozen }, { self:unlockVec(addr: addr); });
			return def;
		});
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is valAddr: Mem:loadI64(ptr: items, byteOffset: idx * 8);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 24);
		if({ kind == 1 && valAddr != 0 }, {
			Mem:retainAddr(objAddr: valAddr);
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		if({ !isFrozen }, { self:unlockVec(addr: addr); });
		return Mem:addrToObj(addr: valAddr);
	}

	## Item at [idx] in vector [v]; panics when out of bounds.
	Function of Any is vecGetChecked(Any is v, Int is idx){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, {
			Mem:panic(msg: 'Null pointer access on uninitialized Array');
			return Mem:addrToObj(addr: 0);
		});
		local Boolean is isFrozen: Mem:loadByte(ptr: addr, byteOffset: 28) != 0;
		if({ !isFrozen }, { self:lockVec(addr: addr); });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			if({ !isFrozen }, { self:unlockVec(addr: addr); });
			Mem:panic(msg: 'Array index out of bounds: index ' . (idx as String) . ' for length ' . (len as String));
			return Mem:addrToObj(addr: 0);
		});
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is valAddr: Mem:loadI64(ptr: items, byteOffset: idx * 8);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 24);
		if({ kind == 1 && valAddr != 0 }, {
			Mem:retainAddr(objAddr: valAddr);
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		if({ !isFrozen }, { self:unlockVec(addr: addr); });
		return Mem:addrToObj(addr: valAddr);
	}

	## Overwrites item at [idx] in vector [v].
	Function is vecSetAt(Any is v, Int is idx, Any is item){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, {
			Mem:panic(msg: 'Null pointer access on uninitialized Array');
			return;
		});
		if({ Mem:loadByte(ptr: addr, byteOffset: 28) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return;
		});
		self:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			self:unlockVec(addr: addr);
			Mem:panic(msg: 'Array assignment index out of bounds: index ' . (idx as String) . ' for length ' . (len as String));
			return;
		});
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is itemAddr: Mem:objToAddr(obj: item);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 24);
		local Int is oldAddr: 0;
		if({ kind == 1 }, {
			if({ itemAddr != 0 }, { Mem:retainAddr(objAddr: itemAddr); });
			oldAddr: Mem:loadI64(ptr: items, byteOffset: idx * 8);
		});
		Mem:storeI64(ptr: items, byteOffset: idx * 8, val: itemAddr);
		self:unlockVec(addr: addr);
		if({ kind == 1 && oldAddr != 0 }, {
			Mem:releaseAddr(objAddr: oldAddr);
		});
	}

	## Appends [item] to vector [v].
	Function is vecAdd(Any is v, Any is item){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return; });
		if({ Mem:loadByte(ptr: addr, byteOffset: 28) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return;
		});
		self:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		local Int is cap: Mem:loadI64(ptr: addr, byteOffset: 16);
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 0);
		if({ len >= cap }, {
			local Int is ncap: if({ cap == 0 }, { 8 }, { cap * 2 });
			items: Mem:realloc(ptr: items, bytes: ncap * 8);
			Mem:storeI64(ptr: addr, byteOffset: 0, val: items);
			Mem:storeI64(ptr: addr, byteOffset: 16, val: ncap);
		});
		local Int is itemAddr: Mem:objToAddr(obj: item);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 24);
		if({ kind == 1 && itemAddr != 0 }, {
			Mem:retainAddr(objAddr: itemAddr);
		});
		Mem:storeI64(ptr: items, byteOffset: len * 8, val: itemAddr);
		Mem:storeI64(ptr: addr, byteOffset: 8, val: len + 1);
		self:unlockVec(addr: addr);
	}

	## Marks vector [v] as holding ARC objects and appends [item].
	Function is vecAddObject(Any is v, Any is item){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return; });
		if({ Mem:loadI32(ptr: addr, byteOffset: 24) == 0 }, {
			Mem:storeI32(ptr: addr, byteOffset: 24, val: 1);
		});
		self:vecAdd(v: v, item: item);
	}

	## Appends all elements of [other] into [v].
	Function is vecAddArray(Any is v, Any is other){
		local Int is aAddr: Mem:objToAddr(obj: v);
		local Int is oAddr: Mem:objToAddr(obj: other);
		if({ aAddr == 0 || oAddr == 0 }, { return; });
		if({ Mem:loadByte(ptr: aAddr, byteOffset: 28) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return;
		});
		if({ aAddr == oAddr }, {
			self:lockVec(addr: aAddr);
			local Int is n: Mem:loadI64(ptr: aAddr, byteOffset: 8);
			local Int is cap: Mem:loadI64(ptr: aAddr, byteOffset: 16);
			local Int is items: Mem:loadI64(ptr: aAddr, byteOffset: 0);
			if({ n + n > cap }, {
				local Int is ncap: if({ cap == 0 }, { 8 }, { cap * 2 });
				while({ ncap < n + n }, { ncap: ncap * 2; });
				items: Mem:realloc(ptr: items, bytes: ncap * 8);
				Mem:storeI64(ptr: aAddr, byteOffset: 0, val: items);
				Mem:storeI64(ptr: aAddr, byteOffset: 16, val: ncap);
			});
			local Int is kind: Mem:loadI32(ptr: aAddr, byteOffset: 24);
			local Int is i: 0;
			while({ i < n }, {
				local Int is it: Mem:loadI64(ptr: items, byteOffset: i * 8);
				if({ kind == 1 && it != 0 }, { Mem:retainAddr(objAddr: it); });
				Mem:storeI64(ptr: items, byteOffset: (n + i) * 8, val: it);
				i: i + 1;
			});
			Mem:storeI64(ptr: aAddr, byteOffset: 8, val: n + n);
			self:unlockVec(addr: aAddr);
			return;
		});
		if({ aAddr < oAddr }, {
			self:lockVec(addr: aAddr);
			self:lockVec(addr: oAddr);
		}, {
			self:lockVec(addr: oAddr);
			self:lockVec(addr: aAddr);
		});
		local Int is aLen: Mem:loadI64(ptr: aAddr, byteOffset: 8);
		local Int is oLen: Mem:loadI64(ptr: oAddr, byteOffset: 8);
		local Int is aCap: Mem:loadI64(ptr: aAddr, byteOffset: 16);
		local Int is aItems: Mem:loadI64(ptr: aAddr, byteOffset: 0);
		local Int is oItems: Mem:loadI64(ptr: oAddr, byteOffset: 0);
		if({ aLen + oLen > aCap }, {
			local Int is ncap2: if({ aCap == 0 }, { 8 }, { aCap * 2 });
			while({ ncap2 < aLen + oLen }, { ncap2: ncap2 * 2; });
			aItems: Mem:realloc(ptr: aItems, bytes: ncap2 * 8);
			Mem:storeI64(ptr: aAddr, byteOffset: 0, val: aItems);
			Mem:storeI64(ptr: aAddr, byteOffset: 16, val: ncap2);
		});
		local Int is aKind: Mem:loadI32(ptr: aAddr, byteOffset: 24);
		local Int is j: 0;
		while({ j < oLen }, {
			local Int is oit: Mem:loadI64(ptr: oItems, byteOffset: j * 8);
			if({ aKind == 1 && oit != 0 }, { Mem:retainAddr(objAddr: oit); });
			Mem:storeI64(ptr: aItems, byteOffset: (aLen + j) * 8, val: oit);
			j: j + 1;
		});
		Mem:storeI64(ptr: aAddr, byteOffset: 8, val: aLen + oLen);
		self:unlockVec(addr: aAddr);
		self:unlockVec(addr: oAddr);
	}

	## Removes and returns the last element of [v], or [def] when empty.
	Function of Any is vecPopLast(Any is v, Any is def){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return def; });
		if({ Mem:loadByte(ptr: addr, byteOffset: 28) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return def;
		});
		self:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len == 0 }, {
			self:unlockVec(addr: addr);
			return def;
		});
		local Int is newLen: len - 1;
		Mem:storeI64(ptr: addr, byteOffset: 8, val: newLen);
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is valAddr: Mem:loadI64(ptr: items, byteOffset: newLen * 8);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 24);
		if({ kind == 1 && valAddr != 0 }, {
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		self:unlockVec(addr: addr);
		return Mem:addrToObj(addr: valAddr);
	}

	## Removes and returns the element at [idx] from [v], shifting trailing elements.
	Function of Any is vecRemoveAt(Any is v, Int is idx, Any is def){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return def; });
		if({ Mem:loadByte(ptr: addr, byteOffset: 28) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return def;
		});
		self:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			self:unlockVec(addr: addr);
			return def;
		});
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is valAddr: Mem:loadI64(ptr: items, byteOffset: idx * 8);
		local Int is tailCount: len - idx - 1;
		if({ tailCount > 0 }, {
			Mem:move(dst: items + (idx * 8), src: items + ((idx + 1) * 8), bytes: tailCount * 8);
		});
		Mem:storeI64(ptr: addr, byteOffset: 8, val: len - 1);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 24);
		if({ kind == 1 && valAddr != 0 }, {
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		self:unlockVec(addr: addr);
		return Mem:addrToObj(addr: valAddr);
	}

	## Removes all elements from vector [v].
	Function is vecClear(Any is v){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return; });
		if({ Mem:loadByte(ptr: addr, byteOffset: 28) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return;
		});
		self:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 24);
		Mem:storeI64(ptr: addr, byteOffset: 0, val: 0);
		Mem:storeI64(ptr: addr, byteOffset: 8, val: 0);
		Mem:storeI64(ptr: addr, byteOffset: 16, val: 0);
		self:unlockVec(addr: addr);
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
		self:lockVec(addr: addr);
		Mem:storeByte(ptr: addr, byteOffset: 28, val: 1);
		self:unlockVec(addr: addr);
	}

	## List of T get with optional error callback.
	Function of Any is vecGet(Any is v, Int is idx, Any is def, Function is error){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, {
			self:notifyError(error: error, msg: 'vector is uninitialized');
			return def;
		});
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			self:notifyError(error: error, msg: 'vector index out of bounds: index ' . (idx as String) . ' for length ' . (len as String));
			return def;
		});
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is valAddr: Mem:loadI64(ptr: items, byteOffset: idx * 8);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 24);
		if({ kind == 1 && valAddr != 0 }, {
			Mem:retainAddr(objAddr: valAddr);
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		return Mem:addrToObj(addr: valAddr);
	}

	## List of T set with optional error callback.
	Function is vecSet(Any is v, Int is idx, Any is item, Function is error){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, {
			self:notifyError(error: error, msg: 'vector is uninitialized');
			return;
		});
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			self:notifyError(error: error, msg: 'vector assignment out of bounds: index ' . (idx as String) . ' for length ' . (len as String));
			return;
		});
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is itemAddr: Mem:objToAddr(obj: item);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 24);
		if({ kind == 1 }, {
			if({ itemAddr != 0 }, { Mem:retainAddr(objAddr: itemAddr); });
			local Int is oldAddr: Mem:loadI64(ptr: items, byteOffset: idx * 8);
			if({ oldAddr != 0 }, { Mem:releaseAddr(objAddr: oldAddr); });
		});
		Mem:storeI64(ptr: items, byteOffset: idx * 8, val: itemAddr);
	}

	## List of T pop with optional error callback.
	Function of Any is vecPop(Any is v, Any is def, Function is error){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, {
			self:notifyError(error: error, msg: 'vector is uninitialized');
			return def;
		});
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 24);
		if({ len == 0 }, {
			self:notifyError(error: error, msg: 'vector pop on empty vector');
			return def;
		});
		local Int is newLen: len - 1;
		Mem:storeI64(ptr: addr, byteOffset: 8, val: newLen);
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is valAddr: Mem:loadI64(ptr: items, byteOffset: newLen * 8);
		if({ kind == 1 && valAddr != 0 }, {
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		return Mem:addrToObj(addr: valAddr);
	}

	## List of Byte length.
	Function of Int is byteBufLength(Any is b){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, { return 0; });
		return Mem:loadI64(ptr: addr, byteOffset: 8);
	}

	## List of Byte clear.
	Function is byteBufClear(Any is b){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr != 0 }, {
			Mem:storeI64(ptr: addr, byteOffset: 8, val: 0);
		});
	}

	## List of Byte push.
	Function is byteBufPush(Any is b, Int is v){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, { return; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		local Int is cap: Mem:loadI64(ptr: addr, byteOffset: 16);
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		if({ len >= cap }, {
			cap: if({ cap == 0 }, { 16 }, { cap * 2 });
			data: Mem:realloc(ptr: data, bytes: cap);
			Mem:storeI64(ptr: addr, byteOffset: 0, val: data);
			Mem:storeI64(ptr: addr, byteOffset: 16, val: cap);
		});
		Mem:storeByte(ptr: data, byteOffset: len, val: v);
		Mem:storeI64(ptr: addr, byteOffset: 8, val: len + 1);
	}

	## List of Byte appendString.
	Function is byteBufAppendString(Any is b, String is s){
		local Int is addr: Mem:objToAddr(obj: b);
		local Int is sAddr: Mem:objToAddr(obj: s);
		if({ addr == 0 || sAddr == 0 }, { return; });
		local Int is n: Mem:loadI64(ptr: sAddr, byteOffset: 8);
		if({ n <= 0 }, { return; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		local Int is cap: Mem:loadI64(ptr: addr, byteOffset: 16);
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		if({ len + n > cap }, {
			if({ cap == 0 }, { cap: 16; });
			while({ cap < len + n }, { cap: cap * 2; });
			data: Mem:realloc(ptr: data, bytes: cap);
			Mem:storeI64(ptr: addr, byteOffset: 0, val: data);
			Mem:storeI64(ptr: addr, byteOffset: 16, val: cap);
		});
		local Int is sData: Mem:loadI64(ptr: sAddr, byteOffset: 0);
		Mem:copy(dst: data + len, src: sData, bytes: n);
		Mem:storeI64(ptr: addr, byteOffset: 8, val: len + n);
	}

	## List of Byte toString.
	Function of String is byteBufToString(Any is b){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, { return ''; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len <= 0 }, { return ''; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		return Mem:strFromBytes(srcAddr: data, len: len);
	}

	## List of Byte get with optional error callback.
	Function of Int is byteBufGet(Any is b, Int is idx, Int is def, Function is error){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, {
			self:notifyError(error: error, msg: 'byte buffer is uninitialized');
			return def;
		});
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			self:notifyError(error: error, msg: 'byte buffer index out of bounds: index ' . (idx as String) . ' for length ' . (len as String));
			return def;
		});
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		return Mem:loadByte(ptr: data, byteOffset: idx);
	}

	## List of Byte set with optional error callback.
	Function is byteBufSet(Any is b, Int is idx, Int is v, Function is error){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, {
			self:notifyError(error: error, msg: 'byte buffer is uninitialized');
			return;
		});
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			self:notifyError(error: error, msg: 'byte buffer assignment out of bounds: index ' . (idx as String) . ' for length ' . (len as String));
			return;
		});
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		Mem:storeByte(ptr: data, byteOffset: idx, val: v);
	}

	## List of Byte pop with optional error callback.
	Function of Int is byteBufPop(Any is b, Int is def, Function is error){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, {
			self:notifyError(error: error, msg: 'byte buffer is uninitialized');
			return def;
		});
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len == 0 }, {
			self:notifyError(error: error, msg: 'byte buffer pop on empty buffer');
			return def;
		});
		local Int is newLen: len - 1;
		Mem:storeI64(ptr: addr, byteOffset: 8, val: newLen);
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		return Mem:loadByte(ptr: data, byteOffset: newLen);
	}

	local Function is mapLock(Int is addr){
		while({ !Mem:atomicCasI64(addr: addr + 40, expected: 0, desired: 1) }, {
		});
	}

	local Function is mapUnlock(Int is addr){
		Mem:atomicStoreI64(addr: addr + 40, val: 0);
	}

	local Function of Int is mapHashString(Int is strAddr, Int is nbuckets){
		if({ strAddr == 0 }, { return 0; });
		local Int is data: Mem:loadI64(ptr: strAddr, byteOffset: 0);
		local Int is len: Mem:loadI64(ptr: strAddr, byteOffset: 8);
		local Int is h: 1469598103934665603;
		local Int is i: 0;
		while({ i < len }, {
			h: (h ^ Mem:loadByte(ptr: data, byteOffset: i)) * 1099511628211;
			i: i + 1;
		});
		return h & (nbuckets - 1);
	}

	local Function of Int is mapHashBits(Int is k, Int is nbuckets){
		local Int is s1: (k >> 30) & 17179869183;
		k: (k ^ s1) * 1099511628211;
		local Int is s2: (k >> 27) & 137438953471;
		k: (k ^ s2) * 6364136223846793005;
		local Int is s3: (k >> 31) & 8589934591;
		k: k ^ s3;
		return k & (nbuckets - 1);
	}

	local Function of Boolean is mapStrKeyEquals(Int is aAddr, Int is bAddr){
		if({ aAddr == bAddr }, { return true; });
		if({ aAddr == 0 || bAddr == 0 }, { return false; });
		local Int is aLen: Mem:loadI64(ptr: aAddr, byteOffset: 8);
		local Int is bLen: Mem:loadI64(ptr: bAddr, byteOffset: 8);
		if({ aLen != bLen }, { return false; });
		if({ aLen == 0 }, { return true; });
		local Int is aData: Mem:loadI64(ptr: aAddr, byteOffset: 0);
		local Int is bData: Mem:loadI64(ptr: bAddr, byteOffset: 0);
		return Mem:cmp(a: aData, b: bData, bytes: aLen) == 0;
	}

	local Function of Int is mapFloatToBits(Float is k){
		if({ k == 0.0 }, { k: 0.0; });
		return Mem:floatToBits(val: k);
	}

	local Function is mapGrow(Int is mAddr){
		local Int is len: Mem:loadI64(ptr: mAddr, byteOffset: 16);
		local Int is nb: Mem:loadI64(ptr: mAddr, byteOffset: 8);
		if({ len < nb }, { return; });
		local Int is newNb: nb * 2;
		local Int is grown: Mem:alloc(bytes: newNb * 8);
		local Int is buckets: Mem:loadI64(ptr: mAddr, byteOffset: 0);
		local Int is keyKind: Mem:loadI32(ptr: mAddr, byteOffset: 24);
		local Int is i: 0;
		while({ i < nb }, {
			local Int is curr: Mem:loadI64(ptr: buckets, byteOffset: i * 8);
			while({ curr != 0 }, {
				local Int is next: Mem:loadI64(ptr: curr, byteOffset: 24);
				local Int is kBits: Mem:loadI64(ptr: curr, byteOffset: 0);
				local Int is idx: if({ keyKind == 0 }, {
					self:mapHashString(strAddr: kBits, nbuckets: newNb)
				}, {
					self:mapHashBits(k: kBits, nbuckets: newNb)
				});
				Mem:storeI64(ptr: curr, byteOffset: 24, val: Mem:loadI64(ptr: grown, byteOffset: idx * 8));
				Mem:storeI64(ptr: grown, byteOffset: idx * 8, val: curr);
				curr: next;
			});
			i: i + 1;
		});
		Mem:free(ptr: buckets);
		Mem:storeI64(ptr: mAddr, byteOffset: 0, val: grown);
		Mem:storeI64(ptr: mAddr, byteOffset: 8, val: newNb);
	}

	local Function is mapSetRaw(Int is mAddr, Int is keyBits, Int is valBits, Boolean is valIsArc){
		if({ mAddr == 0 }, { return; });
		if({ Mem:loadByte(ptr: mAddr, byteOffset: 32) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Map');
			return;
		});
		local Int is keyKind: Mem:loadI32(ptr: mAddr, byteOffset: 24);
		if({ keyKind == 0 && keyBits == 0 }, { return; });
		self:mapLock(addr: mAddr);
		local Int is valKind: Mem:loadI32(ptr: mAddr, byteOffset: 28);
		local Boolean is retainVal: valIsArc || (valKind == 1);
		local Int is arcByte: if({ retainVal }, { 1 }, { 0 });
		local Int is nb: Mem:loadI64(ptr: mAddr, byteOffset: 8);
		local Int is buckets: Mem:loadI64(ptr: mAddr, byteOffset: 0);
		local Int is idx: if({ keyKind == 0 }, {
			self:mapHashString(strAddr: keyBits, nbuckets: nb)
		}, {
			self:mapHashBits(k: keyBits, nbuckets: nb)
		});
		local Int is curr: Mem:loadI64(ptr: buckets, byteOffset: idx * 8);
		while({ curr != 0 }, {
			local Int is cKey: Mem:loadI64(ptr: curr, byteOffset: 0);
			local Boolean is matched: if({ keyKind == 0 }, {
				self:mapStrKeyEquals(aAddr: cKey, bAddr: keyBits)
			}, {
				cKey == keyBits
			});
			if({ matched }, {
				if({ retainVal && valBits != 0 }, {
					Mem:retainAddr(objAddr: valBits);
				});
				local Int is oldVal: Mem:loadI64(ptr: curr, byteOffset: 8);
				local Int is oldIsArc: Mem:loadByte(ptr: curr, byteOffset: 16);
				if({ (oldIsArc != 0 || valKind == 1) && oldVal != 0 }, {
					Mem:releaseAddr(objAddr: oldVal);
				});
				Mem:storeI64(ptr: curr, byteOffset: 8, val: valBits);
				Mem:storeByte(ptr: curr, byteOffset: 16, val: arcByte);
				self:mapUnlock(addr: mAddr);
				return;
			});
			curr: Mem:loadI64(ptr: curr, byteOffset: 24);
		});
		if({ retainVal && valBits != 0 }, {
			Mem:retainAddr(objAddr: valBits);
		});
		if({ (keyKind == 0 || keyKind == 3) && keyBits != 0 }, {
			Mem:retainAddr(objAddr: keyBits);
		});
		local Int is len: Mem:loadI64(ptr: mAddr, byteOffset: 16);
		if({ len >= nb }, {
			self:mapGrow(mAddr: mAddr);
			nb: Mem:loadI64(ptr: mAddr, byteOffset: 8);
			buckets: Mem:loadI64(ptr: mAddr, byteOffset: 0);
			idx: if({ keyKind == 0 }, {
				self:mapHashString(strAddr: keyBits, nbuckets: nb)
			}, {
				self:mapHashBits(k: keyBits, nbuckets: nb)
			});
		});
		local Int is e: Mem:alloc(bytes: 32);
		Mem:storeI64(ptr: e, byteOffset: 0, val: keyBits);
		Mem:storeI64(ptr: e, byteOffset: 8, val: valBits);
		Mem:storeByte(ptr: e, byteOffset: 16, val: arcByte);
		Mem:storeI64(ptr: e, byteOffset: 24, val: Mem:loadI64(ptr: buckets, byteOffset: idx * 8));
		Mem:storeI64(ptr: buckets, byteOffset: idx * 8, val: e);
		Mem:storeI64(ptr: mAddr, byteOffset: 16, val: len + 1);
		self:mapUnlock(addr: mAddr);
	}

	local Function of Any is mapGetRaw(Int is mAddr, Int is keyBits, Any is def){
		if({ mAddr == 0 }, { return def; });
		local Int is keyKind: Mem:loadI32(ptr: mAddr, byteOffset: 24);
		if({ keyKind == 0 && keyBits == 0 }, { return def; });
		local Boolean is isFrozen: Mem:loadByte(ptr: mAddr, byteOffset: 32) != 0;
		if({ !isFrozen }, { self:mapLock(addr: mAddr); });
		local Int is nb: Mem:loadI64(ptr: mAddr, byteOffset: 8);
		local Int is buckets: Mem:loadI64(ptr: mAddr, byteOffset: 0);
		local Int is idx: if({ keyKind == 0 }, {
			self:mapHashString(strAddr: keyBits, nbuckets: nb)
		}, {
			self:mapHashBits(k: keyBits, nbuckets: nb)
		});
		local Int is curr: Mem:loadI64(ptr: buckets, byteOffset: idx * 8);
		while({ curr != 0 }, {
			local Int is cKey: Mem:loadI64(ptr: curr, byteOffset: 0);
			local Boolean is matched: if({ keyKind == 0 }, {
				self:mapStrKeyEquals(aAddr: cKey, bAddr: keyBits)
			}, {
				cKey == keyBits
			});
			if({ matched }, {
				local Int is valBits: Mem:loadI64(ptr: curr, byteOffset: 8);
				local Int is isArc: Mem:loadByte(ptr: curr, byteOffset: 16);
				local Int is valKind: Mem:loadI32(ptr: mAddr, byteOffset: 28);
				if({ (isArc != 0 || valKind == 1) && valBits != 0 }, {
					Mem:retainAddr(objAddr: valBits);
					Mem:claimPoolAddr(objAddr: valBits);
				});
				if({ !isFrozen }, { self:mapUnlock(addr: mAddr); });
				return Mem:addrToObj(addr: valBits);
			});
			curr: Mem:loadI64(ptr: curr, byteOffset: 24);
		});
		if({ !isFrozen }, { self:mapUnlock(addr: mAddr); });
		return def;
	}

	local Function of Boolean is mapHasRaw(Int is mAddr, Int is keyBits){
		if({ mAddr == 0 }, { return false; });
		local Int is keyKind: Mem:loadI32(ptr: mAddr, byteOffset: 24);
		if({ keyKind == 0 && keyBits == 0 }, { return false; });
		local Boolean is isFrozen: Mem:loadByte(ptr: mAddr, byteOffset: 32) != 0;
		if({ !isFrozen }, { self:mapLock(addr: mAddr); });
		local Int is nb: Mem:loadI64(ptr: mAddr, byteOffset: 8);
		local Int is buckets: Mem:loadI64(ptr: mAddr, byteOffset: 0);
		local Int is idx: if({ keyKind == 0 }, {
			self:mapHashString(strAddr: keyBits, nbuckets: nb)
		}, {
			self:mapHashBits(k: keyBits, nbuckets: nb)
		});
		local Int is curr: Mem:loadI64(ptr: buckets, byteOffset: idx * 8);
		while({ curr != 0 }, {
			local Int is cKey: Mem:loadI64(ptr: curr, byteOffset: 0);
			local Boolean is matched: if({ keyKind == 0 }, {
				self:mapStrKeyEquals(aAddr: cKey, bAddr: keyBits)
			}, {
				cKey == keyBits
			});
			if({ matched }, {
				if({ !isFrozen }, { self:mapUnlock(addr: mAddr); });
				return true;
			});
			curr: Mem:loadI64(ptr: curr, byteOffset: 24);
		});
		if({ !isFrozen }, { self:mapUnlock(addr: mAddr); });
		return false;
	}

	local Function of Boolean is mapRemoveRaw(Int is mAddr, Int is keyBits){
		if({ mAddr == 0 }, { return false; });
		if({ Mem:loadByte(ptr: mAddr, byteOffset: 32) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Map');
			return false;
		});
		local Int is keyKind: Mem:loadI32(ptr: mAddr, byteOffset: 24);
		if({ keyKind == 0 && keyBits == 0 }, { return false; });
		self:mapLock(addr: mAddr);
		local Int is nb: Mem:loadI64(ptr: mAddr, byteOffset: 8);
		local Int is buckets: Mem:loadI64(ptr: mAddr, byteOffset: 0);
		local Int is idx: if({ keyKind == 0 }, {
			self:mapHashString(strAddr: keyBits, nbuckets: nb)
		}, {
			self:mapHashBits(k: keyBits, nbuckets: nb)
		});
		local Int is curr: Mem:loadI64(ptr: buckets, byteOffset: idx * 8);
		local Int is prev: 0;
		while({ curr != 0 }, {
			local Int is cKey: Mem:loadI64(ptr: curr, byteOffset: 0);
			local Boolean is matched: if({ keyKind == 0 }, {
				self:mapStrKeyEquals(aAddr: cKey, bAddr: keyBits)
			}, {
				cKey == keyBits
			});
			if({ matched }, {
				local Int is next: Mem:loadI64(ptr: curr, byteOffset: 24);
				if({ prev != 0 }, {
					Mem:storeI64(ptr: prev, byteOffset: 24, val: next);
				}, {
					Mem:storeI64(ptr: buckets, byteOffset: idx * 8, val: next);
				});
				if({ (keyKind == 0 || keyKind == 3) && cKey != 0 }, {
					Mem:releaseAddr(objAddr: cKey);
				});
				local Int is valBits: Mem:loadI64(ptr: curr, byteOffset: 8);
				local Int is isArc: Mem:loadByte(ptr: curr, byteOffset: 16);
				local Int is valKind: Mem:loadI32(ptr: mAddr, byteOffset: 28);
				if({ (isArc != 0 || valKind == 1) && valBits != 0 }, {
					Mem:releaseAddr(objAddr: valBits);
				});
				Mem:free(ptr: curr);
				local Int is len: Mem:loadI64(ptr: mAddr, byteOffset: 16);
				Mem:storeI64(ptr: mAddr, byteOffset: 16, val: len - 1);
				self:mapUnlock(addr: mAddr);
				return true;
			});
			prev: curr;
			curr: Mem:loadI64(ptr: curr, byteOffset: 24);
		});
		self:mapUnlock(addr: mAddr);
		return false;
	}

	Function is mapSet(Any is m, String is key, String is val){
		self:mapSetRaw(mAddr: Mem:objToAddr(obj: m), keyBits: Mem:objToAddr(obj: key), valBits: Mem:objToAddr(obj: val), valIsArc: true);
	}

	Function is mapSetAny(Any is m, String is key, Any is val){
		self:mapSetRaw(mAddr: Mem:objToAddr(obj: m), keyBits: Mem:objToAddr(obj: key), valBits: Mem:objToAddr(obj: val), valIsArc: false);
	}

	Function of Any is mapGet(Any is m, String is key, Any is def){
		return self:mapGetRaw(mAddr: Mem:objToAddr(obj: m), keyBits: Mem:objToAddr(obj: key), def: def);
	}

	Function of Boolean is mapHas(Any is m, String is key){
		return self:mapHasRaw(mAddr: Mem:objToAddr(obj: m), keyBits: Mem:objToAddr(obj: key));
	}

	Function of Boolean is mapRemove(Any is m, String is key){
		return self:mapRemoveRaw(mAddr: Mem:objToAddr(obj: m), keyBits: Mem:objToAddr(obj: key));
	}

	Function is mapSetInt(Any is m, Int is key, String is val){
		self:mapSetRaw(mAddr: Mem:objToAddr(obj: m), keyBits: key, valBits: Mem:objToAddr(obj: val), valIsArc: true);
	}

	Function is mapSetIntAny(Any is m, Int is key, Any is val){
		self:mapSetRaw(mAddr: Mem:objToAddr(obj: m), keyBits: key, valBits: Mem:objToAddr(obj: val), valIsArc: false);
	}

	Function of Any is mapGetInt(Any is m, Int is key, Any is def){
		return self:mapGetRaw(mAddr: Mem:objToAddr(obj: m), keyBits: key, def: def);
	}

	Function of Boolean is mapHasInt(Any is m, Int is key){
		return self:mapHasRaw(mAddr: Mem:objToAddr(obj: m), keyBits: key);
	}

	Function of Boolean is mapRemoveInt(Any is m, Int is key){
		return self:mapRemoveRaw(mAddr: Mem:objToAddr(obj: m), keyBits: key);
	}

	Function is mapSetFlt(Any is m, Float is key, String is val){
		self:mapSetRaw(mAddr: Mem:objToAddr(obj: m), keyBits: self:mapFloatToBits(k: key), valBits: Mem:objToAddr(obj: val), valIsArc: true);
	}

	Function is mapSetFltAny(Any is m, Float is key, Any is val){
		self:mapSetRaw(mAddr: Mem:objToAddr(obj: m), keyBits: self:mapFloatToBits(k: key), valBits: Mem:objToAddr(obj: val), valIsArc: false);
	}

	Function of Any is mapGetFlt(Any is m, Float is key, Any is def){
		return self:mapGetRaw(mAddr: Mem:objToAddr(obj: m), keyBits: self:mapFloatToBits(k: key), def: def);
	}

	Function of Boolean is mapHasFlt(Any is m, Float is key){
		return self:mapHasRaw(mAddr: Mem:objToAddr(obj: m), keyBits: self:mapFloatToBits(k: key));
	}

	Function of Boolean is mapRemoveFlt(Any is m, Float is key){
		return self:mapRemoveRaw(mAddr: Mem:objToAddr(obj: m), keyBits: self:mapFloatToBits(k: key));
	}

	Function is mapSetObj(Any is m, Any is key, String is val){
		self:mapSetRaw(mAddr: Mem:objToAddr(obj: m), keyBits: Mem:objToAddr(obj: key), valBits: Mem:objToAddr(obj: val), valIsArc: true);
	}

	Function is mapSetObjAny(Any is m, Any is key, Any is val){
		self:mapSetRaw(mAddr: Mem:objToAddr(obj: m), keyBits: Mem:objToAddr(obj: key), valBits: Mem:objToAddr(obj: val), valIsArc: false);
	}

	Function of Any is mapGetObj(Any is m, Any is key, Any is def){
		return self:mapGetRaw(mAddr: Mem:objToAddr(obj: m), keyBits: Mem:objToAddr(obj: key), def: def);
	}

	Function of Boolean is mapHasObj(Any is m, Any is key){
		return self:mapHasRaw(mAddr: Mem:objToAddr(obj: m), keyBits: Mem:objToAddr(obj: key));
	}

	Function of Boolean is mapRemoveObj(Any is m, Any is key){
		return self:mapRemoveRaw(mAddr: Mem:objToAddr(obj: m), keyBits: Mem:objToAddr(obj: key));
	}

	Function of Int is mapLength(Any is m){
		local Int is mAddr: Mem:objToAddr(obj: m);
		if({ mAddr == 0 }, { return 0; });
		if({ Mem:loadByte(ptr: mAddr, byteOffset: 32) != 0 }, {
			return Mem:loadI64(ptr: mAddr, byteOffset: 16);
		});
		self:mapLock(addr: mAddr);
		local Int is len: Mem:loadI64(ptr: mAddr, byteOffset: 16);
		self:mapUnlock(addr: mAddr);
		return len;
	}

	Function is mapFreeze(Any is m){
		local Int is mAddr: Mem:objToAddr(obj: m);
		if({ mAddr == 0 }, { return; });
		self:mapLock(addr: mAddr);
		Mem:storeByte(ptr: mAddr, byteOffset: 32, val: 1);
		self:mapUnlock(addr: mAddr);
	}

	Function of Array is mapKeys(Any is m){
		local Array of Int is a: [];
		local Int is mAddr: Mem:objToAddr(obj: m);
		if({ mAddr == 0 }, { return a; });
		local Int is keyKind: Mem:loadI32(ptr: mAddr, byteOffset: 24);
		if({ keyKind == 0 || keyKind == 3 }, {
			Mem:storeI32(ptr: Mem:objToAddr(obj: a), byteOffset: 24, val: 1);
		});
		local Boolean is isFrozen: Mem:loadByte(ptr: mAddr, byteOffset: 32) != 0;
		if({ !isFrozen }, { self:mapLock(addr: mAddr); });
		local Int is nb: Mem:loadI64(ptr: mAddr, byteOffset: 8);
		local Int is buckets: Mem:loadI64(ptr: mAddr, byteOffset: 0);
		local Int is i: 0;
		while({ i < nb }, {
			local Int is curr: Mem:loadI64(ptr: buckets, byteOffset: i * 8);
			while({ curr != 0 }, {
				local Int is kBits: Mem:loadI64(ptr: curr, byteOffset: 0);
				self:vecAdd(v: a, item: Mem:addrToObj(addr: kBits));
				curr: Mem:loadI64(ptr: curr, byteOffset: 24);
			});
			i: i + 1;
		});
		if({ !isFrozen }, { self:mapUnlock(addr: mAddr); });
		return a;
	}
}
