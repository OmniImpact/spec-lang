#! Package base:struct
#! Ordered balanced Red-Black map (`TreeMap of K to V`) backed by a flat,
#! dynamically growing node pool with iterative traversals and no fixed caps.

Class is TreeMap of K to V{
	replace [String] is namespace: ['base', 'struct'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Int is nodes: 0;
	local Int is cap: 0;
	local Int is allocCount: 0;
	local Int is freeHead: -1;
	local Int is root: -1;
	local Int is len: 0;
	local Array of K is keysBuf: Array();
	local Array of V is valsBuf: Array();
	local K is zeroKey;
	local V is zeroVal;

	replace Function is init(){
		:cap: 16;
		:nodes: Mem:alloc(bytes: :cap * 40);
		:allocCount: 0;
		:freeHead: -1;
		:root: -1;
		:len: 0;
		:keysBuf: Array();
		:valsBuf: Array();
	}

	Function is destroy(){
		if({ :nodes != 0 }, {
			Mem:free(ptr: :nodes);
			:nodes: 0;
		});
		:cap: 0;
		:allocCount: 0;
		:freeHead: -1;
		:root: -1;
		:len: 0;
	}

	local Function of Int is getLeft(Int is n){
		if({ n < 0 }, { return -1; });
		return Mem:loadI64(ptr: :nodes, byteOffset: n * 40);
	}

	local Function is setLeft(Int is n, Int is v){
		if({ n >= 0 }, { Mem:storeI64(ptr: :nodes, byteOffset: n * 40, val: v); });
	}

	local Function of Int is getRight(Int is n){
		if({ n < 0 }, { return -1; });
		return Mem:loadI64(ptr: :nodes, byteOffset: n * 40 + 8);
	}

	local Function is setRight(Int is n, Int is v){
		if({ n >= 0 }, { Mem:storeI64(ptr: :nodes, byteOffset: n * 40 + 8, val: v); });
	}

	local Function of Int is getParent(Int is n){
		if({ n < 0 }, { return -1; });
		return Mem:loadI64(ptr: :nodes, byteOffset: n * 40 + 16);
	}

	local Function is setParent(Int is n, Int is v){
		if({ n >= 0 }, { Mem:storeI64(ptr: :nodes, byteOffset: n * 40 + 16, val: v); });
	}

	local Function of Int is getColor(Int is n){
		if({ n < 0 }, { return 0; });
		return Mem:loadI64(ptr: :nodes, byteOffset: n * 40 + 24);
	}

	local Function is setColor(Int is n, Int is c){
		if({ n >= 0 }, { Mem:storeI64(ptr: :nodes, byteOffset: n * 40 + 24, val: c); });
	}

	local Function of Int is getFreeNext(Int is n){
		return Mem:loadI64(ptr: :nodes, byteOffset: n * 40 + 32);
	}

	local Function is setFreeNext(Int is n, Int is v){
		Mem:storeI64(ptr: :nodes, byteOffset: n * 40 + 32, val: v);
	}

	local Function is ensureCapacity(Int is needed){
		if({ needed <= :cap }, { return; });
		local Int is newCap: if({ :cap < 16 }, { 16 }, { :cap * 2 });
		while({ newCap < needed }, {
			newCap: newCap * 2;
		});
		local Int is newNodes: Mem:alloc(bytes: newCap * 40);
		if({ :nodes != 0 && :allocCount > 0 }, {
			Mem:copy(dst: newNodes, src: :nodes, bytes: :allocCount * 40);
		});
		if({ :nodes != 0 }, {
			Mem:free(ptr: :nodes);
		});
		:nodes: newNodes;
		:cap: newCap;
	}

	local Function of Int is allocNode(K is key, V is val){
		local Int is idx: :freeHead;
		if({ idx >= 0 }, {
			:freeHead: :getFreeNext(n: idx);
			:keysBuf:set(index: idx, item: key);
			:valsBuf:set(index: idx, item: val);
		}, {
			idx: :allocCount;
			:ensureCapacity(needed: idx + 1);
			:allocCount: idx + 1;
			:keysBuf:add(item: key);
			:valsBuf:add(item: val);
		});
		:setLeft(n: idx, v: -1);
		:setRight(n: idx, v: -1);
		:setParent(n: idx, v: -1);
		:setColor(n: idx, c: 1);
		:setFreeNext(n: idx, v: -1);
		return idx;
	}

	local Function is freeNode(Int is idx){
		if({ idx < 0 }, { return; });
		:keysBuf:set(index: idx, item: :zeroKey);
		:valsBuf:set(index: idx, item: :zeroVal);
		:setLeft(n: idx, v: -1);
		:setRight(n: idx, v: -1);
		:setParent(n: idx, v: -1);
		:setColor(n: idx, c: 0);
		:setFreeNext(n: idx, v: :freeHead);
		:freeHead: idx;
	}

	local Function is rotateLeft(Int is x){
		local Int is y: :getRight(n: x);
		if({ y < 0 }, { return; });
		local Int is yl: :getLeft(n: y);
		:setRight(n: x, v: yl);
		if({ yl >= 0 }, { :setParent(n: yl, v: x); });
		local Int is xp: :getParent(n: x);
		:setParent(n: y, v: xp);
		if({ xp < 0 }, {
			:root: y;
		}, {
			if({ x == :getLeft(n: xp) }, {
				:setLeft(n: xp, v: y);
			}, {
				:setRight(n: xp, v: y);
			});
		});
		:setLeft(n: y, v: x);
		:setParent(n: x, v: y);
	}

	local Function is rotateRight(Int is x){
		local Int is y: :getLeft(n: x);
		if({ y < 0 }, { return; });
		local Int is yr: :getRight(n: y);
		:setLeft(n: x, v: yr);
		if({ yr >= 0 }, { :setParent(n: yr, v: x); });
		local Int is xp: :getParent(n: x);
		:setParent(n: y, v: xp);
		if({ xp < 0 }, {
			:root: y;
		}, {
			if({ x == :getRight(n: xp) }, {
				:setRight(n: xp, v: y);
			}, {
				:setLeft(n: xp, v: y);
			});
		});
		:setRight(n: y, v: x);
		:setParent(n: x, v: y);
	}

	local Function is fixInsert(Int is z){
		local Int is cur: z;
		local Boolean is running: true;
		while({ running && cur != :root && :getColor(n: :getParent(n: cur)) == 1 }, {
			local Int is p: :getParent(n: cur);
			local Int is gp: :getParent(n: p);
			if({ gp < 0 }, {
				:setColor(n: p, c: 0);
				running: false;
			}, {
				if({ p == :getLeft(n: gp) }, {
					local Int is u: :getRight(n: gp);
					if({ :getColor(n: u) == 1 }, {
						:setColor(n: p, c: 0);
						:setColor(n: u, c: 0);
						:setColor(n: gp, c: 1);
						cur: gp;
					}, {
						if({ cur == :getRight(n: p) }, {
							cur: p;
							:rotateLeft(x: cur);
							p: :getParent(n: cur);
							gp: :getParent(n: p);
						});
						:setColor(n: p, c: 0);
						:setColor(n: gp, c: 1);
						:rotateRight(x: gp);
					});
				}, {
					local Int is u2: :getLeft(n: gp);
					if({ :getColor(n: u2) == 1 }, {
						:setColor(n: p, c: 0);
						:setColor(n: u2, c: 0);
						:setColor(n: gp, c: 1);
						cur: gp;
					}, {
						if({ cur == :getLeft(n: p) }, {
							cur: p;
							:rotateRight(x: cur);
							p: :getParent(n: cur);
							gp: :getParent(n: p);
						});
						:setColor(n: p, c: 0);
						:setColor(n: gp, c: 1);
						:rotateLeft(x: gp);
					});
				});
			});
		});
		if({ :root >= 0 }, { :setColor(n: :root, c: 0); });
	}

	local Function is transplant(Int is u, Int is v){
		local Int is up: :getParent(n: u);
		if({ up < 0 }, {
			:root: v;
		}, {
			if({ u == :getLeft(n: up) }, {
				:setLeft(n: up, v: v);
			}, {
				:setRight(n: up, v: v);
			});
		});
		if({ v >= 0 }, {
			:setParent(n: v, v: up);
		});
	}

	local Function of Int is minSubtree(Int is n){
		local Int is cur: n;
		while({ cur >= 0 && :getLeft(n: cur) >= 0 }, {
			cur: :getLeft(n: cur);
		});
		return cur;
	}

	local Function is fixDelete(Int is xStart, Int is pStart){
		local Int is x: xStart;
		local Int is p: pStart;
		local Boolean is running: true;
		while({ running && x != :root && :getColor(n: x) == 0 }, {
			if({ x >= 0 }, { p: :getParent(n: x); });
			if({ p < 0 }, {
				running: false;
			}, {
				if({ x == :getLeft(n: p) }, {
					local Int is w: :getRight(n: p);
					if({ :getColor(n: w) == 1 }, {
						:setColor(n: w, c: 0);
						:setColor(n: p, c: 1);
						:rotateLeft(x: p);
						w: :getRight(n: p);
					});
					if({ w < 0 }, {
						x: p;
						p: :getParent(n: x);
					}, {
						if({ :getColor(n: :getLeft(n: w)) == 0 && :getColor(n: :getRight(n: w)) == 0 }, {
							:setColor(n: w, c: 1);
							x: p;
							p: :getParent(n: x);
						}, {
							if({ :getColor(n: :getRight(n: w)) == 0 }, {
								:setColor(n: :getLeft(n: w), c: 0);
								:setColor(n: w, c: 1);
								:rotateRight(x: w);
								w: :getRight(n: p);
							});
							:setColor(n: w, c: :getColor(n: p));
							:setColor(n: p, c: 0);
							:setColor(n: :getRight(n: w), c: 0);
							:rotateLeft(x: p);
							x: :root;
						});
					});
				}, {
					local Int is w2: :getLeft(n: p);
					if({ :getColor(n: w2) == 1 }, {
						:setColor(n: w2, c: 0);
						:setColor(n: p, c: 1);
						:rotateRight(x: p);
						w2: :getLeft(n: p);
					});
					if({ w2 < 0 }, {
						x: p;
						p: :getParent(n: x);
					}, {
						if({ :getColor(n: :getRight(n: w2)) == 0 && :getColor(n: :getLeft(n: w2)) == 0 }, {
							:setColor(n: w2, c: 1);
							x: p;
							p: :getParent(n: x);
						}, {
							if({ :getLeft(n: w2) < 0 || :getColor(n: :getLeft(n: w2)) == 0 }, {
								:setColor(n: :getRight(n: w2), c: 0);
								:setColor(n: w2, c: 1);
								:rotateLeft(x: w2);
								w2: :getLeft(n: p);
							});
							:setColor(n: w2, c: :getColor(n: p));
							:setColor(n: p, c: 0);
							:setColor(n: :getLeft(n: w2), c: 0);
							:rotateRight(x: p);
							x: :root;
						});
					});
				});
			});
		});
		if({ x >= 0 }, { :setColor(n: x, c: 0); });
	}

	local Function of Int is findNode(K is key){
		local Int is cur: :root;
		while({ cur >= 0 }, {
			local K is ck: :keysBuf:get(index: cur, default: :zeroKey);
			if({ key < ck }, {
				cur: :getLeft(n: cur);
			}, {
				if({ key > ck }, {
					cur: :getRight(n: cur);
				}, {
					return cur;
				});
			});
		});
		return -1;
	}

	Function of Int is length(){ :len }

	Function of Boolean is isEmpty(){ :len == 0 }

	Function is clear(){
		:keysBuf:clear();
		:valsBuf:clear();
		:allocCount: 0;
		:freeHead: -1;
		:root: -1;
		:len: 0;
	}

	## Inserts or updates [key] -> [value].
	Function is set(K is key, V is value){
		if({ :root < 0 }, {
			local Int is r: :allocNode(key: key, val: value);
			:setColor(n: r, c: 0);
			:root: r;
			:len: 1;
			return;
		});
		local Int is cur: :root;
		local Int is parent: -1;
		local Boolean is goLeft: false;
		while({ cur >= 0 }, {
			parent: cur;
			local K is ck: :keysBuf:get(index: cur, default: :zeroKey);
			if({ key < ck }, {
				goLeft: true;
				cur: :getLeft(n: cur);
			}, {
				if({ key > ck }, {
					goLeft: false;
					cur: :getRight(n: cur);
				}, {
					:valsBuf:set(index: cur, item: value);
					return;
				});
			});
		});
		local Int is n: :allocNode(key: key, val: value);
		:setParent(n: n, v: parent);
		if({ goLeft }, {
			:setLeft(n: parent, v: n);
		}, {
			:setRight(n: parent, v: n);
		});
		:len: :len + 1;
		:fixInsert(z: n);
	}

	## Returns the value for [key], or [default] if not present.
	Function of V is get(K is key, V is default){
		local Int is idx: :findNode(key: key);
		if({ idx < 0 }, { return default; });
		return :valsBuf:get(index: idx, default: default);
	}

	## Returns `true` if [key] is present in the map.
	Function of Boolean is has(K is key){
		return :findNode(key: key) >= 0;
	}

	## Removes [key] if present; returns `true` if a key was removed.
	Function of Boolean is remove(K is key){
		local Int is z: :findNode(key: key);
		if({ z < 0 }, { return false; });
		local Int is y: z;
		local Int is yOrigColor: :getColor(n: y);
		local Int is x: -1;
		local Int is xParent: -1;
		if({ :getLeft(n: z) < 0 }, {
			x: :getRight(n: z);
			xParent: :getParent(n: z);
			:transplant(u: z, v: x);
		}, {
			if({ :getRight(n: z) < 0 }, {
				x: :getLeft(n: z);
				xParent: :getParent(n: z);
				:transplant(u: z, v: x);
			}, {
				y: :minSubtree(n: :getRight(n: z));
				yOrigColor: :getColor(n: y);
				x: :getRight(n: y);
				if({ :getParent(n: y) == z }, {
					xParent: y;
					if({ x >= 0 }, { :setParent(n: x, v: y); });
				}, {
					xParent: :getParent(n: y);
					:transplant(u: y, v: x);
					:setRight(n: y, v: :getRight(n: z));
					:setParent(n: :getRight(n: y), v: y);
				});
				:transplant(u: z, v: y);
				:setLeft(n: y, v: :getLeft(n: z));
				:setParent(n: :getLeft(n: y), v: y);
				:setColor(n: y, c: :getColor(n: z));
			});
		});
		:freeNode(idx: z);
		:len: :len - 1;
		if({ yOrigColor == 0 }, {
			:fixDelete(xStart: x, pStart: xParent);
		});
		return true;
	}

	## Returns the smallest key in the map, or [default] if empty.
	Function of K is minKey(K is default){
		local Int is m: :minSubtree(n: :root);
		if({ m < 0 }, { return default; });
		return :keysBuf:get(index: m, default: default);
	}

	## Returns the largest key in the map, or [default] if empty.
	Function of K is maxKey(K is default){
		local Int is cur: :root;
		if({ cur < 0 }, { return default; });
		while({ :getRight(n: cur) >= 0 }, {
			cur: :getRight(n: cur);
		});
		return :keysBuf:get(index: cur, default: default);
	}

	## Returns the greatest key `<= key`, or [default] if none exists.
	Function of K is floorKey(K is key, K is default){
		local Int is cur: :root;
		local Int is best: -1;
		while({ cur >= 0 }, {
			local K is ck: :keysBuf:get(index: cur, default: :zeroKey);
			if({ key == ck }, { return ck; });
			if({ key < ck }, {
				cur: :getLeft(n: cur);
			}, {
				best: cur;
				cur: :getRight(n: cur);
			});
		});
		if({ best < 0 }, { return default; });
		return :keysBuf:get(index: best, default: default);
	}

	## Returns the smallest key `>= key`, or [default] if none exists.
	Function of K is ceilingKey(K is key, K is default){
		local Int is cur: :root;
		local Int is best: -1;
		while({ cur >= 0 }, {
			local K is ck: :keysBuf:get(index: cur, default: :zeroKey);
			if({ key == ck }, { return ck; });
			if({ key > ck }, {
				cur: :getRight(n: cur);
			}, {
				best: cur;
				cur: :getLeft(n: cur);
			});
		});
		if({ best < 0 }, { return default; });
		return :keysBuf:get(index: best, default: default);
	}

	## Iterative in-order traversal calling `action(key, value)` in ascending key order.
	Function is each(Function is action){
		local Array of Int is stack: Array();
		local Int is cur: :root;
		while({ cur >= 0 || stack:length() > 0 }, {
			while({ cur >= 0 }, {
				stack:add(item: cur);
				cur: :getLeft(n: cur);
			});
			local Int is node: stack:pop(default: -1);
			if({ node >= 0 }, {
				action(:keysBuf:get(index: node, default: :zeroKey), :valsBuf:get(index: node, default: :zeroVal));
				cur: :getRight(n: node);
			});
		});
	}

	## Returns all keys in ascending sorted order.
	Function of Array of K is keys(){
		local Array of K is out: Array();
		:each(action: local Function(K is k, V is _v){
			out:add(item: k);
		});
		return out;
	}

	## Returns all values ordered by ascending key.
	Function of Array of V is values(){
		local Array of V is out: Array();
		:each(action: local Function(K is _k, V is v){
			out:add(item: v);
		});
		return out;
	}
}
