#! N25 (FUNCTIONS.md Part IV IV.2): same-named inner classes under
#! different enclosing classes are ambiguous in the flat registry —
#! the collision is a compile error, not a silent merge.

Class is N25OuterA{
	Class is Dup{
		Function of Int is value(){
			return 1;
		}
	}
}

Class is N25OuterB{
	Class is Dup{
		Function of Int is value(){
			return 2;
		}
	}
}
