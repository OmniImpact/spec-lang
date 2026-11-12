#! specunit: negative
#! expect: must contain a forward statement
#! expect: 'merge' requires an Array field
#! expect: no parent declares a method with that name

#! Package examples:regression
#! Tracks the `merge` modifier: data-structure-aware field overriding.

## NEGATIVE test: this file MUST FAIL TO COMPILE. That is its correct behavior.
##
## Guarded behavior:
## - A `merge` method with a body but no forward statement is rejected.
## - `merge` on a non-mergeable field type (Int) is rejected.
## - `merge` on a method with no parent implementation is rejected.
##
## Required diagnostics:
## - Merge method 'signal' ... must contain a forward statement.
## - 'merge' requires an Array field; 'Int' is not mergeable.
## - Method 'orphan' declares 'merge' but no parent declares a method with that name.
##
## NOTE FOR RUNNERS: assert that this file fails to compile AND that the
## compiler output contains all three diagnostics.

Class is MergeBadBase{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

	replace Function of Int is signal(){
		return 1;
	}

	local Int is count: 1;
}

Class of MergeBadBase is MergeBadChild{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];

	# No forward statement: merge methods must delegate explicitly.
	merge Function of Int is signal(){
		return 2;
	}

	merge Int is count: 2;

	# No parent declares this method.
	merge Function is orphan(){
		();
	}
}

Class is MergeNegativeTest{

	replace Array of Array of String is using: [
		['base', 'sys', Output],
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('unreachable');
	}
}
