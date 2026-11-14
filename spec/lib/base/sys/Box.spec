#! Package base:sys
#! Heap-allocated reference cell for shared mutable state.
##
## A Box holds a single value of type T on the heap. Multiple references
## to the same Box share access to the wrapped value, enabling shared mutable
## state across scopes, closure captures, and pass-by-reference patterns.
##
## ARC memory discipline:
## For ARC-managed types (String, Array, Map, List, custom class instances),
## [isArc] defaults to true so values are retained and released properly.
## For unmanaged primitives (Int, Boolean, Byte), [isArc] should be false.

Class is Box of T{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Box]
	];

	local Any is cell: 0;
	local Boolean is arcManaged: false;

	## Creates a new heap-allocated box containing [value].
	##
	## @param value: The initial value to store in the box.
	## @param isArc: True if [value] is an ARC-managed reference (default: true).
	## @return: The initialized Box instance.
	replace Function is init(T is value, Boolean is isArc: true){
		self:arcManaged: isArc;
		self:cell: base:sysinternal:Box:boxNew(val: value, isArc: isArc);
	}

	## Retrieves the current value stored in the box.
	##
	## @return: The wrapped value.
	Function of T is get(){
		return base:sysinternal:Box:boxGet(b: self:cell);
	}

	## Updates the value stored in the box.
	##
	## @param value: The new value.
	Function is set(T is value){
		base:sysinternal:Box:boxSet(b: self:cell, newVal: value);
	}

	## True if the box is configured for ARC-managed references.
	##
	## @return: True if ARC managed.
	Function of Boolean is isArc(){
		return self:arcManaged;
	}

	## String representation of the box.
	##
	## @return: String representation.
	replace Function of String is toString(){
		return base:sysinternal:Box:boxToString(b: self:cell);
	}
}
