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
	local Function of Int is secret(){
		return 1;
	}

	contained Function of Int is helper(){
		return 2;
	}
}

Class is VisBreaker{
	replace Function is init(Map of String to String is args){
		local VisBase is b: VisBase:init();
		output:line(b:secret());
	}
}

Class is VisUnrelated{
	replace Function is init(Map of String to String is args){
		local VisBase is b: VisBase:init();
		output:line(b:helper());
	}
}

Class of VisBase is VisOverrideAttempt{
	replace Function of Int is secret(){
		return 9;
	}
}

Class is ShadowedLocal{
	local Int is counter: 0;
}

Class of ShadowedLocal is ShadowChild{
	local Int is counter: 1;
}

Class is ContradictoryModifiers{
	replace local Function of Int is broken(){
		return 1;
	}
}
