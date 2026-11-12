#! --test suite rule: test methods are void with zero parameters. A
#! method named test* with any other signature is a compile-time
#! diagnostic, never a silently-skipped test.

Class is TestBadSignature{

	Function is testWithParams(Int is n){
	}
}
