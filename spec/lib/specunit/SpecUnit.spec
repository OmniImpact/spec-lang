#! Package specunit
#! The SpecUnit registry singleton — the mutable state Assert writes and
#! the runner reads (see SPECUNIT.md). State rides held ARRAY fields: the
#! held field reference is immutable (the once-guard singleton), the
#! contained collection is not — addFailure mutates the current test's
#! result through the current-cell array.
#!
#! This class deliberately declares no service surfaces: held bodies have
#! no instance, so as-imported surfaces (which dispatch through a hidden
#! instance field) are unusable in held bodies, and the wrappers' init()
#! declares no return value, so they cannot be local-constructed either.
#! Everything needing services lives in SpecUnitRunner (an instance class
#! with proper as-imports), which the --test entry constructs.

Class is SpecUnit{
	namespace: ['specunit'];

	replace Array of Array of String is using: [
		['specunit', TestResult]
	];

	## Every executed test, in execution order.
	held Array of TestResult is results: [];

	## The running test's cell: zero entries between tests, exactly one
	## while a method executes.
	held Array of TestResult is currentCell: [];

	## Records one soft-assert failure against the current test. The
	## method keeps running; the result flips to failed and the message
	## joins its failure list. The cell is non-empty by invariant: the
	## runner's beginTest runs before any assert can fire, so no guard —
	## and no Conditional import — is needed here (held bodies cannot
	## reach instance-imported surfaces).
	##
	## @param msg: The failure message.
	held Function is addFailure(String is msg){
		local TestResult is r: SpecUnit:currentCell:get(index: 0);
		r:passed: false;
		r:failures:add(item: msg);
	}
}
