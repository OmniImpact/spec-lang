#! specunit: run-fail
#! expect: No test classes found in

#! SpecUnit framework rule: a suite whose classes extend the base but
#! declare no `test*` methods has nothing to run — the runner diagnoses
#! it and fails the CI contract instead of reporting a silent
#! all-green. (The former --test diagnostic for this shape dissolved
#! with the compiler test mode; the framework owns the rule now.)

Class of SpecUnitTest is TestEmptySuite{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner]
	];

	Function is helperNotATest(){
	}
}
