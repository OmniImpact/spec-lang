#! SpecUnit sweep (from nested_bare_import_test.spec): IV.2c phase 3
#! (Part IV) — the as-import of a class brings its nested classes into
#! the importer's scope. With exactly one provider the bare nested-class
#! reference resolves through the per-scope map — the type rewrites to
#! its qualified identity and the C symbols and types follow
#! (LibA_Helper).

Class of SpecUnitTest is TestNestedBareImport{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['wallprobe', 'liba', as LibA()]
	];

	## The bare nested-class reference resolves to the imported
	## class's nested Helper.
	Function is testBareNestedReference(){
		local Helper is h: LibA:Helper:init();
		Assert:areEqualInt(1, h:value());
	}

	## The qualified form resolves the same member.
	Function is testQualifiedNestedReference(){
		local LibA:Helper is hq: LibA:Helper:init();
		Assert:areEqualInt(1, hq:value());
	}
}
