#! Package base:struct
#! Lean growable sequence declared with [T] syntax. [Byte] is a compact byte buffer
#! (the string-builder floor); other element types use a pointer vector.

## A lean growable sequence declared with [T] syntax (e.g. [Byte], [String]).
##
## Fallible reads take a mandatory default: value used whenever there is no
## successful answer, plus an optional error: callback invoked in addition when
## a problem occurs. Bracket indexing is not provided on List; use get.
Class is List of T{
	namespace: ['base', 'struct'];

	## Appends a byte to a [Byte] buffer. Infallible: the buffer grows.
	Function is push(Any is b){
	}

	## Appends the bytes of [s] to a [Byte] buffer. Infallible: the buffer grows.
	Function is appendString(String is s){
	}

	## Returns the byte at [index], or [default] if out of bounds ([error] notified).
	##
	## @param index: Zero-based position.
	## @param default: Fallback value used when there is no successful answer.
	## @param error: Optional callback receiving a diagnostic message.
	Function of T is get(Int is index, Any is default, Function is error){
	}

	## Overwrites the byte at [index]; [error] notified if out of bounds.
	Function is set(Int is index, T is item, Function is error){
	}

	## Removes and returns the last byte, or [default] if empty ([error] notified).
	Function of T is pop(Any is default, Function is error){
	}

	## Returns the number of elements.
	Function of Int is length(){
	}

	## Removes all elements. Capacity is retained.
	Function is clear(){
	}

	## Returns the buffered bytes as a string ([Byte] buffers only).
	replace Function of String is toString(){
	}

}
