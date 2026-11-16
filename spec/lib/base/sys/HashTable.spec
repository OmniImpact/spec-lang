#! Package base:sys
#! Pure-Spec implementation of chained power-of-two hash tables (Map of K to V)
#! over base:sys:Mem.
##
## SpecMap layout (48 bytes):
##   offset  0: buckets   (i64 address of 8-byte bucket pointer array)
##   offset  8: nbuckets  (i64 power-of-two bucket count, initially 8)
##   offset 16: length    (i64 entry count)
##   offset 24: key_kind  (i32: 0 = String, 1 = Int, 2 = Float, 3 = Object)
##   offset 28: val_kind  (i32: 0 = primitive, 1 = ARC object)
##   offset 32: frozen    (i8:  0 = mutable, 1 = frozen)
##   offset 40: lock      (i64 atomic spinlock: 0 = unlocked, 1 = locked)
##
## SpecMapEntry layout (32 bytes):
##   offset  0: key_bits  (i64 key bits or pointer address)
##   offset  8: value     (i64 value bits or pointer address)
##   offset 16: is_str    (i8:  1 when value is an ARC String/Object)
##   offset 24: next      (i64 address of next SpecMapEntry in bucket chain)

Class is HashTable{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Mem()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

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
				a:add(item: kBits);
				curr: Mem:loadI64(ptr: curr, byteOffset: 24);
			});
			i: i + 1;
		});
		if({ !isFrozen }, { self:mapUnlock(addr: mAddr); });
		return a;
	}
}
