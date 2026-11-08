#! Regression: Conditional (FUNCTIONS.md Part II) — every conditional
#! shape composed from the floor's single primitive. Statement forms
#! inline to zero-allocation C; branches return from the method
#! (guard clauses work).

Class is ConditionalTest {
	replace Array of Array of String is using: [
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	# A guard clause: the branch returns from the method.
	Function of String is guard(Int is v){
		Conditional:branch(check: { v < 0; }, then: {
			return 'negative';
		});
		return 'non-negative';
	}

	replace Function is init(Map of String to String is args) {
		Output:line('=== Conditional ===');
		local Int is pass: 0;
		local Int is fail: 0;

		# 2-arg primitive.
		local Int is hits: 0;
		Conditional:branch(check: { 1 > 0; }, then: {
			hits: hits + 1;
		});
		Conditional:branch(check: { 1 > 2; }, then: {
			hits: hits + 10;
		});
		Conditional:branch(check: { hits == 1 }, then: {
 pass: pass + 1;
		}, otherwise: {
 fail: fail + 1; Output:line('[FAIL] 2-arg primitive');
		});

		# 3-arg composed: else = not if.
		local String is which: '';
		Conditional:branch(check: { 5 > 3; }, then: {
			which: 'then';
		}, otherwise: {
			which: 'else';
		});
		Conditional:branch(check: { 1 > 3; }, then: {
			which: which . '!';
		}, otherwise: {
			which: which . '2';
		});
		Conditional:branch(check: { which == 'then2' }, then: {
 pass: pass + 1;
		}, otherwise: {
 fail: fail + 1; Output:line('[FAIL] 3-arg composed: ' . which);
		});

		# 4-arg with finally.
		local String is order: '';
		Conditional:branch(check: { true; }, then: {
			order: 't';
		}, otherwise: {
			order: 'e';
		}, finally: {
			order: order . 'f';
		});
		Conditional:branch(check: { order == 'tf' }, then: {
 pass: pass + 1;
		}, otherwise: {
 fail: fail + 1; Output:line('[FAIL] 4-arg finally: ' . order);
		});

		# Guard clause: the branch returns from the method.
		local String is g1: guard(5);
		local String is g2: guard(-1);
		Conditional:branch(check: { g1 == 'non-negative' && g2 == 'negative' }, then: {
 pass: pass + 1;
		}, otherwise: {
 fail: fail + 1; Output:line('[FAIL] guard clause: ' . g1 . ' / ' . g2);
		});

		# Nested conditionals.
		local String is nest: '';
		Conditional:branch(check: { 1 < 2; }, then: {
			Conditional:branch(check: { 2 < 3; }, then: {
				nest: 'deep';
			});
		});
		Conditional:branch(check: { nest == 'deep' }, then: {
 pass: pass + 1;
		}, otherwise: {
 fail: fail + 1; Output:line('[FAIL] nesting');
		});

		# Bare calls through the unique provider.
		local Int is bareHits: 0;
		branch(check: { true; }, then: {
			bareHits: bareHits + 1;
		});
		Conditional:branch(check: { bareHits == 1 }, then: {
 pass: pass + 1;
		}, otherwise: {
 fail: fail + 1; Output:line('[FAIL] bare call');
		});

		# Value-yielding branch: the if-expression form (FUNCTIONS.md
		# Part II). Both branches end in an expression; the yields unify.
		local String is picked: Conditional:branch(check: { 3 > 2 }, then: { 'big' }, otherwise: { 'small' });
		local String is picked2: Conditional:branch(check: { 3 > 9 }, then: { picked . '!' }, otherwise: { 'tiny' });
		Conditional:branch(check: { picked == 'big' && picked2 == 'tiny' }, then: {
 pass: pass + 1;
		}, otherwise: {
 fail: fail + 1; Output:line('[FAIL] value yield: ' . picked . ' / ' . picked2);
		});

		# The scoped region fills the open then-slot: the body becomes the
		# branch's then-closure (FUNCTIONS.md §as).
		local Int is scopedHits: 0;
		as: Conditional:branch(check: { 2 > 1; });
			scopedHits: scopedHits + 1;
		Conditional:branch(check: { scopedHits == 1 }, then: {
 pass: pass + 1;
		}, otherwise: {
 fail: fail + 1; Output:line('[FAIL] scoped open slot');
		});

		Conditional:branch(check: { fail == 0 }, then: {
			Output:line('[PASS] conditional: ' . (pass as String) . ' checks');
		}, otherwise: {
			Output:line('[FAIL] conditional: ' . (fail as String) . ' failures');
		});
	}
}
