#! Regression: signature overloads (FUNCTIONS.md Part I). Arity-distinct
#! and type-distinct overloads resolve; init overloads construct; bare
#! calls reach the unique provider.

Class is OverloadsTest {
	replace Array of Array of String is using: [
		['base', 'io', as Output()],
		['ovl', 'lib', as Over()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args) {
		Output:line('=== Overloads ===');
		local Int is pass: 0;
		local Int is fail: 0;

		local Int is i1: Over:twice(21);
		Conditional:branch(check: { i1 == 42 }, then: {
 pass: pass + 1;
		}, otherwise: {
 fail: fail + 1; Output:line('[FAIL] twice(Int): ' . (i1 as String));
		});

		local String is s1: Over:twice('ab');
		Conditional:branch(check: { s1 == 'abab' }, then: {
 pass: pass + 1;
		}, otherwise: {
 fail: fail + 1; Output:line('[FAIL] twice(String): ' . s1);
		});

		local Int is s2: Over:sum(5);
		local Int is s3: Over:sum(2, 3);
		Conditional:branch(check: { s2 == 5 && s3 == 5 }, then: {
 pass: pass + 1;
		}, otherwise: {
 fail: fail + 1; Output:line('[FAIL] sum arity overloads');
		});

		local Over is a: Over:init();
		local Over is b: Over:init(start: 9);
		Conditional:branch(check: { a:seedValue() == 0 && b:seedValue() == 9 }, then: {
 pass: pass + 1;
		}, otherwise: {
 fail: fail + 1; Output:line('[FAIL] init overloads');
		});

		local Int is b1: twice(4);
		Conditional:branch(check: { b1 == 8 }, then: {
 pass: pass + 1;
		}, otherwise: {
 fail: fail + 1; Output:line('[FAIL] bare unique provider: ' . (b1 as String));
		});

		Conditional:branch(check: { fail == 0 }, then: {
			Output:line('[PASS] overloads: ' . (pass as String) . ' checks');
		}, otherwise: {
			Output:line('[FAIL] overloads: ' . (fail as String) . ' failures');
		});
	}
}
