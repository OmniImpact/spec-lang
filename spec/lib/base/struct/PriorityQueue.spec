#! Package base:struct
#! O(log n) binary heap priority queue (`PriorityQueue of T`), min-heap by default
#! or max-heap when `maxHeap: true`.

Class is PriorityQueue of T{
	replace [String] is namespace: ['base', 'struct'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Array of T is heap: Array();
	local T is zeroVal;
	local Boolean is isMax: false;

	replace Function is init(Boolean is maxHeap: false){
		:heap: Array();
		:isMax: maxHeap;
	}

	local Function of Boolean is higherPriority(T is a, T is b){
		if({ :isMax }, { return a > b; });
		return a < b;
	}

	local Function is siftUp(Int is startIdx){
		local Int is idx: startIdx;
		while({ idx > 0 }, {
			local Int is parent: (idx - 1) / 2;
			local T is curVal: :heap:get(index: idx, default: :zeroVal);
			local T is parVal: :heap:get(index: parent, default: :zeroVal);
			if({ :higherPriority(a: curVal, b: parVal) }, {
				:heap:set(index: idx, item: parVal);
				:heap:set(index: parent, item: curVal);
				idx: parent;
			}, {
				return;
			});
		});
	}

	local Function is siftDown(Int is startIdx){
		local Int is n: :heap:length();
		local Int is idx: startIdx;
		while({ true }, {
			local Int is left: idx * 2 + 1;
			local Int is right: left + 1;
			local Int is best: idx;
			if({ left < n }, {
				if({ :higherPriority(a: :heap:get(index: left, default: :zeroVal), b: :heap:get(index: best, default: :zeroVal)) }, {
					best: left;
				});
			});
			if({ right < n }, {
				if({ :higherPriority(a: :heap:get(index: right, default: :zeroVal), b: :heap:get(index: best, default: :zeroVal)) }, {
					best: right;
				});
			});
			if({ best == idx }, { return; });
			local T is tmp: :heap:get(index: idx, default: :zeroVal);
			:heap:set(index: idx, item: :heap:get(index: best, default: :zeroVal));
			:heap:set(index: best, item: tmp);
			idx: best;
		});
	}

	Function of Int is length(){ :heap:length() }

	Function of Boolean is isEmpty(){ :heap:length() == 0 }

	Function is clear(){
		:heap:clear();
	}

	## Inserts [item] into the priority queue in O(log n) time.
	Function is push(T is item){
		:heap:add(item: item);
		:siftUp(startIdx: :heap:length() - 1);
	}

	## Returns the highest-priority element without removing it, or [default] if empty.
	Function of T is peek(T is default){
		if({ :heap:length() == 0 }, { return default; });
		return :heap:get(index: 0, default: default);
	}

	## Removes and returns the highest-priority element in O(log n) time, or [default] if empty.
	Function of T is pop(T is default){
		local Int is n: :heap:length();
		if({ n == 0 }, { return default; });
		local T is top: :heap:get(index: 0, default: default);
		local T is last: :heap:pop(default: default);
		if({ :heap:length() > 0 }, {
			:heap:set(index: 0, item: last);
			:siftDown(startIdx: 0);
		});
		return top;
	}

	## Returns a copy of the underlying heap array.
	Function of Array of T is toArray(){
		return :heap:copy();
	}
}
