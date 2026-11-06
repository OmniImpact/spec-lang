#! Package base:core
#! The byte-buffer floor: primitive operations on managed buffers.
##
## Body-less declarations bound to the runtime's C floor (`spec_buf_*`).
## The String class implements its methods over these primitives; ownership
## follows the standard claim/retain conventions.

	Class is Buf{

		## Number of bytes held by the buffer [b].
		Function of Int is bufLength(String is b){
		}

		## Byte value at [idx], or [def] when out of bounds.
		Function of Int is bufGetByte(String is b, Int is idx, Int is def){
		}

		## Refcounted copy of buffer [b].
		Function of String is bufCopy(String is b){
		}

		## Bytes [start] (inclusive) to [end] (exclusive) of buffer [b].
		Function of String is bufSubstring(String is b, Int is start, Int is end){
		}

		## First index of [needle] within buffer [b], or [def] when absent.
		Function of Int is bufIndexOf(String is b, String is needle, Int is def){
		}

		## Buffer [b] with every [search] occurrence replaced by [replacement].
		Function of String is bufReplace(String is b, String is search, String is replacement){
		}

		## Buffer [b] with leading/trailing space, tab, newline, CR removed.
		Function of String is bufTrim(String is b){
		}

		## True when [b] is non-empty and every byte is a digit.
		Function of Boolean is bufIsDigit(String is b){
		}

		## True when [b] is non-empty and every byte is a letter.
		Function of Boolean is bufIsAlpha(String is b){
		}

		## True when [b] is non-empty and every byte is whitespace.
		Function of Boolean is bufIsWhitespace(String is b){
		}

		## Number of leading [search] repetitions in buffer [b].
		Function of Int is bufCountLeading(String is b, String is search){
		}

		## Parts of buffer [b] split on [delimiter]; the trailing part is
		## always present. Empty delimiter: every byte is its own part.
		Function of Array of String is bufSplit(String is b, String is delimiter){
		}

		## Lines of buffer [b] (split on newline, trailing CR stripped).
		Function of Array of String is bufLines(String is b){
		}

		## Parses buffer [b] as an integer in [base] (2-36), accepting 0x/0b/0o
		## prefixes and _ separators. Returns [def] on any invalid input.
		Function of Int is bufParseBase(String is b, Int is base, Int is def){
		}
	}
