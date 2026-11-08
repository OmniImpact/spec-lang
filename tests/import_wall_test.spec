#! FUNCTIONS.md Part IV IV.6: the import walls' grant surface. Each
#! parent carries one as-import; the child declares none — the MI
#! lattice merges BOTH parents' grants bare (functions callable, the
#! nested-class types referencing), and constructing the parent's
#! imported class's nested type passes §I.6 through the inherited grant.
#! The rejection surfaces live in the negatives: N24 (the local member),
#! N26 (the field wall), N27 (the inner's import leak), the transitive
#! pair (no re-export), N3 (the same-level collision).

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

## The child: no using of its own beyond Conditional — both parents'
## imports merge bare through the lattice.
Class of WallParentA, WallParentB is ImportWallTest{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		local Int is pass: 0;
		local Int is fail: 0;

		# The MI merge: parent A's imported function, callable bare.
		if(check: { triple(2) == 6 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			line('[FAIL] parent A import bare: ' . (triple(2) as String));
		});

		# Parent B's imported function, callable bare beside it.
		if(check: { quad(2) == 8 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			line('[FAIL] parent B import bare: ' . (quad(2) as String));
		});

		# The inherited-import gating: the nested-class type from the
		# parent's grant constructs and dispatches (§I.6 via the lattice).
		local LibA:Helper is h: LibA:Helper:init();
		if(check: { h:value() == 1 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			line('[FAIL] inherited-import gating: ' . (h:value() as String));
		});

		if(check: { fail == 0 }, then: {
			line('[PASS] import walls: ' . (pass as String) . ' checks');
		}, else: {
			line('[FAIL] import walls: ' . (fail as String) . ' failures');
		});
	}
}
