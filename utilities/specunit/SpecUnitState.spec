#! Package specunit
#! The SpecUnitState registry singleton — the mutable state Assert writes
#! and the runner reads (see KNOWLEDGE-SPECDEV.md §4a). State rides held ARRAY fields:
#! the held field reference is immutable (the once-guard singleton), the
#! contained collection is not — addFailure mutates the current test's
#! result through the current-cell array.
#!
#! This class deliberately declares no service surfaces: held bodies have
#! no instance, so as-imported surfaces (which dispatch through a hidden
#! instance field) are unusable in held bodies, and the wrappers' init()
#! declares no return value, so they cannot be local-constructed either.
#! Everything needing services lives in SpecUnitRunner (an instance class
#! with proper as-imports), which the suite entry (SpecUnitTest's
#! argv-Map init) constructs.

Class is SpecUnitState{
	namespace: ['specunit'];

	replace Array of Array of String is using: [
		['specunit', TestResult],
		['specunit', CheckRecord]
	];

	## Every executed test, in execution order.
	held Array of TestResult is results: [];

	## Every assertion recorded, in execution order (the branch-free
	## assertion pattern: Assert appends records unconditionally; the
	## runner interprets the span since each test's checksBefore).
	held Array of CheckRecord is checks: [];

	## The running test's cell: zero entries between tests, exactly one
	## while a method executes.
	held Array of TestResult is currentCell: [];

}
