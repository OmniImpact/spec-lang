#! specunit: negative
#! expect: Entry class 'EntryBadInit' requires an init

#! Entry-init rule: feed the command-line args when an init can take
#! them, fall back to an empty init, and only error when the entry's
#! lattice declares overloads but NEITHER form exists. This entry has
#! exactly one overload — required String — so neither form exists and
#! the driver reports a compile-time diagnostic instead of emitting a
#! main the backend C compiler rejects.

Class is EntryBadInit{

	replace Function is init(String is name){
	}
}
