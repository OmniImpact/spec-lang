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

	## Runtime binding: the implementations for this class's
	## declaration-only methods live in the runtime floor; the backend
	## emits no struct, vtable, or constructor for it.
	binding: true;

	## Appends a byte to a [Byte] buffer. Infallible: the buffer grows.
	Function is push(T is b){
	}

	## Appends the bytes of [s] to a [Byte] buffer. Infallible: the buffer grows.
	Function is appendString(String is s){
	}

	## Returns the byte at [index], or [default] if out of bounds ([error] notified).
	##
	## @param index: Zero-based position.
	## @param default: Fallback value used when there is no successful answer.
	## @param error: Optional callback receiving a diagnostic message.
	Function of T is get(Int is index, T is default, Function is error){
	}

	## Overwrites the byte at [index]; [error] notified if out of bounds.
	Function is set(Int is index, T is item, Function is error){
	}

	## Removes and returns the last byte, or [default] if empty ([error] notified).
	Function of T is pop(T is default, Function is error){
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

	## Appends all bytes of [other] into this [Byte] buffer.
	Function is appendBytes(List of Byte is other){
	}

	## Appends [count] bytes starting at [start] from [other] into this [Byte] buffer.
	Function is appendRange(List of Byte is other, Int is start, Int is count){
	}

	## Returns a new [List of Byte] containing bytes [start..end).
	Function of List of Byte is slice(Int is start, Int is end){
	}

	## Appends a 16-bit big-endian unsigned integer.
	Function is pushU16BE(Int is v){
	}

	## Appends a 32-bit big-endian unsigned integer.
	Function is pushU32BE(Int is v){
	}

	## Appends a 32-bit little-endian unsigned integer.
	Function is pushU32LE(Int is v){
	}

	## Reads a 16-bit big-endian unsigned integer at [offset], or [default] if out of bounds.
	Function of Int is readU16BE(Int is offset, Int is default: 0){
	}

	## Reads a 32-bit big-endian unsigned integer at [offset], or [default] if out of bounds.
	Function of Int is readU32BE(Int is offset, Int is default: 0){
	}

	## Reads a 32-bit little-endian unsigned integer at [offset], or [default] if out of bounds.
	Function of Int is readU32LE(Int is offset, Int is default: 0){
	}

}
