#! Package examples:regression
#! Tracks the strict root-contract rule for Any-typed references.

## NEGATIVE test: this file MUST FAIL TO COMPILE. That is its correct behavior.
##
## Guarded behavior: an Any-typed reference may only invoke root-contract
## members (toString, typeName, init). Calling a subclass method through
## `Any` is rejected — cast to the concrete class first.
##
## Required diagnostic:
## - Member 'fetch' is not part of the root contract
##
## NOTE FOR RUNNERS: assert that this file fails to compile AND that the
## compiler output contains the diagnostic.

Class is StrictAnimal{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	Function of String is speak(){
		return '...';
	}
}

Class of StrictAnimal is StrictDog{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	replace Function of String is speak(){
		return 'woof';
	}

	Function of String is fetch(){
		return 'ball';
	}
}

Class is StrictNegativeTest{

	replace Array of Array of String is using: [
		['base', 'sys', Output],
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args){
		# Holding a StrictDog in an Any-typed reference: only root-contract
		# members (toString, typeName, init) are callable. fetch is not
		# declared on Any, so this call is rejected.
		local Any is anyRef: StrictDog:init();
		Output:line(anyRef:fetch());
	}
}
