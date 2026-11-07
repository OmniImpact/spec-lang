#! Package base:sysinternal
#! The byte-buffer floor: primitive operations on managed buffers.
##
## Body-less, interface-style declarations bound to the runtime's C floor.
## The namespace IS the binding annotation: every method compiles to
## spec_<snake_case(method)> per the floor naming convention. These are the
## ONLY methods in the system allowed to touch C; all other classes reach
## the floor through this class. Ownership follows the standard claim/retain
## conventions.

Class is Buf{
	namespace: ['base', 'sysinternal'];

	## Number of bytes held by the buffer [b].
	##
	## @param b: The buffer.
	## @return: Byte count.
	Function of Int is bufLength(String is b);

	## Byte value at [idx], or [def] when out of bounds.
	##
	## @param b: The buffer.
	## @param idx: Zero-based byte index.
	## @param def: Fallback when [idx] is out of bounds.
	## @return: The byte value, or [def].
	Function of Int is bufGetByte(String is b, Int is idx, Int is def);

	## Refcounted copy of buffer [b].
	##
	## @param b: The buffer.
	## @return: An owned copy sharing no storage with [b].
	Function of String is stringCopy(String is b);

	## Bytes [start] (inclusive) to [end] (exclusive) of buffer [b].
	##
	## @param b: The buffer.
	## @param start: Inclusive start index.
	## @param end: Exclusive end index.
	## @return: The sub-buffer.
	Function of String is stringSubstring(String is b, Int is start, Int is end);

	## First index of [needle] within buffer [b], or [def] when absent.
	##
	## @param b: The buffer.
	## @param needle: Byte sequence to locate.
	## @param def: Fallback when absent (conventionally -1).
	## @return: The index, or [def].
	Function of Int is stringIndexOf(String is b, String is needle, Int is def);

	## First index of [needle] within buffer [b] at or after [from], or [def] when absent.
	##
	## @param b: The buffer.
	## @param needle: Byte sequence to locate.
	## @param from: Zero-based start position.
	## @param def: Fallback when absent (conventionally -1).
	## @return: The index, or [def].
	Function of Int is stringIndexOfFrom(String is b, String is needle, Int is from, Int is def);

	## Buffer [b] with every [search] occurrence replaced by [replacement].
	## Appends the bytes of [src] to the end of [dst] in place. [dst] must
	## be a mutable (non-interned) buffer — the accumulator's sole owner.
	##
	## @param dst: The buffer grown in place.
	## @param src: The bytes appended.
	Function is bufAppendBuf(String is dst, String is src);
}
