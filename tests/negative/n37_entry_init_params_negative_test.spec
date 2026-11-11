#! The entry init must be constructible from argv: zero parameters, or
#! exactly one Map of String to String. Any other signature is a
#! compile-time diagnostic — never raw backend-C compiler output.

Class is EntryBadInit{

	replace Function is init(String is name){
	}
}
