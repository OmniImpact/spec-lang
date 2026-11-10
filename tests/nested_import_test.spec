#! IV.2c (Part IV): the qualified nested-class references
#! across two as-imported providers. Same-named inner classes under
#! different outers coexist — each qualified reference picks its class,
#! the C symbols and types stay distinct (LibA_Helper / LibB_Helper).
#! The as-imported functions call bare (`if`, `line`).

Class is NestedImportTest{
	replace Array of Array of String is using: [
		['wallprobe', 'liba', as LibA()],
		['wallprobe', 'libb', as LibB()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Output()]
	];

	replace Function is init(Map of String to String is args){
		local Int is pass: 0;
		local Int is fail: 0;

		# IV.2c: the qualified nested-class references — with both
		# providers imported, the bare form is ambiguous (the N25
		# negative pins the error) and the qualified form is the escape.
		# Two same-named inner classes under different outers coexist:
		# the C symbols and types stay distinct.
		local LibA:Helper is h: LibA:Helper:init();
		if(check: { h:value() == 1 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			line('[FAIL] qualified nested reference: ' . (h:value() as String));
		});

		local LibB:Helper is h2: LibB:Helper:init();
		if(check: { h2:value() == 2 }, then: {
			pass: pass + 1;
		}, else: {
			fail: fail + 1;
			line('[FAIL] second provider qualified reference: ' . (h2:value() as String));
		});

		if(check: { fail == 0 }, then: {
			line('[PASS] nested imports: ' . (pass as String) . ' checks');
		}, else: {
			line('[FAIL] nested imports: ' . (fail as String) . ' failures');
		});
	}
}
