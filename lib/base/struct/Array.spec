#! Package base:struct
#! Provides contiguous dynamic collections and associative hash maps.

## A dynamic, auto-resizing sequential collection of elements.
##
## In accordance with the "Never Null" standard, out-of-bounds queries,
## popping empty arrays, or failed searches return a caller-supplied default.
class Array{

	## Returns the number of elements contained in the array.
	##
	## @return: Element count integer.
	replace Function of Int is length(){
	}

	## Retrieves an element at the specified zero-based index.
	##
	## @param index: Zero-based position.
	## @param default: Fallback value returned if [index] is out of bounds.
	## @return: The element, or [default].
	## @fallback: Returns [default] when index < 0 or index >= length().
	replace Function of Any is get(Int is index, Any is default){
	}

	## Appends an element or merges another array into this array.
	##
	## @param item: Value or [Array] to append.
	replace Function is add(Any is item){
	}

	## Removes and returns the last element in the array.
	##
	## @param default: Fallback value returned if the array is empty.
	## @return: The removed last element, or [default].
	## @fallback: Returns [default] when the array has zero elements.
	replace Function of Any is pop(Any is default){
	}

	## Removes and returns the element at the specified index, shifting trailing elements.
	##
	## @param index: Zero-based position to remove.
	## @param default: Fallback value returned if [index] is out of bounds.
	## @return: The removed element, or [default].
	## @fallback: Returns [default] when index is out of bounds.
	replace Function of Any is removeAt(Int is index, Any is default){
	}

	## Returns a shallow sub-array slice from [start] (inclusive) to [end] (exclusive).
	##
	## @param start: Inclusive start index.
	## @param end: Exclusive end index.
	## @return: New sliced [Array].
	replace Function of Array is slice(Int is start, Int is end){
	}

	## Empties the array, resetting its length to zero.
	replace Function is clear(){
	}

	## Searches for the first occurrence of [search], returning its zero-based index.
	##
	## @param search: String value to locate.
	## @param default: Fallback index returned if not found.
	## @return: Matching index, or [default].
	## @fallback: Returns [default] (conventionally -1) if item is absent.
	replace Function of Int is indexOf(String is search, Int is default){
	}

	## Returns whether the array contains zero elements.
	##
	## @return: `true` if empty, `false` otherwise.
	Function of Boolean is isEmpty(){
		return self:length() == 0;
	}

}
