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
		return Vector:vecLength(v: self);
	}

	## Retrieves an element at the specified zero-based index.
	##
	## @param index: Zero-based position.
	## @param default: Fallback value returned if [index] is out of bounds.
	## @return: The element, or [default].
	## @fallback: Returns [default] when index < 0 or index >= length().
	Function of T is get(Int is index, Any is default){
		return Vector:vecGetAt(v: self, idx: index, def: default);
	}

	## Appends an element or merges another array into this array.
	##
	## @param item: Value or [Array] to append.
	Function is add(Any is item){
		Vector:vecAdd(v: self, item: item);
	}

	## Replaces the element at the specified zero-based [index] with [item].
	##
	## @param index: Zero-based position.
	## @param item: Replacement element value.
	Function is set(Int is index, Any is item){
		Vector:vecSetAt(v: self, idx: index, item: item);
	}

	## Removes and returns the last element in the array.
	##
	## @param default: Fallback value returned if the array is empty.
	## @return: The removed last element, or [default].
	## @fallback: Returns [default] when the array has zero elements.
	Function of T is pop(Any is default){
		return Vector:vecPopLast(v: self, def: default);
	}

	## Removes and returns the element at [index], shifting trailing elements.
	##
	## @param index: Zero-based position to remove.
	## @param default: Fallback value returned if [index] is out of bounds.
	## @return: The removed element, or [default].
	## @fallback: Returns [default] when index is out of bounds.
	Function of T is removeAt(Int is index, Any is default){
		return Vector:vecRemoveAt(v: self, idx: index, def: default);
	}

	## Returns a shallow sub-array slice from [start] (inclusive) to [end] (exclusive).
	##
	## @param start: Inclusive start index.
	## @param end: Exclusive end index.
	## @return: New sliced [Array].
	Function of Array of T is slice(Int is start, Int is end){
		local Array of T is res: [];
		local Int is len: self:length();
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
			res:add(item: self:get(index: i, default: ''));
			i: i + 1;
		});
		return res;
	}

	## Empties the array, resetting its length to zero.
	Function is clear(){
		Vector:vecClear(v: self);
	}

	## Searches for the first occurrence of [search], returning its index.
	##
	## @param search: String value to locate.
	## @param default: Fallback index returned if not found.
	## @return: Matching index, or [default].
	## @fallback: Returns [default] (conventionally -1) if the item is absent.
	Function of Int is indexOf(String is search, Int is default: -1){
		local Int is len: self:length();
		local Int is i: 0;
		local Int is found: default;
		while({ found == default && i < len }, {
			local String is item: self:get(index: i, default: '') as String;
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
	}

	## Evaluates whether any element in the array satisfies the [predicate].
	##
	## @param predicate: Function returning `true` for a match.
	## @return: `true` if any element matches, `false` otherwise.
	Function of Boolean is any(Function is predicate){
	}

	## Counts how many elements in the array satisfy the [predicate].
	##
	## @param predicate: Function returning `true` for elements to count.
	## @return: Count of matching elements.
	Function of Int is count(Function is predicate){
	}

	## Returns a new array containing all elements that satisfy the [predicate].
	##
	## @param predicate: Function returning `true` for elements to retain.
	## @return: Filtered [Array].
	Function of Array of T is filter(Function is predicate){
	}

	## Transforms each element in the array using [transform], returning a new [Array].
	##
	## @param transform: Function mapping each item to a transformed value.
	## @return: Mapped [Array].
	Function of Array of T is map(Function is transform){
	}

	## Reduces the array to a single accumulated value starting from [initial].
	##
	## @param initial: Initial accumulator value.
	## @param accumulate: Function combining (accumulator, item) into the next accumulator.
	## @return: Final accumulated value.
	Function of Any is fold(Any is initial, Function is accumulate){
	}

	## Joins all string elements of the array into one string separated by [separator].
	##
	## @param separator: Delimiter string inserted between adjacent items.
	## @return: Joined string.
	Function of String is join(String is separator){
		local Int is len: self:length();
		if({ len == 0 }, {
			return '';
		});
		local String is out: '';
		local Int is i: 0;
		repeat(count: len, worker: {
			if({ i > 0 }, {
				out: out . separator;
			});
			out: out . (self:get(index: i, default: '') as String);
			i: i + 1;
		});
		return out;
	}

	## Returns whether the array contains zero elements.
	##
	## @return: `true` if empty, `false` otherwise.
	Function of Boolean is isEmpty(){
		return self:length() == 0;
	}
}
