#! Package base:sysinternal
#! The pointer-vector floor: primitive operations on managed vectors.
##
## Body-less, interface-style declarations bound to the runtime's C floor.
## The namespace IS the binding annotation: every method compiles to
## spec_<snake_case(method)> per the floor naming convention. These are the
## ONLY methods in the system allowed to touch C; all other classes reach
## the floor through this class. Ownership follows the standard claim/retain
## conventions.

Class is Vector{
	namespace: ['base', 'sysinternal'];

	## Number of elements held by vector [v].
	##
	## @param v: The vector.
	## @return: Element count.
	Function of Int is vecLength(Any is v);

	## Item at [idx] in vector [v], or [def] when out of bounds.
	##
	## @param v: The vector.
	## @param idx: Zero-based element index.
	## @param def: Fallback when [idx] is out of bounds.
	## @return: The element, or [def].
	Function of Any is vecGetAt(Any is v, Int is idx, Any is def);

	## Overwrites item at [idx] in vector [v].
	##
	## @param v: The vector.
	## @param idx: Zero-based element index.
	## @param item: The replacement value.
	Function is vecSetAt(Any is v, Int is idx, Any is item);

	## Appends [item] to vector [v].
	##
	## @param v: The vector.
	## @param item: Value to append.
	Function is vecAdd(Any is v, Any is item);

	## Removes and returns the last element of [v], or [def] when empty.
	##
	## @param v: The vector.
	## @param def: Fallback when [v] is empty.
	## @return: The removed last element, or [def].
	Function of Any is vecPopLast(Any is v, Any is def);

	## Removes and returns the element at [idx] from [v], shifting trailing elements.
	##
	## @param v: The vector.
	## @param idx: Zero-based index to remove.
	## @param def: Fallback when [idx] is out of bounds.
	## @return: The removed element, or [def].
	Function of Any is vecRemoveAt(Any is v, Int is idx, Any is def);

	## Removes all elements from vector [v].
	##
	## @param v: The vector.
	Function is vecClear(Any is v);
}
