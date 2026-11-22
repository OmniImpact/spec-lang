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

	replace Array of Array of String is using: [
		['base', 'sys', as Vector()]
	];

	## Appends [item] to this list. Infallible: the backing buffer grows.
	Function is push(T is item){
		Vector:listPush(v: :, item: item);
	}

	## Appends the bytes of [value] to a [Byte] buffer. Infallible: the buffer grows.
	Function is appendString(String is value){
		Vector:byteBufAppendString(b: :, s: value);
	}

	## Returns the element at [index], or [default] if out of bounds ([error] notified).
	##
	## @param index: Zero-based position.
	## @param default: Fallback value used when there is no successful answer.
	## @param error: Optional callback receiving a diagnostic message.
	Function of T is get(Int is index, T is default, Function is error: local Function(String is m){}){
		return Vector:listGet(v: :, idx: index, def: default, error: error);
	}

	## Overwrites the element at [index]; [error] notified if out of bounds.
	Function is set(Int is index, T is item, Function is error: local Function(String is m){}){
		Vector:listSet(v: :, idx: index, item: item, error: error);
	}

	## Removes and returns the last element, or [default] if empty ([error] notified).
	Function of T is pop(T is default, Function is error: local Function(String is m){}){
		return Vector:listPop(v: :, def: default, error: error);
	}

	## Returns the number of elements.
	Function of Int is length(){
		return Vector:listLength(v: :);
	}

	## Returns whether the list contains zero elements.
	Function of Boolean is isEmpty(){
		return :length() == 0;
	}

	## Removes all elements. Capacity is retained.
	Function is clear(){
		Vector:listClear(v: :);
	}

	## Returns the buffered bytes as a string ([Byte] buffers only).
	replace Function of String is toString(){
		return Vector:byteBufToString(b: :);
	}

	## Appends all bytes of [other] into this [Byte] buffer.
	Function is appendBytes(List of Byte is other){
		Vector:byteBufAppendBytes(b: :, other: other);
	}

	## Appends [count] bytes starting at [start] from [other] into this [Byte] buffer.
	Function is appendRange(List of Byte is other, Int is start, Int is count){
		Vector:byteBufAppendRange(b: :, other: other, start: start, count: count);
	}

	## Returns a new [List of Byte] containing bytes [start..end).
	Function of List of Byte is slice(Int is start, Int is end){
		return Vector:byteBufSlice(b: :, start: start, end: end);
	}

	## Appends a 16-bit big-endian unsigned integer.
	Function is pushU16BE(Int is v){
		Vector:byteBufPushU16BE(b: :, v: v);
	}

	## Appends a 32-bit big-endian unsigned integer.
	Function is pushU32BE(Int is v){
		Vector:byteBufPushU32BE(b: :, v: v);
	}

	## Appends a 32-bit little-endian unsigned integer.
	Function is pushU32LE(Int is v){
		Vector:byteBufPushU32LE(b: :, v: v);
	}

	## Reads a 16-bit big-endian unsigned integer at [offset], or [default] if out of bounds.
	Function of Int is readU16BE(Int is offset, Int is default: 0){
		return Vector:byteBufReadU16BE(b: :, offset: offset, def: default);
	}

	## Reads a 32-bit big-endian unsigned integer at [offset], or [default] if out of bounds.
	Function of Int is readU32BE(Int is offset, Int is default: 0){
		return Vector:byteBufReadU32BE(b: :, offset: offset, def: default);
	}

	## Reads a 32-bit little-endian unsigned integer at [offset], or [default] if out of bounds.
	Function of Int is readU32LE(Int is offset, Int is default: 0){
		return Vector:byteBufReadU32LE(b: :, offset: offset, def: default);
	}

}
