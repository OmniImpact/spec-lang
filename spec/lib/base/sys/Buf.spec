#! Package base:sys
#! Public wrapper over the sysinternal byte-buffer floor.
##
## The ONLY classes allowed to call base:sysinternal are the same-name
## wrappers in base:sys (enforced by the checker). Wrapper bodies address
## the floor by its full qualified chain; everything outside this package
## addresses the floor through these public methods. Methods here may add
## to the floor's surface, but the floor itself stays absolutely minimal.

Class is Buf{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Buf]
	];

	## Number of bytes held by the buffer [b].
	##
	## @param b: The buffer.
	## @return: Byte count.
	Function of Int is bufLength(String is b){
		return base:sysinternal:Buf:bufLength(b: b);
	}

	## Byte value at [idx], or [def] when out of bounds.
	##
	## @param b: The buffer.
	## @param idx: Zero-based byte index.
	## @param def: Fallback when [idx] is out of bounds.
	## @return: The byte value, or [def].
	Function of Int is bufGetByte(String is b, Int is idx, Int is def){
		return base:sysinternal:Buf:bufGetByte(b: b, idx: idx, def: def);
	}

	## Refcounted copy of buffer [b].
	##
	## @param b: The buffer.
	## @return: An owned copy sharing no storage with [b].
	Function of String is stringCopy(String is b){
		return base:sysinternal:Buf:stringCopy(b: b);
	}

	## Returns the process-interned form of [s]: equal contents yield
	## the SAME string object. Interned strings are immortal.
	##
	## @param s: The string.
	## @return: The interned string.
	Function of String is intern(String is s){
		return base:sysinternal:Buf:intern(b: s);
	}

	## Bytes [start] (inclusive) to [end] (exclusive) of buffer [b].
	##
	## @param b: The buffer.
	## @param start: Inclusive start index.
	## @param end: Exclusive end index.
	## @return: The sub-buffer.
	Function of String is stringSubstring(String is b, Int is start, Int is end){
		return base:sysinternal:Buf:stringSubstring(b: b, start: start, end: end);
	}

	## First index of [needle] within buffer [b], or [def] when absent.
	##
	## @param b: The buffer.
	## @param needle: Byte sequence to locate.
	## @param def: Fallback when absent (conventionally -1).
	## @return: The index, or [def].
	Function of Int is stringIndexOf(String is b, String is needle, Int is def){
		return base:sysinternal:Buf:stringIndexOf(b: b, needle: needle, def: def);
	}

	## First index of [needle] within buffer [b] at or after [from], or [def] when absent.
	##
	## @param b: The buffer.
	## @param needle: Byte sequence to locate.
	## @param from: Zero-based start position.
	## @param def: Fallback when absent (conventionally -1).
	## @return: The index, or [def].
	Function of Int is stringIndexOfFrom(String is b, String is needle, Int is from, Int is def){
		return base:sysinternal:Buf:stringIndexOfFrom(b: b, needle: needle, from: from, def: def);
	}

	## Buffer [b] with every [search] occurrence replaced by [replacement].
	##
	## @param b: The buffer.
	## @param search: Sequence to replace.
	## @param replacement: Replacement sequence.
	## @return: The replaced copy.
	Function of String is stringReplaceAll(String is b, String is search, String is replacement){
		return b:replaceAll(search: search, replacement: replacement);
	}

	## Buffer [b] with leading/trailing space, tab, newline, CR removed.
	##
	## @param b: The buffer.
	## @return: The trimmed copy.
	Function of String is stringTrim(String is b){
		return b:trim();
	}

	## True when [b] is non-empty and every byte is a digit.
	##
	## @param b: The buffer.
	## @return: true when all digits.
	Function of Boolean is stringIsDigit(String is b){
		return b:isDigit();
	}

	## True when [b] is non-empty and every byte is a letter.
	##
	## @param b: The buffer.
	## @return: true when all letters.
	Function of Boolean is stringIsAlpha(String is b){
		return b:isAlpha();
	}

	## True when [b] is non-empty and every byte is whitespace.
	##
	## @param b: The buffer.
	## @return: true when all whitespace.
	Function of Boolean is stringIsWhitespace(String is b){
		return b:isWhitespace();
	}

	## Number of leading [search] repetitions in buffer [b].
	##
	## @param b: The buffer.
	## @param search: The repetition unit.
	## @return: Repetition count.
	Function of Int is stringCountLeading(String is b, String is search){
		return b:countLeading(search: search);
	}

	## Parts of buffer [b] split on [delimiter]; the trailing part is
	## always present. Empty delimiter: every byte is its own part.
	##
	## @param b: The buffer.
	## @param delimiter: Split boundary.
	## @return: The parts.
	Function of Array of String is stringSplit(String is b, String is delimiter){
		return b:split(delimiter: delimiter);
	}

	## Lines of buffer [b] (split on newline, trailing CR stripped).
	##
	## @param b: The buffer.
	## @return: The lines.
	Function of Array of String is stringLines(String is b){
		return b:lines();
	}

	## Appends the bytes of [src] to the end of [dst] in place. [dst] must
	## be a mutable (non-interned) buffer — the accumulator's sole owner.
	##
	## @param dst: The buffer grown in place.
	## @param src: The bytes appended.
	Function is bufAppendBuf(String is dst, String is src){
		base:sysinternal:Buf:bufAppendBuf(dst: dst, src: src);
	}

	## Parses buffer [b] as an integer in [base] (2-36), accepting 0x/0b/0o
	## prefixes and _ separators. Returns [def] on any invalid input.
	##
	## @param b: The buffer.
	## @param base: Number base (2-36).
	## @param def: Fallback on invalid input.
	## @return: The parsed value, or [def].
	Function of Int is parseBase(String is b, Int is base, Int is def){
		return b:parseInt(base: base, default: def);
	}
}
