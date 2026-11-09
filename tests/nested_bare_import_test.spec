#! IV.2c phase 3 (Part IV): the as-import of a class brings
#! its nested classes into the importer's scope. With exactly one
#! provider the bare nested-class reference resolves through the
#! per-scope map — the type rewrites to its qualified identity and the
#! C symbols and types follow (LibA_Helper). The as-imported functions
#! call bare (`if`, `line`).

Class is NestedBareImportTest{
	replace Array of Array of String is using: [
		['wallprobe', 'liba', as LibA()],
		['base', 'sys', as Conditional()],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		local Int is pass: 0;
		local Int is fail: 0;

		# The bare nested-class reference resolves to the imported
		# class's nested Helper.
		local Helper is h: LibA:Helper:init();
		if(check: { h:value() == 1 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			line('[FAIL] bare nested reference: ' . (h:value() as String));
		});

		# The qualified form resolves the same member.
		local LibA:Helper is hq: LibA:Helper:init();
		if(check: { hq:value() == 1 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			line('[FAIL] qualified nested reference: ' . (hq:value() as String));
		});

		if(check: { fail == 0 }, then: {
			line('[PASS] nested imports: ' . (pass as String) . ' checks');
		}, else: {
			line('[FAIL] nested imports: ' . (fail as String) . ' failures');
		});
	}
}
