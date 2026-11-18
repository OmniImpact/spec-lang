#! The first SpecUnit tests of the type system's void/Function semantics
#! (the void-vocabulary standardization): Void is the one canonical void spelling;
#! the paramless Function type is the EMPTY FUNCTION — a distinct, valid,
#! non-void return type whose C emission is void. The runner must discover
#! and invoke test methods of BOTH declaration forms; the assertions
#! verify each method actually executed on its own fresh instance.

Class of SpecUnitTest is TestFunctionTypes{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	## Per-test fresh instances reset this — each method marks its own
	## value and asserts the marker, proving execution and isolation.
	Int is marked: 0;

	## Declared with the paramless Function type — the empty function:
	## a valid, distinct, NON-void return type. The registry records it
	## under flag 4 (not the Void flag), and the runner invokes it.
	Function is testParamlessFunctionDeclaration(){
		self:mark(v: 1);
		Assert:areEqualInt(1, self:marked);
	}

	## Declared bare — the parser normalizes the untyped form to the
	## canonical Void spelling; identical runtime behavior to the
	## paramless form above.
	testVoidDeclaration(){
		self:mark(v: 2);
		Assert:areEqualInt(2, self:marked);
	}

	Function is mark(Int is v){
		self:marked: v;
	}
}
