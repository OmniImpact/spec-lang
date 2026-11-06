#! New-tree bootstrap check: the frozen toolchain compiles newc/ sources
#! through array-form package resolution (scan roots), and the new tree's
#! utility classes construct-and-call over the compiled String surface.

Class is NewcCharsTest{

	replace Array of Array of String is using: [
		['newc', 'util', Chars],
		['base', 'io', Output]
	];

	replace Function is init(Map of String to String is args){
		output:line('=== New-Tree Chars Test ===');
		local Chars is ch: Chars:init();
		local Int is failures: 0;

		if (ch:isIdentifierStart(ch: '_') && ch:isIdentifierStart(ch: 'a') && !ch:isIdentifierStart(ch: '7')) {
			output:line('[PASS] identifier start classification');
		} else {
			output:line('[FAIL] identifier start classification');
			failures: failures + 1;
		}

		if (ch:isIdentifierContinue(ch: '7') && ch:isIdentifierContinue(ch: '_') && !ch:isIdentifierContinue(ch: '-')) {
			output:line('[PASS] identifier continue classification');
		} else {
			output:line('[FAIL] identifier continue classification');
			failures: failures + 1;
		}

		if (ch:isUpper(ch: 'A') && !ch:isUpper(ch: 'a')) {
			output:line('[PASS] uppercase classification');
		} else {
			output:line('[FAIL] uppercase classification');
			failures: failures + 1;
		}

		if (failures == 0) {
			output:line('[PASS] new-tree chars test complete');
		} else {
			output:line('[FAIL] new-tree chars test: ' . (failures as String) . ' failures');
		}
	}
}
