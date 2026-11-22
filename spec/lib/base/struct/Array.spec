#! Package base:struct
#! Contiguous dynamic collections and associative hash maps.

## A dynamic, auto-resizing sequential collection of elements.
##
## Runtime-managed: instances are the runtime's
## SpecArray objects; this declaration is the API surface. In accordance
## with the "Never Null" standard, out-of-bounds queries, popping empty
## arrays, and failed searches return a caller-supplied default.

Class is Array of T{
	namespace: ['base', 'struct'];

	replace Array of Array of String is using: [
		['base', 'sys', as Vector()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	## Returns the number of elements contained in the array.
	##
	## @return: Element count.
	Function of Int is length(){
		return Vector:vecLength(v: :);
	}

	## Retrieves an element at the specified zero-based index (panics if out of bounds).
	##
	## @param index: Zero-based position.
	## @return: The element at [index].
	Function of T is get(Int is index){
		return Vector:vecGetChecked(v: :, idx: index);
	}

	## Retrieves an element at the specified zero-based index.
	##
	## @param index: Zero-based position.
	## @param default: Fallback value returned if [index] is out of bounds.
	## @return: The element, or [default].
	## @fallback: Returns [default] when index < 0 or index >= length().
	Function of T is get(Int is index, T is default){
		return Vector:vecGetAt(v: :, idx: index, def: default);
	}

	## Appends an element to this array.
	##
	## @param item: Value to append.
	Function is add(Any is item){
		Vector:vecAdd(v: :, item: item);
	}

	## Replaces the element at the specified zero-based [index] with [item].
	##
	## @param index: Zero-based position.
	## @param item: Replacement element value.
	Function is set(Int is index, T is item){
		Vector:vecSetAt(v: :, idx: index, item: item);
	}

	## Removes and returns the last element in the array (panics if empty).
	Function of T is pop(){
		return Vector:vecPopChecked(v: :);
	}

	## Removes and returns the last element in the array.
	##
	## @param default: Fallback value returned if the array is empty.
	## @return: The removed last element, or [default].
	## @fallback: Returns [default] when the array has zero elements.
	Function of T is pop(T is default){
		return Vector:vecPopLast(v: :, def: default);
	}

	## Removes and returns the element at [index], panicking if out of bounds.
	Function of T is removeAt(Int is index){
		return Vector:vecRemoveAtChecked(v: :, idx: index);
	}

	## Removes and returns the element at [index], shifting trailing elements.
	##
	## @param index: Zero-based position to remove.
	## @param default: Fallback value returned if [index] is out of bounds.
	## @return: The removed element, or [default].
	## @fallback: Returns [default] when index is out of bounds.
	Function of T is removeAt(Int is index, T is default){
		return Vector:vecRemoveAt(v: :, idx: index, def: default);
	}

	## Returns a shallow sub-array slice from [start] (inclusive) to [end] (exclusive).
	##
	## @param start: Inclusive start index.
	## @param end: Exclusive end index.
	## @return: New sliced [Array].
	Function of Array of T is slice(Int is start, Int is end){
		local Array of T is res: Vector:newVecLike(v: :);
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
		Vector:vecClear(v: :);
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
		local Array of T is out: Vector:newVecLike(v: :);
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
		local Array of T is out: Vector:newVecLike(v: :);
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
		local Array of T is out: Vector:newVecLike(v: :);
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
			return Vector:newVecLike(v: :);
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
