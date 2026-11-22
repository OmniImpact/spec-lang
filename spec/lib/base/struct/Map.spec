#! Package base:struct
#! Contiguous dynamic collections and associative hash maps.

## An associative key-value map.
##
## Monomorphized per instantiation (Map__String__Int and friends) with real
## Spec fields and SpinLock concurrency control over base:sys:Mem.

Class is Map of K to V{
	namespace: ['base', 'struct'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Mem()],
		['base', 'sys', SpinLock],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	local Int is buckets: 0;
	local Int is nbuckets: 0;
	local Int is len: 0;
	local Int is keyKind: 0;
	local Int is valKind: 0;
	local Boolean is frozen: false;
	local SpinLock is lock: SpinLock:init();

	replace Function is init(Int is keyKind: 0, Int is valKind: 0){
		:keyKind: keyKind;
		:valKind: valKind;
		:nbuckets: 8;
		:buckets: Mem:alloc(bytes: 64);
	}

	Function is destroy(){
		if({ :buckets == 0 }, { return; });
		local Int is i: 0;
		while({ i < :nbuckets }, {
			local Int is curr: Mem:loadI64(ptr: :buckets, byteOffset: i * 8);
			while({ curr != 0 }, {
				local Int is next: Mem:loadI64(ptr: curr, byteOffset: 24);
				local Int is kBits: Mem:loadI64(ptr: curr, byteOffset: 0);
				if({ :keyKind == 0 && kBits != 0 }, {
					Mem:releaseAddr(objAddr: kBits);
				});
				local Int is vBits: Mem:loadI64(ptr: curr, byteOffset: 8);
				local Int is isArc: Mem:loadByte(ptr: curr, byteOffset: 16);
				if({ (isArc != 0 || :valKind == 1) && vBits != 0 }, {
					Mem:releaseAddr(objAddr: vBits);
				});
				Mem:free(ptr: curr);
				curr: next;
			});
			i: i + 1;
		});
		Mem:free(ptr: :buckets);
		:buckets: 0;
	}

	local Function of Int is hashString(Int is strAddr, Int is nb){
		if({ strAddr == 0 }, { return 0; });
		local Int is data: Mem:loadI64(ptr: strAddr, byteOffset: 0);
		local Int is slen: Mem:loadI64(ptr: strAddr, byteOffset: 8);
		local Int is h: 1469598103934665603;
		local Int is i: 0;
		while({ i < slen }, {
			h: (h ^ Mem:loadByte(ptr: data, byteOffset: i)) * 1099511628211;
			i: i + 1;
		});
		return h & (nb - 1);
	}

	local Function of Int is hashBits(Int is k, Int is nb){
		local Int is s1: (k >> 30) & 17179869183;
		k: (k ^ s1) * 1099511628211;
		local Int is s2: (k >> 27) & 137438953471;
		k: (k ^ s2) * 6364136223846793005;
		local Int is s3: (k >> 31) & 8589934591;
		k: k ^ s3;
		return k & (nb - 1);
	}

	local Function of Boolean is strKeyEquals(Int is aAddr, Int is bAddr){
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

	local Function is growBuckets(){
		if({ :len < :nbuckets }, { return; });
		local Int is newNb: :nbuckets * 2;
		local Int is grown: Mem:alloc(bytes: newNb * 8);
		local Int is i: 0;
		while({ i < :nbuckets }, {
			local Int is curr: Mem:loadI64(ptr: :buckets, byteOffset: i * 8);
			while({ curr != 0 }, {
				local Int is next: Mem:loadI64(ptr: curr, byteOffset: 24);
				local Int is kBits: Mem:loadI64(ptr: curr, byteOffset: 0);
				local Int is idx: if({ :keyKind == 0 }, {
					:hashString(strAddr: kBits, nb: newNb)
				}, {
					:hashBits(k: kBits, nb: newNb)
				});
				Mem:storeI64(ptr: curr, byteOffset: 24, val: Mem:loadI64(ptr: grown, byteOffset: idx * 8));
				Mem:storeI64(ptr: grown, byteOffset: idx * 8, val: curr);
				curr: next;
			});
			i: i + 1;
		});
		Mem:free(ptr: :buckets);
		:buckets: grown;
		:nbuckets: newNb;
	}

	local Function of Int is normKeyBits(Int is keyBits){
		if({ :keyKind == 2 && (keyBits << 1) == 0 }, { return 0; });
		return keyBits;
	}

	local Function of Any is getRaw(Int is keyBits, Any is def){
		keyBits: :normKeyBits(keyBits: keyBits);
		if({ :keyKind == 0 && keyBits == 0 }, { return def; });
		local Boolean is isFrozen: :frozen;
		if({ !isFrozen }, { :lock:lock(); });
		local Int is idx: if({ :keyKind == 0 }, {
			:hashString(strAddr: keyBits, nb: :nbuckets)
		}, {
			:hashBits(k: keyBits, nb: :nbuckets)
		});
		local Int is curr: Mem:loadI64(ptr: :buckets, byteOffset: idx * 8);
		while({ curr != 0 }, {
			local Int is cKey: Mem:loadI64(ptr: curr, byteOffset: 0);
			local Boolean is matched: if({ :keyKind == 0 }, {
				:strKeyEquals(aAddr: cKey, bAddr: keyBits)
			}, {
				cKey == keyBits
			});
			if({ matched }, {
				local Int is valBits: Mem:loadI64(ptr: curr, byteOffset: 8);
				local Int is isArc: Mem:loadByte(ptr: curr, byteOffset: 16);
				if({ (isArc != 0 || :valKind == 1) && valBits != 0 }, {
					Mem:retainAddr(objAddr: valBits);
					Mem:claimPoolAddr(objAddr: valBits);
				});
				if({ !isFrozen }, { :lock:unlock(); });
				return Mem:addrToObj(addr: valBits);
			});
			curr: Mem:loadI64(ptr: curr, byteOffset: 24);
		});
		if({ !isFrozen }, { :lock:unlock(); });
		return def;
	}

	## Looks up the value mapped to [key], panicking if not found.
	Function of V is getChecked(K is key){
		local Int is keyBits: :normKeyBits(keyBits: Mem:objToAddr(obj: key));
		if({ :keyKind == 0 && keyBits == 0 }, {
			Mem:panic(msg: 'Map key not found');
			return Mem:addrToObj(addr: 0);
		});
		local Boolean is isFrozen: :frozen;
		if({ !isFrozen }, { :lock:lock(); });
		local Int is idx: if({ :keyKind == 0 }, {
			:hashString(strAddr: keyBits, nb: :nbuckets)
		}, {
			:hashBits(k: keyBits, nb: :nbuckets)
		});
		local Int is curr: Mem:loadI64(ptr: :buckets, byteOffset: idx * 8);
		while({ curr != 0 }, {
			local Int is cKey: Mem:loadI64(ptr: curr, byteOffset: 0);
			local Boolean is matched: if({ :keyKind == 0 }, {
				:strKeyEquals(aAddr: cKey, bAddr: keyBits)
			}, {
				cKey == keyBits
			});
			if({ matched }, {
				local Int is valBits: Mem:loadI64(ptr: curr, byteOffset: 8);
				local Int is isArc: Mem:loadByte(ptr: curr, byteOffset: 16);
				if({ (isArc != 0 || :valKind == 1) && valBits != 0 }, {
					Mem:retainAddr(objAddr: valBits);
					Mem:claimPoolAddr(objAddr: valBits);
				});
				if({ !isFrozen }, { :lock:unlock(); });
				return Mem:addrToObj(addr: valBits);
			});
			curr: Mem:loadI64(ptr: curr, byteOffset: 24);
		});
		if({ !isFrozen }, { :lock:unlock(); });
		Mem:panic(msg: 'Map key not found');
		return Mem:addrToObj(addr: 0);
	}

	## Marks this map as frozen (immutable).
	Function is freeze(){
		:lock:lock();
		:frozen: true;
		:lock:unlock();
	}

	## Looks up the value mapped to [key], returning [default] if not found.
	##
	## @param key: Lookup key string.
	## @param default: Fallback value returned if key is absent.
	## @return: Mapped value, or [default].
	## @fallback: Returns [default] when [key] does not exist in the map.
	Function of V is get(K is key, V is default){
		return :getRaw(keyBits: Mem:objToAddr(obj: key), def: default);
	}

	## Looks up a string value by key, returning [default] if not found.
	##
	## @param key: Lookup key.
	## @param default: Fallback string returned if key is absent.
	## @return: Mapped value, or [default].
	## @fallback: Returns [default] when [key] does not exist in the map.
	Function of String is getString(K is key, String is default){
		return :getRaw(keyBits: Mem:objToAddr(obj: key), def: default) as String;
	}

	## Looks up an integer value by key, returning [default] if not found.
	##
	## @param key: Lookup key.
	## @param default: Fallback integer returned if key is absent.
	## @return: Mapped value, or [default].
	Function of Int is getInt(K is key, Int is default){
		local String is s: :getString(key: key, default: '');
		if({ s:length() > 0 }, {
			return s:parseInt(base: 10, default: default);
		});
		return default;
	}

	## Looks up a float value by key, returning [default] if not found.
	##
	## @param key: Lookup key.
	## @param default: Fallback float returned if key is absent.
	## @return: Mapped value, or [default].
	Function of Float is getFloat(K is key, Float is default){
		return :getRaw(keyBits: Mem:objToAddr(obj: key), def: default) as Float;
	}

	## Looks up a boolean value by key, returning [default] if not found.
	##
	## @param key: Lookup key.
	## @param default: Fallback boolean returned if key is absent.
	## @return: Mapped value, or [default].
	Function of Boolean is getBool(K is key, Boolean is default){
		local String is s: :getString(key: key, default: '');
		return match(on: s, when: [
			'true': { true },
			'false': { false },
			else: { default }
		]);
	}

	## Inserts or updates an entry in the map, with an explicit per-entry ARC flag
	## (used by heterogeneous map literals and index assignment).
	Function is setEntry(K is key, V is value, Boolean is valIsArc){
		if({ :frozen }, {
			Mem:panic(msg: 'Mutation attempted on frozen Map');
			return;
		});
		local Int is keyBits: :normKeyBits(keyBits: Mem:objToAddr(obj: key));
		if({ :keyKind == 0 && keyBits == 0 }, { return; });
		local Int is valBits: Mem:objToAddr(obj: value);
		:lock:lock();
		local Boolean is retainVal: valIsArc || (:valKind == 1);
		local Int is arcByte: if({ retainVal }, { 1 }, { 0 });
		local Int is idx: if({ :keyKind == 0 }, {
			:hashString(strAddr: keyBits, nb: :nbuckets)
		}, {
			:hashBits(k: keyBits, nb: :nbuckets)
		});
		local Int is curr: Mem:loadI64(ptr: :buckets, byteOffset: idx * 8);
		while({ curr != 0 }, {
			local Int is cKey: Mem:loadI64(ptr: curr, byteOffset: 0);
			local Boolean is matched: if({ :keyKind == 0 }, {
				:strKeyEquals(aAddr: cKey, bAddr: keyBits)
			}, {
				cKey == keyBits
			});
			if({ matched }, {
				if({ retainVal && valBits != 0 }, {
					Mem:retainAddr(objAddr: valBits);
				});
				local Int is oldVal: Mem:loadI64(ptr: curr, byteOffset: 8);
				local Int is oldIsArc: Mem:loadByte(ptr: curr, byteOffset: 16);
				if({ (oldIsArc != 0 || :valKind == 1) && oldVal != 0 }, {
					Mem:releaseAddr(objAddr: oldVal);
				});
				Mem:storeI64(ptr: curr, byteOffset: 8, val: valBits);
				Mem:storeByte(ptr: curr, byteOffset: 16, val: arcByte);
				:lock:unlock();
				return;
			});
			curr: Mem:loadI64(ptr: curr, byteOffset: 24);
		});
		if({ retainVal && valBits != 0 }, {
			Mem:retainAddr(objAddr: valBits);
		});
		if({ :keyKind == 0 && keyBits != 0 }, {
			Mem:retainAddr(objAddr: keyBits);
		});
		if({ :len >= :nbuckets }, {
			:growBuckets();
			idx: if({ :keyKind == 0 }, {
				:hashString(strAddr: keyBits, nb: :nbuckets)
			}, {
				:hashBits(k: keyBits, nb: :nbuckets)
			});
		});
		local Int is e: Mem:alloc(bytes: 32);
		Mem:storeI64(ptr: e, byteOffset: 0, val: keyBits);
		Mem:storeI64(ptr: e, byteOffset: 8, val: valBits);
		Mem:storeByte(ptr: e, byteOffset: 16, val: arcByte);
		Mem:storeI64(ptr: e, byteOffset: 24, val: Mem:loadI64(ptr: :buckets, byteOffset: idx * 8));
		Mem:storeI64(ptr: :buckets, byteOffset: idx * 8, val: e);
		:len: :len + 1;
		:lock:unlock();
	}

	## Inserts or updates an entry in the map.
	##
	## @param key: Entry key.
	## @param value: Entry value.
	Function is set(K is key, V is value){
		:setEntry(key: key, value: value, valIsArc: false);
	}

	## Determines whether an entry exists for the specified key.
	##
	## @param key: Key to test.
	## @return: `true` if key is present, `false` otherwise.
	Function of Boolean is has(K is key){
		local Int is keyBits: :normKeyBits(keyBits: Mem:objToAddr(obj: key));
		if({ :keyKind == 0 && keyBits == 0 }, { return false; });
		local Boolean is isFrozen: :frozen;
		if({ !isFrozen }, { :lock:lock(); });
		local Int is idx: if({ :keyKind == 0 }, {
			:hashString(strAddr: keyBits, nb: :nbuckets)
		}, {
			:hashBits(k: keyBits, nb: :nbuckets)
		});
		local Int is curr: Mem:loadI64(ptr: :buckets, byteOffset: idx * 8);
		while({ curr != 0 }, {
			local Int is cKey: Mem:loadI64(ptr: curr, byteOffset: 0);
			local Boolean is matched: if({ :keyKind == 0 }, {
				:strKeyEquals(aAddr: cKey, bAddr: keyBits)
			}, {
				cKey == keyBits
			});
			if({ matched }, {
				if({ !isFrozen }, { :lock:unlock(); });
				return true;
			});
			curr: Mem:loadI64(ptr: curr, byteOffset: 24);
		});
		if({ !isFrozen }, { :lock:unlock(); });
		return false;
	}

	## Removes the entry associated with [key].
	##
	## @param key: Key to remove.
	## @return: `true` if removed, `false` if key was not present.
	Function of Boolean is remove(K is key){
		if({ :frozen }, {
			Mem:panic(msg: 'Mutation attempted on frozen Map');
			return false;
		});
		local Int is keyBits: :normKeyBits(keyBits: Mem:objToAddr(obj: key));
		if({ :keyKind == 0 && keyBits == 0 }, { return false; });
		:lock:lock();
		local Int is idx: if({ :keyKind == 0 }, {
			:hashString(strAddr: keyBits, nb: :nbuckets)
		}, {
			:hashBits(k: keyBits, nb: :nbuckets)
		});
		local Int is curr: Mem:loadI64(ptr: :buckets, byteOffset: idx * 8);
		local Int is prev: 0;
		while({ curr != 0 }, {
			local Int is cKey: Mem:loadI64(ptr: curr, byteOffset: 0);
			local Boolean is matched: if({ :keyKind == 0 }, {
				:strKeyEquals(aAddr: cKey, bAddr: keyBits)
			}, {
				cKey == keyBits
			});
			if({ matched }, {
				local Int is next: Mem:loadI64(ptr: curr, byteOffset: 24);
				if({ prev != 0 }, {
					Mem:storeI64(ptr: prev, byteOffset: 24, val: next);
				}, {
					Mem:storeI64(ptr: :buckets, byteOffset: idx * 8, val: next);
				});
				if({ :keyKind == 0 && cKey != 0 }, {
					Mem:releaseAddr(objAddr: cKey);
				});
				local Int is valBits: Mem:loadI64(ptr: curr, byteOffset: 8);
				local Int is isArc: Mem:loadByte(ptr: curr, byteOffset: 16);
				if({ (isArc != 0 || :valKind == 1) && valBits != 0 }, {
					Mem:releaseAddr(objAddr: valBits);
				});
				Mem:free(ptr: curr);
				:len: :len - 1;
				:lock:unlock();
				return true;
			});
			prev: curr;
			curr: Mem:loadI64(ptr: curr, byteOffset: 24);
		});
		:lock:unlock();
		return false;
	}

	## Returns an array containing all keys currently present in the map.
	##
	## @return: [Array] of keys.
	Function of Array of K is keys(){
		local Array of K is a: [];
		local Boolean is isFrozen: :frozen;
		if({ !isFrozen }, { :lock:lock(); });
		local Int is i: 0;
		while({ i < :nbuckets }, {
			local Int is curr: Mem:loadI64(ptr: :buckets, byteOffset: i * 8);
			while({ curr != 0 }, {
				local Int is kBits: Mem:loadI64(ptr: curr, byteOffset: 0);
				a:add(item: Mem:addrToObj(addr: kBits));
				curr: Mem:loadI64(ptr: curr, byteOffset: 24);
			});
			i: i + 1;
		});
		if({ !isFrozen }, { :lock:unlock(); });
		return a;
	}

	## Returns the total number of entries in the map.
	##
	## @return: Entry count.
	Function of Int is length(){
		if({ :frozen }, { return :len; });
		:lock:lock();
		local Int is n: :len;
		:lock:unlock();
		return n;
	}

	## Iterates through each key-value pair, invoking [action] with (key, value).
	##
	## @param action: Function invoked with (key, value) for each entry.
	Function is each(Function is action){
		local Array of K is ks: :keys();
		local Int is i: 0;
		while({ i < ks:length() }, {
			local K is k: ks:get(index: i);
			action(k, :getRaw(keyBits: Mem:objToAddr(obj: k), def: 0));
			i: i + 1;
		});
	}

	## Returns whether the map contains zero entries.
	##
	## @return: `true` if empty, `false` otherwise.
	Function of Boolean is isEmpty(){
		return :length() == 0;
	}

	## Returns an array containing all values in key iteration order.
	##
	## @return: [Array] of values.
	Function of Array is values(){
		local Array is out: [];
		:each(action: local Function(K is k, Any is v){
			out:add(item: v);
		});
		return out;
	}

	## Removes all entries from the map.
	Function is clear(){
		local Array of K is ks: :keys();
		ks:each(action: local Function(K is k){
			:remove(key: k);
		});
	}

	## Copies all entries from [other] into this map, overwriting matching keys.
	##
	## @param other: Source map to merge in.
	Function is merge(Map of K to V is other){
		other:each(action: local Function(K is k, V is v){
			:set(key: k, value: v);
		});
	}

	## Returns a new map containing entries for which [predicate](key, value) returns `true`.
	##
	## @param predicate: Function taking (key, value) and returning `Boolean`.
	## @return: Filtered [Map].
	Function of Map of K to V is filter(Function of Boolean is predicate){
		local Map of K to V is out: Map:init(keyKind: :keyKind, valKind: :valKind);
		:each(action: local Function(K is k, V is v){
			if({ predicate(k, v) }, {
				out:set(key: k, value: v);
			});
		});
		return out;
	}

	## Returns `true` if any entry satisfies [predicate](key, value).
	##
	## @param predicate: Function taking (key, value) and returning `Boolean`.
	## @return: `true` if any entry matches.
	Function of Boolean is any(Function of Boolean is predicate){
		local Boolean is found: false;
		:each(action: local Function(K is k, Any is v){
			if({ !found && predicate(k, v) }, {
				found: true;
			});
		});
		return found;
	}

	## Counts entries for which [predicate](key, value) returns `true`.
	##
	## @param predicate: Function taking (key, value) and returning `Boolean`.
	## @return: Count of matching entries.
	Function of Int is count(Function of Boolean is predicate){
		local Int is total: 0;
		:each(action: local Function(K is k, Any is v){
			if({ predicate(k, v) }, {
				total: total + 1;
			});
		});
		return total;
	}
}
