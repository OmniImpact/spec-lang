#! --test suite rule: the generated runner main constructs
#! SpecUnitRunner, so the suite must import the specunit package. A
#! suite with test classes but no SpecUnitRunner import is a
#! compile-time diagnostic, never raw backend-C output.

Class is TestMissingImport{

	Function is testSomething(){
	}
}
