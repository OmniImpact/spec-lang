#! Package examples:regression
#! Tracks merge-on-Function validation rules.

## NEGATIVE test: this file MUST FAIL TO COMPILE. That is its correct behavior.
##
## Guarded behavior:
## - A forward statement in a non-merge method is rejected.
## - A merge method delegating to an abstract parent is rejected.
## - Partial forwards must name their arguments.
## - Forward arguments exceeding the parent signature are rejected.
## - Omitted forward arguments without parent defaults are rejected.
## - Forward argument type mismatches are rejected.
##
## Required diagnostics:
## - Forward statement `(args...)` requires the enclosing method to declare 'merge'.
## - Cannot merge method 'absWrap' ... with abstract method from 'FwdBase'.
## - Partial forward requires named arguments.
## - Forward statement passes 3 arguments but parent 'twoOf' accepts 2.
## - Forward statement omits 'b' of 'twoOf' which has no default value.
## - Forward argument 'n' of 'scaled': cannot assign 'String' to 'Int'.
##
## NOTE FOR RUNNERS: assert that this file fails to compile AND that the
## compiler output contains all six diagnostics.

Class is FwdBase{
	replace Function of Int is double(Int is n){
		return n * 2;
	}

	replace Function of Int is twoOf(Int is a, Int is b){
		return a;
	}

	replace Function of Int is partial(Int is a, Int is b){
		return a;
	}

	replace Function of Int is absWrap(Int is n){
	}
}

Class of FwdBase is FwdChild{

	replace Function is plainCall(){
		('unexpected');
	}

	merge Function of Int is absWrap(Int is n){
		(n);
	}

	merge Function of Int is double(Int is n){
		(n: 'not-a-number');
	}

	merge Function of Int is twoOf(Int is a, Int is b){
		(1, 2, 3);
	}

	merge Function of Int is partial(Int is a, Int is b){
		(1);
	}
}

Class is FwdNegativeTest{

	replace Array of String is using: [
		base:io:Output
	];

	replace Function is init(Map of String to String is args){
		output:line('unreachable');
	}
}
