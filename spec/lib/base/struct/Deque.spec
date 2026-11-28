#! Package base:struct
#! O(1) amortized ring-buffer double-ended queue (`Deque of T`) with dynamic
#! growth and no fixed capacity caps.

Class is Deque of T{
	replace [String] is namespace: ['base', 'struct'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Array of T is buf: Array();
	local T is zeroVal;
	local Int is cap: 0;
	local Int is head: 0;
	local Int is count: 0;

	replace Function is init(){
		:buf: Array();
		:cap: 0;
		:head: 0;
		:count: 0;
	}

	local Function is grow(){
		local Int is newCap: if({ :cap < 16 }, { 16 }, { :cap * 2 });
		local Array of T is next: Array();
		local Int is i: 0;
		while({ i < :count }, {
			local Int is idx: (:head + i) % :cap;
			next:add(item: :buf:get(index: idx, default: :zeroVal));
			i: i + 1;
		});
		while({ i < newCap }, {
			next:add(item: :zeroVal);
			i: i + 1;
		});
		:buf: next;
		:cap: newCap;
		:head: 0;
	}

	Function of Int is length(){ :count }

	Function of Boolean is isEmpty(){ :count == 0 }

	Function is clear(){
		local Int is i: 0;
		while({ i < :count }, {
			local Int is idx: (:head + i) % :cap;
			:buf:set(index: idx, item: :zeroVal);
			i: i + 1;
		});
		:head: 0;
		:count: 0;
	}

	## Appends [item] to the back of the deque in O(1) amortized time.
	Function is pushBack(T is item){
		if({ :count >= :cap }, { :grow(); });
		local Int is tail: (:head + :count) % :cap;
		:buf:set(index: tail, item: item);
		:count: :count + 1;
	}

	## Prepends [item] to the front of the deque in O(1) amortized time.
	Function is pushFront(T is item){
		if({ :count >= :cap }, { :grow(); });
		:head: (:head - 1 + :cap) % :cap;
		:buf:set(index: :head, item: item);
		:count: :count + 1;
	}

	## Removes and returns the front element, or [default] if empty.
	Function of T is popFront(T is default){
		if({ :count == 0 }, { return default; });
		local T is val: :buf:get(index: :head, default: default);
		:buf:set(index: :head, item: :zeroVal);
		:head: (:head + 1) % :cap;
		:count: :count - 1;
		return val;
	}

	## Removes and returns the back element, or [default] if empty.
	Function of T is popBack(T is default){
		if({ :count == 0 }, { return default; });
		local Int is tail: (:head + :count - 1) % :cap;
		local T is val: :buf:get(index: tail, default: default);
		:buf:set(index: tail, item: :zeroVal);
		:count: :count - 1;
		return val;
	}

	## Returns the front element without removing it, or [default] if empty.
	Function of T is peekFront(T is default){
		if({ :count == 0 }, { return default; });
		return :buf:get(index: :head, default: default);
	}

	## Returns the back element without removing it, or [default] if empty.
	Function of T is peekBack(T is default){
		if({ :count == 0 }, { return default; });
		local Int is tail: (:head + :count - 1) % :cap;
		return :buf:get(index: tail, default: default);
	}

	## Returns the element at logical index [index] (`0..length()-1`), or [default].
	Function of T is get(Int is index, T is default){
		if({ index < 0 || index >= :count }, { return default; });
		return :buf:get(index: (:head + index) % :cap, default: default);
	}

	## Calls `action(item)` from front to back.
	Function is each(Function is action){
		local Int is i: 0;
		while({ i < :count }, {
			action(:buf:get(index: (:head + i) % :cap, default: :zeroVal));
			i: i + 1;
		});
	}

	## Returns all elements from front to back as an Array.
	Function of Array of T is toArray(){
		local Array of T is out: Array();
		local Int is i: 0;
		while({ i < :count }, {
			out:add(item: :buf:get(index: (:head + i) % :cap, default: :zeroVal));
			i: i + 1;
		});
		return out;
	}
}
