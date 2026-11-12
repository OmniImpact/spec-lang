#! SpecUnit sweep (from import_wall_test.spec): the import walls' grant
#! surface. Each parent carries one as-import; the child declares none —
#! the MI lattice merges BOTH parents' grants bare (functions callable,
#! the nested-class type referencing), and constructing the parent's
#! imported class's nested type passes §I.6 through the inherited grant.
#! The rejection surfaces live in the negatives: N24 (the local member),
#! N26 (the field wall), N27 (the inner's import leak), the transitive
#! pair (no re-export), N3 (the same-level collision).

Class of SpecUnitTest, WallParentA, WallParentB is TestImportWall{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	## The MI merge: parent A's imported function, callable bare.
	Function is testParentAImportBare(){
		Assert:areEqualInt(6, triple(2));
	}

	## Parent B's imported function, callable bare beside it.
	Function is testParentBImportBare(){
		Assert:areEqualInt(8, quad(2));
	}

	## The inherited-import gating: the nested-class type from the
	## parent's grant constructs and dispatches (§I.6 via the lattice).
	Function is testInheritedImportGating(){
		local LibA:Helper is h: LibA:Helper:init();
		Assert:areEqualInt(1, h:value());
	}
}

## Parent A: imports LibA — triple() and the LibA:Helper type ride the grant.
Class is WallParentA{
	replace Array of Array of String is using: [
		['wallprobe', 'liba', as LibA()]
	];

	replace Function is init(){
	}
}

## Parent B: imports LibB — quad() rides the grant.
Class is WallParentB{
	replace Array of Array of String is using: [
		['wallprobe', 'libb', as LibB()]
	];

	replace Function is init(){
	}
}
