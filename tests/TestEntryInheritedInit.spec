#! SpecUnit port (from entry_inherited_init_test.spec): the inherited
#! entry init — a root class with NO init of its own resolves its
#! effective init through the lattice and main constructs it through
#! the OWNER's C symbol with the owner's arity. The chain here is two
#! hops (TestEntryInheritedInit -> EntryBaseChain -> SpecUnitTest), and
#! the base stamps SpecUnitTest:entryConstructed before any test runs.
#! If the emission ever flattened inits into the child (calling the
#! child's synthesized stub instead of the owner's symbol), the runner
#! would never start — and the runner's report-table gate fails that
#! silent-empty shape instead of false-passing it.

Class of SpecUnitTest is EntryBaseChain{
}

Class of EntryBaseChain is TestEntryInheritedInit{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	Function is testInheritedEntryConstructed(){
		Assert:areEqualInt(1, SpecUnitTest:entryStamped:length());
	}

	Function is testSelfIdentitySurvivesTheChain(){
		Assert:areEqualString('TestEntryInheritedInit', self:name());
	}
}
