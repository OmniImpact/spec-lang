#! Package base:sys
#! Heap-allocated reference cell for shared mutable state.
##
## A Box holds a single value of type T on the heap. Multiple references
## to the same Box share access to the wrapped value, enabling shared mutable
## state across scopes, closure captures, and pass-by-reference patterns.
## Compiled as a distinct monomorphized specialization per type argument T.

Class is Box of T{
	namespace: ['base', 'sys'];

	local T is val;

	## Creates a new heap-allocated box containing [value].
	##
	## @param value: The initial value to store in the box.
	replace Function is init(T is value){
		:val: value;
	}

	## Retrieves the current value stored in the box.
	##
	## @return: The wrapped value.
	Function of T is get(){
		return :val;
	}

	## Updates the value stored in the box.
	##
	## @param value: The new value.
	Function is set(T is value){
		:val: value;
	}

	## String representation of the box.
	##
	## @return: String representation.
	replace Function of String is toString(){
		return 'Box(' . (:val as String) . ')';
	}
}
