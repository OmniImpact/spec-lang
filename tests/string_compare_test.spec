#! Regression: D5 hardening — relational operators on String compare
#! lexicographically through the floor, never by pointer. Mixed-type
#! relational comparisons are compile errors.

Class is StringCompareTest {
	replace Array of Array of String is using: [
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args) {
		Output:line('=== String Comparison ===');
		local String is a: 'apple';
		local String is b: 'banana';
		local String is a2: 'applf';
		local Int is pass: 0;
		local Int is fail: 0;

		Conditional:if(check: { a < b && b > a }, then: {
 pass: pass + 1;
		}, else: {
 fail: fail + 1; Output:line('[FAIL] ordering');
		});
		Conditional:if(check: { a <= a && a >= a }, then: {
 pass: pass + 1;
		}, else: {
 fail: fail + 1; Output:line('[FAIL] reflexivity');
		});
		Conditional:if(check: { a < a2 && a2 > a }, then: {
 pass: pass + 1;
		}, else: {
 fail: fail + 1; Output:line('[FAIL] prefix ordering: apple < applf');
		});
		Conditional:if(check: { ('aa' > 'ab') == false }, then: {
 pass: pass + 1;
		}, else: {
 fail: fail + 1; Output:line('[FAIL] aa > ab');
		});

		Conditional:if(check: { fail == 0 }, then: {
			Output:line('[PASS] string comparison: ' . (pass as String) . ' checks');
		}, else: {
			Output:line('[FAIL] string comparison: ' . (fail as String) . ' failures');
		});
	}
}
