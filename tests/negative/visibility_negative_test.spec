#! specunit: negative
#! expect: Member 'secret' is local to class 'VisBase'
#! expect: Member 'helper' is contained in class 'VisBase'
#! expect: Member 'secret' is local in ancestor 'VisBase' and cannot be replaced or merged
#! expect: Member 'counter' is local in ancestor 'ShadowedLocal' and cannot be replaced or merged
#! expect: combines 'replace'/'merge' with a visibility modifier

#! Package examples:regression
#! Tracks visibility enforcement diagnostics.

## NEGATIVE test: this file MUST FAIL TO COMPILE. That is its correct behavior.
##
## Guarded behavior:
## - `local` members are inaccessible outside the declaring class.
## - `contained` members are inaccessible from unrelated classes.
## - `local`/`contained` members cannot be replaced or merged.
## - A child cannot shadow a `local` ancestor member.
## - 'replace'/'merge' cannot combine with 'local'/'contained'.
##
## Required diagnostics:
## - Member 'secret' is local to class 'VisBase' and cannot be accessed from 'VisBreaker'.
## - Member 'helper' is contained in class 'VisBase' and cannot be accessed from unrelated class 'VisUnrelated'.
## - Member 'secret' is local in ancestor 'VisBase' and cannot be replaced or merged.
## - Member 'counter' is local in ancestor 'ShadowedLocal' and cannot be replaced or merged.
## - Member 'broken' ... combines 'replace'/'merge' with a visibility modifier.
##
## NOTE FOR RUNNERS: assert that this file fails to compile AND that the
## compiler output contains all four diagnostics.

Class is VisBase{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	local Function of Int is secret(){
		return 1;
	}

	contained Function of Int is helper(){
		return 2;
	}
}

Class is VisBreaker{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	replace Function is init(Map of String to String is args){
		local VisBase is b: VisBase:init();
		Output:line(b:secret());
	}
}

Class is VisUnrelated{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	replace Function is init(Map of String to String is args){
		local VisBase is b: VisBase:init();
		Output:line(b:helper());
	}
}

Class of VisBase is VisOverrideAttempt{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	replace Function of Int is secret(){
		return 9;
	}
}

Class is ShadowedLocal{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	local Int is counter: 0;
}

Class of ShadowedLocal is ShadowChild{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	local Int is counter: 1;
}

Class is ContradictoryModifiers{

	replace Array of Array of String is using: [
		['base', 'sys', as Output()]
	];
	replace local Function of Int is broken(){
		return 1;
	}
}
