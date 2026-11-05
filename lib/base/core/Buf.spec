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
}
