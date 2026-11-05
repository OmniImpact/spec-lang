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
	}
