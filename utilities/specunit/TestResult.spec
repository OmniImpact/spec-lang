#! Package specunit
#! The SpecUnit result model: one instance per executed test method,
#! aggregating soft-assert failures (see KNOWLEDGE-SPECDEV.md §4a).

## One test method's execution record. A test passes iff its failure
## list is empty — assertions record and continue, so a single run
## reports every broken expectation, JUnit assertAll style.

Class is TestResult{
	namespace: ['specunit'];

	## The fully-qualified test identity: "ClassName.methodName".
	String is name;

	## Whether the method completed with zero recorded failures.
	Boolean is passed: true;

	## The failure messages, in assertion order.
	Array of String is failures: [];

	## Wall-clock stamp when the method began (Process:clockMs).
	Int is startedAtMs: 0;

	## endTest's computed duration.
	Int is durationMs: 0;

	## The registry's check count when this test began — endTest
	## interprets the span [checksBefore, checks:length()) as this
	## test's assertions.
	Int is checksBefore: 0;

	## Creates a passing result for the named test.
	##
	## @param testName: The "ClassName.methodName" identity.
	replace Function is init(String is testName){
		self:name: testName;
	}
}
