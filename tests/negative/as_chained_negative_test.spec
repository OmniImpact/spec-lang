#! Package examples:regression
#! Tracks the chained-cast restriction of the `as` operator.

## NEGATIVE test: this file MUST FAIL TO COMPILE. That is its correct behavior.
##
## Guarded behavior: chained casts (`x as A as B`) are a syntax error; cast in
## separate steps instead.
##
## Required diagnostic:
## - Chained 'as' casts are not supported
##
## NOTE FOR RUNNERS: assert that this file fails to compile AND that the
## compiler output contains the diagnostic.

Class is AsChainedNegativeTest{

	replace local Function is init(Map of String to String is args){
		local Float is chained: 4 as Int as Float;
	}
}
