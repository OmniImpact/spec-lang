#! SpecUnit sweep (from nested_import_test.spec): IV.2c (Part IV) — the
#! qualified nested-class references across two as-imported providers.
#! Same-named inner classes under different outers coexist — each
#! qualified reference picks its class, the C symbols and types stay
#! distinct (LibA_Helper / LibB_Helper).

Class of SpecUnitTest is TestNestedImport{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['wallprobe', 'liba', as LibA()],
		['wallprobe', 'libb', as LibB()]
	];

	## IV.2c: with both providers imported, the bare form is ambiguous
	## (the N25 negative pins the error) and the qualified form is the
	## escape. Two same-named inner classes under different outers
	## coexist: the C symbols and types stay distinct.
	Function is testQualifiedNestedReference(){
		local LibA:Helper is h: LibA:Helper:init();
		Assert:areEqualInt(1, h:value());
	}

	## The second provider's same-named inner class picks ITS class.
	Function is testSecondProviderQualifiedReference(){
		local LibB:Helper is h2: LibB:Helper:init();
		Assert:areEqualInt(2, h2:value());
	}
}
