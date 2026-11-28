#! Package base:struct
#! Ordered balanced set (`TreeSet of T`) backed by [TreeMap].

Class is TreeSet of T{
	replace [String] is namespace: ['base', 'struct'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'struct', TreeMap],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local TreeMap of T to Boolean is map: TreeMap();

	replace Function is init(){
		:map: TreeMap();
	}

	Function of Int is length(){ :map:length() }

	Function of Boolean is isEmpty(){ :map:isEmpty() }

	Function is clear(){
		:map:clear();
	}

	## Adds [item] to the set; returns `true` if newly inserted.
	Function of Boolean is add(T is item){
		if({ :map:has(key: item) }, { return false; });
		:map:set(key: item, value: true);
		return true;
	}

	## Returns `true` if [item] is in the set.
	Function of Boolean is has(T is item){
		return :map:has(key: item);
	}

	## Removes [item] from the set; returns `true` if it was present.
	Function of Boolean is remove(T is item){
		return :map:remove(key: item);
	}

	## Returns the smallest element in the set, or [default] if empty.
	Function of T is min(T is default){
		return :map:minKey(default: default);
	}

	## Returns the largest element in the set, or [default] if empty.
	Function of T is max(T is default){
		return :map:maxKey(default: default);
	}

	## Returns the greatest element `<= item`, or [default] if none exists.
	Function of T is floor(T is item, T is default){
		return :map:floorKey(key: item, default: default);
	}

	## Returns the smallest element `>= item`, or [default] if none exists.
	Function of T is ceiling(T is item, T is default){
		return :map:ceilingKey(key: item, default: default);
	}

	## Iterative in-order traversal calling `action(item)` in ascending order.
	Function is each(Function is action){
		:map:each(action: local Function(T is k, Boolean is _v){
			action(k);
		});
	}

	## Returns all elements in ascending sorted order.
	Function of Array of T is toArray(){
		return :map:keys();
	}

	## Returns a new set containing elements in `this` or [other].
	Function of TreeSet of T is union(TreeSet of T is other){
		local TreeSet of T is out: TreeSet();
		:each(action: local Function(T is item){
			out:add(item: item);
		});
		other:each(action: local Function(T is item){
			out:add(item: item);
		});
		return out;
	}

	## Returns a new set containing elements in both `this` and [other].
	Function of TreeSet of T is intersect(TreeSet of T is other){
		local TreeSet of T is out: TreeSet();
		:each(action: local Function(T is item){
			if({ other:has(item: item) }, {
				out:add(item: item);
			});
		});
		return out;
	}

	## Returns a new set containing elements in `this` but not in [other].
	Function of TreeSet of T is difference(TreeSet of T is other){
		local TreeSet of T is out: TreeSet();
		:each(action: local Function(T is item){
			if({ !other:has(item: item) }, {
				out:add(item: item);
			});
		});
		return out;
	}
}
