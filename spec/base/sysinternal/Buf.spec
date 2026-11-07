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

	## Buffer [b] with every [search] occurrence replaced by [replacement].
	##
	## @param b: The buffer.
	## @param search: Sequence to replace.
	## @param replacement: Replacement sequence.
	## @return: The replaced copy.
	Function of String is stringReplaceAll(String is b, String is search, String is replacement);

	## Buffer [b] with leading/trailing space, tab, newline, CR removed.
	##
	## @param b: The buffer.
	## @return: The trimmed copy.
	Function of String is stringTrim(String is b);

	## True when [b] is non-empty and every byte is a digit.
	##
	## @param b: The buffer.
	## @return: true when all digits.
	Function of Boolean is stringIsDigit(String is b);

	## True when [b] is non-empty and every byte is a letter.
	##
	## @param b: The buffer.
	## @return: true when all letters.
	Function of Boolean is stringIsAlpha(String is b);

	## True when [b] is non-empty and every byte is whitespace.
	##
	## @param b: The buffer.
	## @return: true when all whitespace.
	Function of Boolean is stringIsWhitespace(String is b);

	## Number of leading [search] repetitions in buffer [b].
	##
	## @param b: The buffer.
	## @param search: The repetition unit.
	## @return: Repetition count.
	Function of Int is stringCountLeading(String is b, String is search);

	## Parts of buffer [b] split on [delimiter]; the trailing part is
	## always present. Empty delimiter: every byte is its own part.
	##
	## @param b: The buffer.
	## @param delimiter: Split boundary.
	## @return: The parts.
	Function of Array of String is stringSplit(String is b, String is delimiter);

	## Lines of buffer [b] (split on newline, trailing CR stripped).
	##
	## @param b: The buffer.
	## @return: The lines.
	Function of Array of String is stringLines(String is b);

	## Parses buffer [b] as an integer in [base] (2-36), accepting 0x/0b/0o
	## prefixes and _ separators. Returns [def] on any invalid input.
	##
	## @param b: The buffer.
	## @param base: Number base (2-36).
	## @param def: Fallback on invalid input.
	## @return: The parsed value, or [def].
	Function of Int is parseBase(String is b, Int is base, Int is def);
}
