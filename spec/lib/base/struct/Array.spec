#! Package base:struct
#! Contiguous dynamic collections and associative hash maps.

## A dynamic, auto-resizing sequential collection of elements.
##
## Runtime-managed: instances are the runtime's
## SpecArray objects; this declaration is the API surface. In accordance
## with the "Never Null" standard, out-of-bounds queries, popping empty
## arrays, and failed searches return a caller-supplied default.

Class of Mergeable is Array of T{
	replace [String] is namespace: ['base', 'struct'];

	replace [[String]] is using: [
		['base', 'core', Mergeable],
		['base', 'struct', List],
		['base', 'sys', as Mem()],
		['base', 'sys', SpinLock],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	local Int is items: 0;
	local Int is len: 0;
	local Int is cap: 0;
	local Int is elemKind: 0;
	local Boolean is frozen: false;
	local SpinLock is lock: SpinLock:init();

	replace Function is init(Int is elemKind: 0){
		:elemKind: elemKind;
	}

	## Initializes an Array by copying all elements from a [List].
	replace Function is init(List of T is items){
		:elemKind: 0;
		:addList(other: items);
	}

	Function is destroy(){
		if({ :items != 0 }, {
			if({ :elemKind == 1 }, {
				local Int is i: 0;
				while({ i < :len }, {
					local Int is it: Mem:loadI64(ptr: :items, byteOffset: i * 8);
					if({ it != 0 }, { Mem:releaseAddr(objAddr: it); });
					i: i + 1;
				});
			});
			Mem:free(ptr: :items);
			:items: 0;
		});
	}

	local Function is notifyError(Function is error, String is msg){
		if({ Mem:hasClosure(cb: error) }, {
			error(msg);
		});
	}

	local Function of Array of T is newLike(){
		local Array of T is out: Array();
		out:elemKind: :elemKind;
		return out;
	}

	## Appends all elements of [other] into this array.
	Function is addArray(Array of T is other){
		if({ :frozen }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return;
		});
		local Int is aAddr: Mem:objToAddr(obj: :);
		local Int is oAddr: Mem:objToAddr(obj: other);
		if({ oAddr == 0 }, { return; });
		if({ aAddr == oAddr }, {
			:lock:lock();
			local Int is n: :len;
			if({ n + n > :cap }, {
				local Int is ncap: if({ :cap == 0 }, { 8 }, { :cap * 2 });
				while({ ncap < n + n }, { ncap: ncap * 2; });
				:items: Mem:realloc(ptr: :items, bytes: ncap * 8);
				:cap: ncap;
			});
			local Int is i: 0;
			while({ i < n }, {
				local Int is it: Mem:loadI64(ptr: :items, byteOffset: i * 8);
				if({ :elemKind == 1 && it != 0 }, { Mem:retainAddr(objAddr: it); });
				Mem:storeI64(ptr: :items, byteOffset: (n + i) * 8, val: it);
				i: i + 1;
			});
			:len: n + n;
			:lock:unlock();
			return;
		});
		if({ aAddr < oAddr }, {
			:lock:lock();
			other:lock:lock();
		}, {
			other:lock:lock();
			:lock:lock();
		});
		local Int is oLen: other:len;
		local Int is oItems: other:items;
		if({ :len + oLen > :cap }, {
			local Int is ncap2: if({ :cap == 0 }, { 8 }, { :cap * 2 });
			while({ ncap2 < :len + oLen }, { ncap2: ncap2 * 2; });
			:items: Mem:realloc(ptr: :items, bytes: ncap2 * 8);
			:cap: ncap2;
		});
		local Int is j: 0;
		while({ j < oLen }, {
			local Int is oit: Mem:loadI64(ptr: oItems, byteOffset: j * 8);
			if({ :elemKind == 1 && oit != 0 }, { Mem:retainAddr(objAddr: oit); });
			Mem:storeI64(ptr: :items, byteOffset: (:len + j) * 8, val: oit);
			j: j + 1;
		});
		:len: :len + oLen;
		:lock:unlock();
		other:lock:unlock();
	}

	## Appends all elements of [other] (a List) into this array.
	Function is addList(List of T is other){
		if({ :frozen }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return;
		});
		local Int is oAddr: Mem:objToAddr(obj: other);
		if({ oAddr == 0 }, { return; });
		local Int is oLen: other:length();
		if({ oLen <= 0 }, { return; });
		local Int is oData: other:rawDataAddr();
		if({ oData == 0 }, { return; });
		local Boolean is oByteMode: other:isByteMode();
		:lock:lock();
		if({ :len + oLen > :cap }, {
			local Int is ncap: if({ :cap == 0 }, { 8 }, { :cap * 2 });
			while({ ncap < :len + oLen }, { ncap: ncap * 2; });
			:items: Mem:realloc(ptr: :items, bytes: ncap * 8);
			:cap: ncap;
		});
		local Int is j: 0;
		while({ j < oLen }, {
			local Int is oit: if({ oByteMode }, {
				Mem:loadByte(ptr: oData, byteOffset: j)
			}, {
				Mem:loadI64(ptr: oData, byteOffset: j * 8)
			});
			if({ !oByteMode && :elemKind == 1 && oit != 0 }, { Mem:retainAddr(objAddr: oit); });
			Mem:storeI64(ptr: :items, byteOffset: (:len + j) * 8, val: oit);
			j: j + 1;
		});
		:len: :len + oLen;
		:lock:unlock();
	}

	## Merges all elements of [other] into this array (appending in order).
	##
	## @param other: Source array to append.
	replace Function is merge(Array of T is other){
		:addArray(other: other);
	}

	## Marks this array as frozen (immutable).
	Function is freeze(){
		:lock:lock();
		:frozen: true;
		:lock:unlock();
	}

	## Returns the number of elements contained in the array.
	##
	## @return: Element count.
	Function of Int is length(){
		if({ :frozen }, { return :len; });
		:lock:lock();
		local Int is n: :len;
		:lock:unlock();
		return n;
	}

	## Retrieves an element at the specified zero-based index (panics if out of bounds).
	##
	## @param index: Zero-based position.
	## @return: The element at [index].
	Function of T is get(Int is index){
		local Boolean is isFrozen: :frozen;
		if({ !isFrozen }, { :lock:lock(); });
		if({ index < 0 || index >= :len }, {
			local Int is curLen: :len;
			if({ !isFrozen }, { :lock:unlock(); });
			Mem:panic(msg: 'Array index out of bounds: index ' . (index as String) . ' for length ' . (curLen as String));
			return Mem:addrToObj(addr: 0);
		});
		local Int is valAddr: Mem:loadI64(ptr: :items, byteOffset: index * 8);
		if({ :elemKind == 1 && valAddr != 0 }, {
			Mem:retainAddr(objAddr: valAddr);
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		if({ !isFrozen }, { :lock:unlock(); });
		return Mem:addrToObj(addr: valAddr);
	}

	## Retrieves an element at the specified zero-based index, or [default] if out of bounds.
	##
	## @param index: Zero-based position.
	## @param default: Fallback value returned if [index] is out of bounds.
	## @return: The element, or [default].
	## @fallback: Returns [default] when index < 0 or index >= length().
	Function of T is get(Int is index, T is default){
		local Boolean is isFrozen: :frozen;
		if({ !isFrozen }, { :lock:lock(); });
		if({ index < 0 || index >= :len }, {
			if({ !isFrozen }, { :lock:unlock(); });
			return default;
		});
		local Int is valAddr: Mem:loadI64(ptr: :items, byteOffset: index * 8);
		if({ :elemKind == 1 && valAddr != 0 }, {
			Mem:retainAddr(objAddr: valAddr);
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		if({ !isFrozen }, { :lock:unlock(); });
		return Mem:addrToObj(addr: valAddr);
	}

	## Retrieves an element at the specified zero-based index, or [default] if out of bounds ([error] notified).
	##
	## @param index: Zero-based position.
	## @param default: Fallback value returned if [index] is out of bounds.
	## @param error: Callback receiving a diagnostic message on out-of-bounds access.
	## @return: The element, or [default].
	## @fallback: Returns [default] when index < 0 or index >= length().
	Function of T is get(Int is index, T is default, Function is error){
		local Boolean is isFrozen: :frozen;
		if({ !isFrozen }, { :lock:lock(); });
		if({ index < 0 || index >= :len }, {
			local Int is curLen: :len;
			if({ !isFrozen }, { :lock:unlock(); });
			:notifyError(error: error, msg: 'Array index out of bounds: index ' . (index as String) . ' for length ' . (curLen as String));
			return default;
		});
		local Int is valAddr: Mem:loadI64(ptr: :items, byteOffset: index * 8);
		if({ :elemKind == 1 && valAddr != 0 }, {
			Mem:retainAddr(objAddr: valAddr);
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		if({ !isFrozen }, { :lock:unlock(); });
		return Mem:addrToObj(addr: valAddr);
	}

	## Appends an element to this array.
	##
	## @param item: Value to append.
	Function is add(Any is item){
		if({ :frozen }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return;
		});
		:lock:lock();
		if({ :len >= :cap }, {
			local Int is ncap: if({ :cap == 0 }, { 8 }, { :cap * 2 });
			:items: Mem:realloc(ptr: :items, bytes: ncap * 8);
			:cap: ncap;
		});
		local Int is itemAddr: Mem:objToAddr(obj: item);
		if({ :elemKind == 1 && itemAddr != 0 }, {
			Mem:retainAddr(objAddr: itemAddr);
		});
		Mem:storeI64(ptr: :items, byteOffset: :len * 8, val: itemAddr);
		:len: :len + 1;
		:lock:unlock();
	}

	## Replaces the element at the specified zero-based [index] with [item].
	##
	## @param index: Zero-based position.
	## @param item: Replacement element value.
	Function is set(Int is index, T is item){
		if({ :frozen }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return;
		});
		:lock:lock();
		if({ index < 0 || index >= :len }, {
			local Int is curLen: :len;
			:lock:unlock();
			Mem:panic(msg: 'Array assignment index out of bounds: index ' . (index as String) . ' for length ' . (curLen as String));
			return;
		});
		local Int is itemAddr: Mem:objToAddr(obj: item);
		local Int is oldAddr: 0;
		if({ :elemKind == 1 }, {
			if({ itemAddr != 0 }, { Mem:retainAddr(objAddr: itemAddr); });
			oldAddr: Mem:loadI64(ptr: :items, byteOffset: index * 8);
		});
		Mem:storeI64(ptr: :items, byteOffset: index * 8, val: itemAddr);
		:lock:unlock();
		if({ :elemKind == 1 && oldAddr != 0 }, {
			Mem:releaseAddr(objAddr: oldAddr);
		});
	}

	## Removes and returns the last element in the array (panics if empty).
	Function of T is pop(){
		if({ :frozen }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return Mem:addrToObj(addr: 0);
		});
		:lock:lock();
		if({ :len == 0 }, {
			:lock:unlock();
			Mem:panic(msg: 'Array pop on empty array');
			return Mem:addrToObj(addr: 0);
		});
		:len: :len - 1;
		local Int is valAddr: Mem:loadI64(ptr: :items, byteOffset: :len * 8);
		if({ :elemKind == 1 && valAddr != 0 }, {
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		:lock:unlock();
		return Mem:addrToObj(addr: valAddr);
	}

	## Removes and returns the last element in the array, or [default] if empty.
	##
	## @param default: Fallback value returned if the array is empty.
	## @return: The removed last element, or [default].
	## @fallback: Returns [default] when the array has zero elements.
	Function of T is pop(T is default){
		if({ :frozen }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return default;
		});
		:lock:lock();
		if({ :len == 0 }, {
			:lock:unlock();
			return default;
		});
		:len: :len - 1;
		local Int is valAddr: Mem:loadI64(ptr: :items, byteOffset: :len * 8);
		if({ :elemKind == 1 && valAddr != 0 }, {
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		:lock:unlock();
		return Mem:addrToObj(addr: valAddr);
	}

	## Removes and returns the last element in the array, or [default] if empty ([error] notified).
	##
	## @param default: Fallback value returned if the array is empty.
	## @param error: Callback receiving a diagnostic message when the array is empty.
	## @return: The removed last element, or [default].
	## @fallback: Returns [default] when the array has zero elements.
	Function of T is pop(T is default, Function is error){
		if({ :frozen }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return default;
		});
		:lock:lock();
		if({ :len == 0 }, {
			:lock:unlock();
			:notifyError(error: error, msg: 'Array pop on empty array');
			return default;
		});
		:len: :len - 1;
		local Int is valAddr: Mem:loadI64(ptr: :items, byteOffset: :len * 8);
		if({ :elemKind == 1 && valAddr != 0 }, {
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		:lock:unlock();
		return Mem:addrToObj(addr: valAddr);
	}

	## Removes and returns the element at [index], panicking if out of bounds.
	Function of T is removeAt(Int is index){
		if({ :frozen }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return Mem:addrToObj(addr: 0);
		});
		:lock:lock();
		if({ index < 0 || index >= :len }, {
			local Int is curLen: :len;
			:lock:unlock();
			Mem:panic(msg: 'Array index out of bounds: index ' . (index as String) . ' for length ' . (curLen as String));
			return Mem:addrToObj(addr: 0);
		});
		local Int is valAddr: Mem:loadI64(ptr: :items, byteOffset: index * 8);
		local Int is tailCount: :len - index - 1;
		if({ tailCount > 0 }, {
			Mem:move(dst: :items + (index * 8), src: :items + ((index + 1) * 8), bytes: tailCount * 8);
		});
		:len: :len - 1;
		if({ :elemKind == 1 && valAddr != 0 }, {
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		:lock:unlock();
		return Mem:addrToObj(addr: valAddr);
	}

	## Removes and returns the element at [index], shifting trailing elements.
	##
	## @param index: Zero-based position to remove.
	## @param default: Fallback value returned if [index] is out of bounds.
	## @return: The removed element, or [default].
	## @fallback: Returns [default] when index is out of bounds.
	Function of T is removeAt(Int is index, T is default){
		if({ :frozen }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return default;
		});
		:lock:lock();
		if({ index < 0 || index >= :len }, {
			:lock:unlock();
			return default;
		});
		local Int is valAddr: Mem:loadI64(ptr: :items, byteOffset: index * 8);
		local Int is tailCount: :len - index - 1;
		if({ tailCount > 0 }, {
			Mem:move(dst: :items + (index * 8), src: :items + ((index + 1) * 8), bytes: tailCount * 8);
		});
		:len: :len - 1;
		if({ :elemKind == 1 && valAddr != 0 }, {
			Mem:claimPoolAddr(objAddr: valAddr);
		});
		:lock:unlock();
		return Mem:addrToObj(addr: valAddr);
	}

	## Returns a shallow sub-array slice from [start] (inclusive) to [end] (exclusive).
	##
	## @param start: Inclusive start index.
	## @param end: Exclusive end index.
	## @return: New sliced [Array].
	Function of Array of T is slice(Int is start, Int is end){
		local Array of T is res: :newLike();
		local Int is len: :length();
		local Int is s: match(when: [
			{ start < 0 }: { 0 },
			else:          { start }
		]);
		local Int is e: match(when: [
			{ end > len }: { len },
			else:          { end }
		]);
		local Int is i: s;
		while({ i < e }, {
			res:add(item: :get(index: i));
			i: i + 1;
		});
		return res;
	}

	## Empties the array, resetting its length to zero.
	Function is clear(){
		if({ :frozen }, {
			Mem:panic(msg: 'Mutation attempted on frozen Array');
			return;
		});
		:lock:lock();
		local Int is oldLen: :len;
		local Int is oldItems: :items;
		local Int is kind: :elemKind;
		:items: 0;
		:len: 0;
		:cap: 0;
		:lock:unlock();
		if({ oldItems != 0 }, {
			if({ kind == 1 }, {
				local Int is i: 0;
				while({ i < oldLen }, {
					local Int is elem: Mem:loadI64(ptr: oldItems, byteOffset: i * 8);
					if({ elem != 0 }, {
						Mem:releaseAddr(objAddr: elem);
					});
					i: i + 1;
				});
			});
			Mem:free(ptr: oldItems);
		});
	}

	## Searches for the first occurrence of [search], returning its index.
	##
	## @param search: String value to locate.
	## @param default: Fallback index returned if not found.
	## @return: Matching index, or [default].
	## @fallback: Returns [default] (conventionally -1) if the item is absent.
	Function of Int is indexOf(String is search, Int is default: -1){
		local Int is len: :length();
		local Int is i: 0;
		local Int is found: default;
		while({ found == default && i < len }, {
			local String is item: :get(index: i) as String;
			if({ item == search }, {
				found: i;
			});
			i: i + 1;
		});
		return found;
	}

	## Iterates through each element in the array, invoking [action] with the element.
	##
	## @param action: Function invoked for each item.
	Function is each(Function is action){
		local Int is len: :length();
		local Int is i: 0;
		while({ i < len }, {
			action(:get(index: i));
			i: i + 1;
		});
	}

	## Evaluates whether any element in the array satisfies the [predicate].
	##
	## @param predicate: Function returning `true` for a match.
	## @return: `true` if any element matches, `false` otherwise.
	Function of Boolean is any(Function of Boolean is predicate){
		local Int is len: :length();
		local Int is i: 0;
		while({ i < len }, {
			if({ predicate(:get(index: i)) }, {
				return true;
			});
			i: i + 1;
		});
		return false;
	}

	## Counts how many elements in the array satisfy the [predicate].
	##
	## @param predicate: Function returning `true` for elements to count.
	## @return: Count of matching elements.
	Function of Int is count(Function of Boolean is predicate){
		local Int is len: :length();
		local Int is total: 0;
		local Int is i: 0;
		while({ i < len }, {
			if({ predicate(:get(index: i)) }, {
				total: total + 1;
			});
			i: i + 1;
		});
		return total;
	}

	## Returns a new array containing all elements that satisfy the [predicate].
	##
	## @param predicate: Function returning `true` for elements to retain.
	## @return: Filtered [Array].
	Function of Array of T is filter(Function of Boolean is predicate){
		local Array of T is out: :newLike();
		local Int is len: :length();
		local Int is i: 0;
		while({ i < len }, {
			local T is item: :get(index: i);
			if({ predicate(item) }, {
				out:add(item: item);
			});
			i: i + 1;
		});
		return out;
	}

	## Transforms each element in the array using [transform], returning a new [Array].
	##
	## @param transform: Function mapping each item to a transformed value.
	## @return: Mapped [Array].
	Function of Array of T is map(Function is transform){
		local Array of T is out: :newLike();
		local Int is len: :length();
		local Int is i: 0;
		while({ i < len }, {
			out:add(item: transform(:get(index: i)));
			i: i + 1;
		});
		return out;
	}

	## Reduces the array to a single accumulated value starting from [initial].
	##
	## @param initial: Initial accumulator value.
	## @param accumulate: Function combining (accumulator, item) into the next accumulator.
	## @return: Final accumulated value.
	Function of Any is fold(Any is initial, Function is accumulate){
		local Any is acc: initial;
		local Int is len: :length();
		local Int is i: 0;
		while({ i < len }, {
			acc: accumulate(acc, :get(index: i));
			i: i + 1;
		});
		return acc;
	}

	## Joins all string elements of the array into one string separated by [separator].
	##
	## @param separator: Delimiter string inserted between adjacent items.
	## @return: Joined string.
	Function of String is join(String is separator){
		local Int is len: :length();
		if({ len == 0 }, {
			return '';
		});
		local String is out: '';
		local Int is i: 0;
		repeat(count: len, worker: {
			if({ i > 0 }, {
				out: out . separator;
			});
			out: out . (:get(index: i) as String);
			i: i + 1;
		});
		return out;
	}

	## Returns whether the array contains zero elements.
	##
	## @return: `true` if empty, `false` otherwise.
	Function of Boolean is isEmpty(){
		return :length() == 0;
	}

	## Returns whether [search] is present in the array.
	##
	## @param search: String value to locate.
	## @return: `true` if found, `false` otherwise.
	Function of Boolean is contains(String is search){
		return :indexOf(search: search, default: -1) >= 0;
	}

	## Returns the first element, or [default] if the array is empty.
	##
	## @param default: Fallback value returned when empty.
	## @return: First element, or [default].
	Function of T is first(T is default){
		if({ :length() == 0 }, {
			return default;
		});
		return :get(index: 0, default: default);
	}

	## Returns the last element, or [default] if the array is empty.
	##
	## @param default: Fallback value returned when empty.
	## @return: Last element, or [default].
	Function of T is last(T is default){
		local Int is len: :length();
		if({ len == 0 }, {
			return default;
		});
		return :get(index: len - 1, default: default);
	}

	## Returns a shallow copy of this array.
	##
	## @return: New [Array] with the same elements.
	Function of Array of T is copy(){
		return :slice(start: 0, end: :length());
	}

	## Returns a new array containing the elements in reverse order.
	##
	## @return: Reversed [Array].
	Function of Array of T is reverse(){
		local Array of T is out: :newLike();
		local Int is i: :length() - 1;
		while({ i >= 0 }, {
			out:add(item: :get(index: i));
			i: i - 1;
		});
		return out;
	}

	## Returns a new array containing at most the first [n] elements.
	##
	## @param n: Maximum number of leading elements to take.
	## @return: Prefix [Array].
	Function of Array of T is take(Int is n){
		if({ n <= 0 }, {
			return :newLike();
		});
		return :slice(start: 0, end: n);
	}

	## Returns a new array with the first [n] elements omitted.
	##
	## @param n: Number of leading elements to skip.
	## @return: Suffix [Array].
	Function of Array of T is drop(Int is n){
		if({ n <= 0 }, {
			return :slice(start: 0, end: :length());
		});
		return :slice(start: n, end: :length());
	}

	## Evaluates whether every element satisfies [predicate] (vacuously `true` when empty).
	##
	## @param predicate: Function returning `true` for matching elements.
	## @return: `true` if all elements match, `false` otherwise.
	Function of Boolean is all(Function of Boolean is predicate){
		local Int is len: :length();
		local Boolean is ok: true;
		local Int is i: 0;
		while({ ok && i < len }, {
			if({ !predicate(:get(index: i)) }, {
				ok: false;
			});
			i: i + 1;
		});
		return ok;
	}

	## Evaluates whether no element satisfies [predicate].
	##
	## @param predicate: Function returning `true` for matching elements.
	## @return: `true` if zero elements match, `false` otherwise.
	Function of Boolean is none(Function of Boolean is predicate){
		local Int is len: :length();
		local Boolean is ok: true;
		local Int is i: 0;
		while({ ok && i < len }, {
			if({ predicate(:get(index: i)) }, {
				ok: false;
			});
			i: i + 1;
		});
		return ok;
	}

	## Returns the first element satisfying [predicate], or [default] if none match.
	##
	## @param predicate: Function returning `true` for the target element.
	## @param default: Fallback value returned if no element matches.
	## @return: First matching element, or [default].
	Function of T is find(Function of Boolean is predicate, T is default){
		local Int is len: :length();
		local Any is found: default;
		local Boolean is hasFound: false;
		local Int is i: 0;
		while({ !hasFound && i < len }, {
			local Any is item: :get(index: i, default: default);
			if({ predicate(item) }, {
				found: item;
				hasFound: true;
			});
			i: i + 1;
		});
		return found;
	}
}
