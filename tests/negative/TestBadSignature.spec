#! specunit: run-fail
#! expect: Introspection:invoke supports void zero-parameter methods only

#! SpecUnit framework rule: test methods are void with zero parameters.
#! There is no compiler test mode to enforce the signature at compile
#! time — the reflection floor's invoke guard panics at run time
#! instead, the suite fails, and the runner's run-fail contract
#! catches it. Never a silently-skipped test.

Class of SpecUnitTest is TestBadSignature{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner]
	];

	Function is testWithParams(Int is n){
	}
}
