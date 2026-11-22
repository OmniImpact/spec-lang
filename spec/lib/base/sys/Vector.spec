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

	## Allocates a new primitive-element SpecArray (elem_kind = 0).
	Function of Any is newVec(){
		local Int is aAddr: Mem:allocArcKind(bytes: 40, kind: 2);
		return Mem:addrToObj(addr: aAddr);
	}

	## Allocates a new ARC-element SpecArray (elem_kind = 1).
	Function of Any is newVecObject(){
		local Int is aAddr: Mem:allocArcKind(bytes: 40, kind: 2);
		Mem:storeI32(ptr: aAddr, byteOffset: 24, val: 1);
		return Mem:addrToObj(addr: aAddr);
	}

	## Allocates a new empty SpecArray with the same elem_kind as [v].
	Function of Any is newVecLike(Any is v){
		local Int is vAddr: Mem:objToAddr(obj: v);
		if({ vAddr != 0 && Mem:loadI32(ptr: vAddr, byteOffset: 24) == 1 }, {
			return :newVecObject();
		});
		return :newVec();
	}

	## Allocates a new compact SpecByteBuffer (24 bytes).
	Function of Any is newByteBuf(){
		local Int is bAddr: Mem:allocArcKind(bytes: 24, kind: 3);
		return Mem:addrToObj(addr: bAddr);
	}

	## Destroys this vector, releasing any ARC elements and freeing its backing array.
	Function is vecDestroy(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return; });
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 0);
		if({ items != 0 }, {
			local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 24);
			if({ kind == 1 }, {
				local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
				local Int is i: 0;
				while({ i < len }, {
					local Int is it: Mem:loadI64(ptr: items, byteOffset: i * 8);
					if({ it != 0 }, { Mem:releaseAddr(objAddr: it); });
					i: i + 1;
				});
			});
			Mem:free(ptr: items);
			Mem:storeI64(ptr: addr, byteOffset: 0, val: 0);
		});
	}

	## Destroys this byte buffer, freeing its backing byte array.
	Function is byteBufDestroy(){
		local Int is addr: Mem:objToAddr(obj: :);
		if({ addr == 0 }, { return; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		if({ data != 0 }, {
			Mem:free(ptr: data);
			Mem:storeI64(ptr: addr, byteOffset: 0, val: 0);
		});
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
		:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		:unlockVec(addr: addr);
		return len;
	}

	## Item at [idx] in vector [v], or [def] when out of bounds.
	Function of Any is vecGetAt(Any is v, Int is idx, Any is def){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return def; });
		local Boolean is isFrozen: Mem:loadByte(ptr: addr, byteOffset: 28) != 0;
		if({ !isFrozen }, { :lockVec(addr: addr); });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			if({ !isFrozen }, { :unlockVec(addr: addr); });
			return def;
		});
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is valAddr: Mem:loadI64(ptr: items, byteOffset: idx * 8);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 24);
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
		local Boolean is isFrozen: Mem:loadByte(ptr: addr, byteOffset: 28) != 0;
		if({ !isFrozen }, { :lockVec(addr: addr); });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			if({ !isFrozen }, { :unlockVec(addr: addr); });
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
		if({ Mem:loadByte(ptr: addr, byteOffset: 28) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return;
		});
		:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			:unlockVec(addr: addr);
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
		:unlockVec(addr: addr);
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
		:lockVec(addr: addr);
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
		:unlockVec(addr: addr);
	}

	## Marks vector [v] as holding ARC objects and appends [item].
	Function is vecAddObject(Any is v, Any is item){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return; });
		if({ Mem:loadI32(ptr: addr, byteOffset: 24) == 0 }, {
			Mem:storeI32(ptr: addr, byteOffset: 24, val: 1);
		});
		:vecAdd(v: v, item: item);
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
			:lockVec(addr: aAddr);
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
		:unlockVec(addr: aAddr);
		:unlockVec(addr: oAddr);
	}

	## Removes and returns the last element of [v], or [def] when empty.
	Function of Any is vecPopLast(Any is v, Any is def){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, { return def; });
		if({ Mem:loadByte(ptr: addr, byteOffset: 28) != 0 }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return def;
		});
		:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len == 0 }, {
			:unlockVec(addr: addr);
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
		:unlockVec(addr: addr);
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
		:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			:unlockVec(addr: addr);
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
		:unlockVec(addr: addr);
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
		:lockVec(addr: addr);
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		local Int is items: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 24);
		Mem:storeI64(ptr: addr, byteOffset: 0, val: 0);
		Mem:storeI64(ptr: addr, byteOffset: 8, val: 0);
		Mem:storeI64(ptr: addr, byteOffset: 16, val: 0);
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
		Mem:storeByte(ptr: addr, byteOffset: 28, val: 1);
		:unlockVec(addr: addr);
	}

	## List of T get with optional error callback.
	Function of Any is vecGet(Any is v, Int is idx, Any is def, Function is error){
		local Int is addr: Mem:objToAddr(obj: v);
		if({ addr == 0 }, {
			:notifyError(error: error, msg: 'vector is uninitialized');
			return def;
		});
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			:notifyError(error: error, msg: 'vector index out of bounds: index ' . (idx as String) . ' for length ' . (len as String));
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
			:notifyError(error: error, msg: 'vector is uninitialized');
			return;
		});
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			:notifyError(error: error, msg: 'vector assignment out of bounds: index ' . (idx as String) . ' for length ' . (len as String));
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
			:notifyError(error: error, msg: 'vector is uninitialized');
			return def;
		});
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		local Int is kind: Mem:loadI32(ptr: addr, byteOffset: 24);
		if({ len == 0 }, {
			:notifyError(error: error, msg: 'vector pop on empty vector');
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
			:notifyError(error: error, msg: 'byte buffer is uninitialized');
			return def;
		});
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			:notifyError(error: error, msg: 'byte buffer index out of bounds: index ' . (idx as String) . ' for length ' . (len as String));
			return def;
		});
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		return Mem:loadByte(ptr: data, byteOffset: idx);
	}

	## List of Byte set with optional error callback.
	Function is byteBufSet(Any is b, Int is idx, Int is v, Function is error){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, {
			:notifyError(error: error, msg: 'byte buffer is uninitialized');
			return;
		});
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ idx < 0 || idx >= len }, {
			:notifyError(error: error, msg: 'byte buffer assignment out of bounds: index ' . (idx as String) . ' for length ' . (len as String));
			return;
		});
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		Mem:storeByte(ptr: data, byteOffset: idx, val: v);
	}

	## List of Byte pop with optional error callback.
	Function of Int is byteBufPop(Any is b, Int is def, Function is error){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, {
			:notifyError(error: error, msg: 'byte buffer is uninitialized');
			return def;
		});
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ len == 0 }, {
			:notifyError(error: error, msg: 'byte buffer pop on empty buffer');
			return def;
		});
		local Int is newLen: len - 1;
		Mem:storeI64(ptr: addr, byteOffset: 8, val: newLen);
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		return Mem:loadByte(ptr: data, byteOffset: newLen);
	}

	## Appends all bytes of [other] into byte buffer [b].
	Function is byteBufAppendBytes(Any is b, Any is other){
		local Int is addr: Mem:objToAddr(obj: b);
		local Int is oAddr: Mem:objToAddr(obj: other);
		if({ addr == 0 || oAddr == 0 }, { return; });
		local Int is n: Mem:loadI64(ptr: oAddr, byteOffset: 8);
		if({ n <= 0 }, { return; });
		local Int is oData: Mem:loadI64(ptr: oAddr, byteOffset: 0);
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
		if({ addr == oAddr }, {
			Mem:move(dst: data + len, src: data, bytes: n);
		}, {
			Mem:copy(dst: data + len, src: oData, bytes: n);
		});
		Mem:storeI64(ptr: addr, byteOffset: 8, val: len + n);
	}

	## Appends [count] bytes starting at [start] from [other] into byte buffer [b].
	Function is byteBufAppendRange(Any is b, Any is other, Int is start, Int is count){
		local Int is addr: Mem:objToAddr(obj: b);
		local Int is oAddr: Mem:objToAddr(obj: other);
		if({ addr == 0 || oAddr == 0 || count <= 0 }, { return; });
		local Int is oLen: Mem:loadI64(ptr: oAddr, byteOffset: 8);
		local Int is s: if({ start < 0 }, { 0 }, { start });
		if({ s >= oLen }, { return; });
		local Int is n: if({ s + count > oLen }, { oLen - s }, { count });
		if({ n <= 0 }, { return; });
		local Int is oData: Mem:loadI64(ptr: oAddr, byteOffset: 0);
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
		if({ addr == oAddr }, {
			Mem:move(dst: data + len, src: data + s, bytes: n);
		}, {
			Mem:copy(dst: data + len, src: oData + s, bytes: n);
		});
		Mem:storeI64(ptr: addr, byteOffset: 8, val: len + n);
	}

	## Returns a new byte buffer containing bytes [start..end) of [b].
	Function of Any is byteBufSlice(Any is b, Int is start, Int is end){
		local [Byte] is out;
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, { return out; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		local Int is s: if({ start < 0 }, { 0 }, { start });
		local Int is e: if({ end > len }, { len }, { end });
		if({ e > s }, {
			:byteBufAppendRange(b: out, other: b, start: s, count: e - s);
		});
		return out;
	}

	## Appends a 16-bit big-endian unsigned integer to byte buffer [b].
	Function is byteBufPushU16BE(Any is b, Int is v){
		:byteBufPush(b: b, v: (v >> 8) & 255);
		:byteBufPush(b: b, v: v & 255);
	}

	## Appends a 32-bit big-endian unsigned integer to byte buffer [b].
	Function is byteBufPushU32BE(Any is b, Int is v){
		:byteBufPush(b: b, v: (v >> 24) & 255);
		:byteBufPush(b: b, v: (v >> 16) & 255);
		:byteBufPush(b: b, v: (v >> 8) & 255);
		:byteBufPush(b: b, v: v & 255);
	}

	## Appends a 32-bit little-endian unsigned integer to byte buffer [b].
	Function is byteBufPushU32LE(Any is b, Int is v){
		:byteBufPush(b: b, v: v & 255);
		:byteBufPush(b: b, v: (v >> 8) & 255);
		:byteBufPush(b: b, v: (v >> 16) & 255);
		:byteBufPush(b: b, v: (v >> 24) & 255);
	}

	## Reads a 16-bit big-endian unsigned integer at [offset], or [def] if out of bounds.
	Function of Int is byteBufReadU16BE(Any is b, Int is offset, Int is def){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, { return def; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ offset < 0 || offset + 2 > len }, { return def; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is b0: Mem:loadByte(ptr: data, byteOffset: offset);
		local Int is b1: Mem:loadByte(ptr: data, byteOffset: offset + 1);
		return (b0 << 8) | b1;
	}

	## Reads a 32-bit big-endian unsigned integer at [offset], or [def] if out of bounds.
	Function of Int is byteBufReadU32BE(Any is b, Int is offset, Int is def){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, { return def; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ offset < 0 || offset + 4 > len }, { return def; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is b0: Mem:loadByte(ptr: data, byteOffset: offset);
		local Int is b1: Mem:loadByte(ptr: data, byteOffset: offset + 1);
		local Int is b2: Mem:loadByte(ptr: data, byteOffset: offset + 2);
		local Int is b3: Mem:loadByte(ptr: data, byteOffset: offset + 3);
		return ((b0 << 24) | (b1 << 16) | (b2 << 8) | b3) & 4294967295;
	}

	## Reads a 32-bit little-endian unsigned integer at [offset], or [def] if out of bounds.
	Function of Int is byteBufReadU32LE(Any is b, Int is offset, Int is def){
		local Int is addr: Mem:objToAddr(obj: b);
		if({ addr == 0 }, { return def; });
		local Int is len: Mem:loadI64(ptr: addr, byteOffset: 8);
		if({ offset < 0 || offset + 4 > len }, { return def; });
		local Int is data: Mem:loadI64(ptr: addr, byteOffset: 0);
		local Int is b0: Mem:loadByte(ptr: data, byteOffset: offset);
		local Int is b1: Mem:loadByte(ptr: data, byteOffset: offset + 1);
		local Int is b2: Mem:loadByte(ptr: data, byteOffset: offset + 2);
		local Int is b3: Mem:loadByte(ptr: data, byteOffset: offset + 3);
		return (b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)) & 4294967295;
	}
}
