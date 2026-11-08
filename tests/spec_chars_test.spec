#! New-tree bootstrap check: the frozen toolchain compiles spec/ sources
#! through array-form package resolution, and the compiler's utility
#! classes construct-and-call over the compiled String surface.

Class is SpecCharsTest{

	replace Array of Array of String is using: [
		['base', 'compiler', 'utils', Chars],
		['base', 'io', Output],
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Spec Chars Test ===');
		local Chars is ch: Chars:init();
		local Int is failures: 0;

		Conditional:branch(check: { ch:isIdentifierStart(ch: '_') && ch:isIdentifierStart(ch: 'a') && !ch:isIdentifierStart(ch: '7') }, then: {
			Output:line('[PASS] identifier start classification');
		}, otherwise: {
			Output:line('[FAIL] identifier start classification');
			failures: failures + 1;
		});

		Conditional:branch(check: { ch:isIdentifierContinue(ch: '7') && ch:isIdentifierContinue(ch: '_') && !ch:isIdentifierContinue(ch: '-') }, then: {
			Output:line('[PASS] identifier continue classification');
		}, otherwise: {
			Output:line('[FAIL] identifier continue classification');
			failures: failures + 1;
		});

		Conditional:branch(check: { ch:isUpper(ch: 'A') && !ch:isUpper(ch: 'a') }, then: {
			Output:line('[PASS] uppercase classification');
		}, otherwise: {
			Output:line('[FAIL] uppercase classification');
			failures: failures + 1;
		});

		Conditional:branch(check: { failures == 0 }, then: {
			Output:line('[PASS] spec chars test complete');
		}, otherwise: {
			Output:line('[FAIL] spec chars test: ' . (failures as String) . ' failures');
		});
	}
}
