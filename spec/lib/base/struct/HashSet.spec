#! Package base:struct
#! Unordered O(1) hash set (`HashSet of T`) backed by a dynamically growing
#! open-chaining bucket table with ARC-safe `Array of T` storage and no fixed caps.

Class is HashSet of T{
	replace [String] is namespace: ['base', 'struct'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sys', as Mem()],
		['base', 'sys', as Introspection()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Int is buckets: 0;
	local Int is nbuckets: 0;
	local Int is nodes: 0;
	local Int is nodeCap: 0;
	local Int is allocCount: 0;
	local Int is freeHead: -1;
	local Int is len: 0;
	local Array of T is keysBuf: Array();
	local T is zeroKey;

	replace Function is init(){
		:nbuckets: 16;
		:buckets: Mem:alloc(bytes: :nbuckets * 8);
		local Int is bi: 0;
		while({ bi < :nbuckets }, {
			Mem:storeI64(ptr: :buckets, byteOffset: bi * 8, val: -1);
			bi: bi + 1;
		});
		:nodeCap: 16;
		:nodes: Mem:alloc(bytes: :nodeCap * 24);
		:allocCount: 0;
		:freeHead: -1;
		:len: 0;
		:keysBuf: Array();
	}

	Function is destroy(){
		if({ :buckets != 0 }, {
			Mem:free(ptr: :buckets);
			:buckets: 0;
		});
		if({ :nodes != 0 }, {
			Mem:free(ptr: :nodes);
			:nodes: 0;
		});
		:nbuckets: 0;
		:nodeCap: 0;
		:allocCount: 0;
		:freeHead: -1;
		:len: 0;
	}

	local Function of Int is hashItem(T is item){
		local String is ti: Introspection:typeIdentity(obj: item);
		if({ ti == 'String' || ti == 'Str' }, {
			local Int is strAddr: Mem:objToAddr(obj: item);
			if({ strAddr == 0 }, { return 0; });
			local Int is dataPtr: Mem:loadI64(ptr: strAddr, byteOffset: 0);
			local Int is sLen: Mem:loadI64(ptr: strAddr, byteOffset: 8);
			local Int is h: 5381;
			local Int is i: 0;
			while({ i < sLen }, {
				h: ((h << 5) + h) + Mem:loadByte(ptr: dataPtr, byteOffset: i);
				i: i + 1;
			});
			if({ h < 0 }, { h: 0 - h; });
			return h;
		});
		local Int is bits: Mem:objToAddr(obj: item);
		local Int is x: bits ^ (bits >> 16);
		if({ x < 0 }, { x: 0 - x; });
		return x;
	}

	local Function of Int is getNext(Int is n){
		return Mem:loadI64(ptr: :nodes, byteOffset: n * 24);
	}

	local Function is setNext(Int is n, Int is v){
		Mem:storeI64(ptr: :nodes, byteOffset: n * 24, val: v);
	}

	local Function of Int is getHash(Int is n){
		return Mem:loadI64(ptr: :nodes, byteOffset: n * 24 + 8);
	}

	local Function is setHash(Int is n, Int is h){
		Mem:storeI64(ptr: :nodes, byteOffset: n * 24 + 8, val: h);
	}

	local Function of Int is getFreeNext(Int is n){
		return Mem:loadI64(ptr: :nodes, byteOffset: n * 24 + 16);
	}

	local Function is setFreeNext(Int is n, Int is v){
		Mem:storeI64(ptr: :nodes, byteOffset: n * 24 + 16, val: v);
	}

	local Function is ensureNodeCap(Int is needed){
		if({ needed <= :nodeCap }, { return; });
		local Int is newCap: if({ :nodeCap < 16 }, { 16 }, { :nodeCap * 2 });
		while({ newCap < needed }, { newCap: newCap * 2; });
		local Int is newNodes: Mem:alloc(bytes: newCap * 24);
		if({ :nodes != 0 && :allocCount > 0 }, {
			Mem:copy(dst: newNodes, src: :nodes, bytes: :allocCount * 24);
		});
		if({ :nodes != 0 }, { Mem:free(ptr: :nodes); });
		:nodes: newNodes;
		:nodeCap: newCap;
	}

	local Function is rehash(Int is newNb){
		local Int is newBuckets: Mem:alloc(bytes: newNb * 8);
		local Int is bi: 0;
		while({ bi < newNb }, {
			Mem:storeI64(ptr: newBuckets, byteOffset: bi * 8, val: -1);
			bi: bi + 1;
		});
		bi: 0;
		while({ bi < :nbuckets }, {
			local Int is cur: Mem:loadI64(ptr: :buckets, byteOffset: bi * 8);
			while({ cur >= 0 }, {
				local Int is nxt: :getNext(n: cur);
				local Int is h: :getHash(n: cur);
				local Int is bIdx: h % newNb;
				local Int is oldHead: Mem:loadI64(ptr: newBuckets, byteOffset: bIdx * 8);
				:setNext(n: cur, v: oldHead);
				Mem:storeI64(ptr: newBuckets, byteOffset: bIdx * 8, val: cur);
				cur: nxt;
			});
			bi: bi + 1;
		});
		Mem:free(ptr: :buckets);
		:buckets: newBuckets;
		:nbuckets: newNb;
	}

	local Function of Int is allocNode(T is item, Int is h){
		local Int is idx: :freeHead;
		if({ idx >= 0 }, {
			:freeHead: :getFreeNext(n: idx);
			:keysBuf:set(index: idx, item: item);
		}, {
			idx: :allocCount;
			:ensureNodeCap(needed: idx + 1);
			:allocCount: idx + 1;
			:keysBuf:add(item: item);
		});
		:setNext(n: idx, v: -1);
		:setHash(n: idx, h: h);
		:setFreeNext(n: idx, v: -1);
		return idx;
	}

	Function of Int is length(){ :len }

	Function of Boolean is isEmpty(){ :len == 0 }

	Function is clear(){
		local Int is bi: 0;
		while({ bi < :nbuckets }, {
			Mem:storeI64(ptr: :buckets, byteOffset: bi * 8, val: -1);
			bi: bi + 1;
		});
		:keysBuf:clear();
		:allocCount: 0;
		:freeHead: -1;
		:len: 0;
	}

	## Adds [item] to the set; returns `true` if newly inserted.
	Function of Boolean is add(T is item){
		local Int is h: :hashItem(item: item);
		local Int is bIdx: h % :nbuckets;
		local Int is cur: Mem:loadI64(ptr: :buckets, byteOffset: bIdx * 8);
		while({ cur >= 0 }, {
			if({ :getHash(n: cur) == h && :keysBuf:get(index: cur, default: :zeroKey) == item }, {
				return false;
			});
			cur: :getNext(n: cur);
		});
		if({ (:len + 1) * 10 > :nbuckets * 7 }, {
			:rehash(newNb: :nbuckets * 2);
			bIdx: h % :nbuckets;
		});
		local Int is nIdx: :allocNode(item: item, h: h);
		local Int is oldHead: Mem:loadI64(ptr: :buckets, byteOffset: bIdx * 8);
		:setNext(n: nIdx, v: oldHead);
		Mem:storeI64(ptr: :buckets, byteOffset: bIdx * 8, val: nIdx);
		:len: :len + 1;
		return true;
	}

	## Returns `true` if [item] is in the set.
	Function of Boolean is has(T is item){
		local Int is h: :hashItem(item: item);
		local Int is bIdx: h % :nbuckets;
		local Int is cur: Mem:loadI64(ptr: :buckets, byteOffset: bIdx * 8);
		while({ cur >= 0 }, {
			if({ :getHash(n: cur) == h && :keysBuf:get(index: cur, default: :zeroKey) == item }, {
				return true;
			});
			cur: :getNext(n: cur);
		});
		return false;
	}

	## Removes [item] from the set; returns `true` if it was present.
	Function of Boolean is remove(T is item){
		local Int is h: :hashItem(item: item);
		local Int is bIdx: h % :nbuckets;
		local Int is cur: Mem:loadI64(ptr: :buckets, byteOffset: bIdx * 8);
		local Int is prev: -1;
		while({ cur >= 0 }, {
			if({ :getHash(n: cur) == h && :keysBuf:get(index: cur, default: :zeroKey) == item }, {
				local Int is nxt: :getNext(n: cur);
				if({ prev < 0 }, {
					Mem:storeI64(ptr: :buckets, byteOffset: bIdx * 8, val: nxt);
				}, {
					:setNext(n: prev, v: nxt);
				});
				:keysBuf:set(index: cur, item: :zeroKey);
				:setNext(n: cur, v: -1);
				:setFreeNext(n: cur, v: :freeHead);
				:freeHead: cur;
				:len: :len - 1;
				return true;
			});
			prev: cur;
			cur: :getNext(n: cur);
		});
		return false;
	}

	## Calls `action(item)` for every element in the set.
	Function is each(Function is action){
		local Int is bi: 0;
		while({ bi < :nbuckets }, {
			local Int is cur: Mem:loadI64(ptr: :buckets, byteOffset: bi * 8);
			while({ cur >= 0 }, {
				action(:keysBuf:get(index: cur, default: :zeroKey));
				cur: :getNext(n: cur);
			});
			bi: bi + 1;
		});
	}

	## Returns all elements as an Array.
	Function of Array of T is toArray(){
		local Array of T is out: Array();
		:each(action: local Function(T is item){
			out:add(item: item);
		});
		return out;
	}

	## Returns a new set containing elements in `this` or [other].
	Function of HashSet of T is union(HashSet of T is other){
		local HashSet of T is out: HashSet();
		:each(action: local Function(T is item){
			out:add(item: item);
		});
		other:each(action: local Function(T is item){
			out:add(item: item);
		});
		return out;
	}

	## Returns a new set containing elements in both `this` and [other].
	Function of HashSet of T is intersect(HashSet of T is other){
		local HashSet of T is out: HashSet();
		:each(action: local Function(T is item){
			if({ other:has(item: item) }, {
				out:add(item: item);
			});
		});
		return out;
	}

	## Returns a new set containing elements in `this` but not in [other].
	Function of HashSet of T is difference(HashSet of T is other){
		local HashSet of T is out: HashSet();
		:each(action: local Function(T is item){
			if({ !other:has(item: item) }, {
				out:add(item: item);
			});
		});
		return out;
	}
}
