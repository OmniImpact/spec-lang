#! specunit: negative
#! expect: inherits conflicting implementations of 'value' from 'DiamondA' and 'DiamondB'

#! Package examples:regression
#! Tracks ambiguous multiple-inheritance implementation conflicts.

## NEGATIVE test: this file MUST FAIL TO COMPILE. That is its correct behavior.
##
## Guarded behavior: when two unrelated parents provide concrete
## implementations of the same method and the child does not declare it,
## first-wins resolution would silently pick one - this is a compile error.
## Abstract declarations do not conflict (they compose into contracts), and
## an ancestor-descendant declarer pair does not conflict (the descendant
## refines the ancestor).
##
## Required diagnostics:
## - DiamondBadChild inherits conflicting implementations of 'value' from
##   'DiamondA' and 'DiamondB'.
## - SharedBase's single implementation reached via both paths is NOT a
##   conflict: DiamondSharedChild must compile cleanly (positive control).
##
## NOTE FOR RUNNERS: assert that this file fails to compile AND that the
## compiler output contains the conflicting-implementations diagnostic.

Class is DiamondA{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	replace Function of Int is value(){
		return 1;
	}
}

Class is DiamondB{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	replace Function of Int is value(){
		return 2;
	}
}

Class of DiamondA, DiamondB is DiamondBadChild{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	replace Function is init(Map of String to String is args){
		Output:line('unreachable');
	}
}

Class is SharedBase{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	replace Function of Int is shared(){
		return 7;
	}
}

Class of SharedBase is SharedLeft{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
}

Class of SharedBase is SharedRight{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
}

Class of SharedLeft, SharedRight is DiamondSharedChild{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	replace Function is init(Map of String to String is args){
		Output:line('shared ok');
	}
}
