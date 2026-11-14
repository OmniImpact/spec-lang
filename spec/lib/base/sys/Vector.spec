#! Package base:sys
#! Public wrapper over the sysinternal pointer-vector floor.
##
## The ONLY classes allowed to call base:sysinternal are the same-name
## wrappers in base:sys (enforced by the checker). Wrapper bodies address
## the floor by its full qualified chain; everything outside this package
## addresses the floor through these public methods. Methods here may add
## to the floor's surface, but the floor itself stays absolutely minimal.

Class is Vector{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Vector]
	];

	## Number of elements held by the vector [v].
	##
	## @param v: The vector.
	## @return: Element count.
	Function of Int is vecLength(Any is v){
		return base:sysinternal:Vector:vecLength(v: v);
	}

	## Item at [idx] in vector [v], or [def] when out of bounds.
	##
	## @param v: The vector.
	## @param idx: Zero-based element index.
	## @param def: Fallback when [idx] is out of bounds.
	## @return: The element, or [def].
	Function of Any is vecGetAt(Any is v, Int is idx, Any is def){
		return base:sysinternal:Vector:vecGetAt(v: v, idx: idx, def: def);
	}

	## Overwrites item at [idx] in vector [v].
	##
	## @param v: The vector.
	## @param idx: Zero-based element index.
	## @param item: The replacement value.
	Function is vecSetAt(Any is v, Int is idx, Any is item){
		base:sysinternal:Vector:vecSetAt(v: v, idx: idx, item: item);
	}

	## Appends [item] to vector [v].
	##
	## @param v: The vector.
	## @param item: Value to append.
	Function is vecAdd(Any is v, Any is item){
		base:sysinternal:Vector:vecAdd(v: v, item: item);
	}

	## Removes and returns the last element of [v], or [def] when empty.
	##
	## @param v: The vector.
	## @param def: Fallback when [v] is empty.
	## @return: The removed last element, or [def].
	Function of Any is vecPopLast(Any is v, Any is def){
		return base:sysinternal:Vector:vecPopLast(v: v, def: def);
	}

	## Removes and returns the element at [idx] from [v], shifting trailing elements.
	##
	## @param v: The vector.
	## @param idx: Zero-based index to remove.
	## @param def: Fallback when [idx] is out of bounds.
	## @return: The removed element, or [def].
	Function of Any is vecRemoveAt(Any is v, Int is idx, Any is def){
		return base:sysinternal:Vector:vecRemoveAt(v: v, idx: idx, def: def);
	}

	## Removes all elements from vector [v].
	##
	## @param v: The vector.
	Function is vecClear(Any is v){
		base:sysinternal:Vector:vecClear(v: v);
	}
}
