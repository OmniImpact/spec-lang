#! The first SpecUnit tests of the framework itself: the base class's
#! reflective defaults. name() defaults to the declaring class's own
#! name; description() defaults to the user-facing summary with the
#! test count. The class has exactly two test methods, so the
#! description is assertable verbatim.

Class of SpecUnitTest is TestSpecUnitTestBase{

	replace [[String]] is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Conditional()]
	];

	Function is testDefaultName(){
		Assert:areEqualString('TestSpecUnitTestBase', :name());
	}

	Function is testDefaultDescription(){
		Assert:areEqualString('Unit test: TestSpecUnitTestBase has 2 tests', :description());
		Assert:areEqualInt(30, :timeout());
		Assert:areEqualInt(30000, :timeoutMs());
	}
}
