#! Regression: signature overloads (Part I). Arity-distinct
#! and type-distinct overloads resolve; init overloads construct; bare
#! calls reach the unique provider.

Class is OverloadsTest {
	replace Array of Array of String is using: [
		['base', 'sys', as Output()],
		# IV.6 strictness: the plain form grants construction; the as-form
		# grants the bare function calls (Over:twice).
		['ovl', 'lib', Over],
		['ovl', 'lib', as Over()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args) {
		Output:line('=== Overloads ===');
		local Int is pass: 0;
		local Int is fail: 0;

		local Int is i1: Over:twice(21);
		Conditional:if(check: { i1 == 42 }, then: {
 pass: pass + 1;
		}, else: {
 fail: fail + 1; Output:line('[FAIL] twice(Int): ' . (i1 as String));
		});

		local String is s1: Over:twice('ab');
		Conditional:if(check: { s1 == 'abab' }, then: {
 pass: pass + 1;
		}, else: {
 fail: fail + 1; Output:line('[FAIL] twice(String): ' . s1);
		});

		local Int is s2: Over:sum(5);
		local Int is s3: Over:sum(2, 3);
		Conditional:if(check: { s2 == 5 && s3 == 5 }, then: {
 pass: pass + 1;
		}, else: {
 fail: fail + 1; Output:line('[FAIL] sum arity overloads');
		});

		local Over is a: Over:init();
		local Over is b: Over:init(start: 9);
		Conditional:if(check: { a:seedValue() == 0 && b:seedValue() == 9 }, then: {
 pass: pass + 1;
		}, else: {
 fail: fail + 1; Output:line('[FAIL] init overloads');
		});

		local Int is b1: twice(4);
		Conditional:if(check: { b1 == 8 }, then: {
 pass: pass + 1;
		}, else: {
 fail: fail + 1; Output:line('[FAIL] bare unique provider: ' . (b1 as String));
		});

		Conditional:if(check: { fail == 0 }, then: {
			Output:line('[PASS] overloads: ' . (pass as String) . ' checks');
		}, else: {
			Output:line('[FAIL] overloads: ' . (fail as String) . ' failures');
		});
	}
}
