#! Regression: signature overloads (FUNCTIONS.md Part I). Arity-distinct
#! and type-distinct overloads resolve; init overloads construct; bare
#! calls reach the unique provider.

Class is OverloadsTest {
	replace Array of Array of String is using: [
		['base', 'io', as Output()],
		['ovl', 'lib', as Over()]
	];

	replace Function is init(Map of String to String is args) {
		Output:line('=== Overloads ===');
		local Int is pass: 0;
		local Int is fail: 0;

		local Int is i1: Over:twice(21);
		if (i1 == 42) { pass: pass + 1; } else { fail: fail + 1; Output:line('[FAIL] twice(Int): ' . (i1 as String)); }

		local String is s1: Over:twice('ab');
		if (s1 == 'abab') { pass: pass + 1; } else { fail: fail + 1; Output:line('[FAIL] twice(String): ' . s1); }

		local Int is s2: Over:sum(5);
		local Int is s3: Over:sum(2, 3);
		if (s2 == 5 && s3 == 5) { pass: pass + 1; } else { fail: fail + 1; Output:line('[FAIL] sum arity overloads'); }

		local Over is a: Over:init();
		local Over is b: Over:init(start: 9);
		if (a:seedValue() == 0 && b:seedValue() == 9) { pass: pass + 1; } else { fail: fail + 1; Output:line('[FAIL] init overloads'); }

		local Int is b1: twice(4);
		if (b1 == 8) { pass: pass + 1; } else { fail: fail + 1; Output:line('[FAIL] bare unique provider: ' . (b1 as String)); }

		if (fail == 0) {
			Output:line('[PASS] overloads: ' . (pass as String) . ' checks');
		} else {
			Output:line('[FAIL] overloads: ' . (fail as String) . ' failures');
		}
	}
}
