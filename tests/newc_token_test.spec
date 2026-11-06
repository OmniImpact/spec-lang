#! Token port check: enum dispatch surface, accessors, and the diagnostic
#! template — the first pipeline module of the new tree.

Class is NewcTokenTest{

	replace Array of Array of String is using: [
		['newc', 'lexer', TokenKind],
		['newc', 'lexer', Token],
		['base', 'io', Output]
	];

	replace Function is init(Map of String to String is args){
		output:line('=== New-Tree Token Test ===');
		local Int is failures: 0;

		local Token is sym: Token:init(kind: TokenKind:SYMBOL, value: '{', line: 3, col: 14);
		if (sym:getTokenKind() == TokenKind:SYMBOL && sym:getValue() == '{' && sym:getLine() == 3 && sym:getCol() == 14) {
			output:line('[PASS] accessors round-trip');
		} else {
			output:line('[FAIL] accessors round-trip');
			failures: failures + 1;
		}

		# Enum dispatch with when — the style contract's replacement for
		# string-tag comparisons.
		local String is tag: '';
		when (sym:getTokenKind()) {
			is SYMBOL: { tag: 'symbol'; }
			is IDENTIFIER: { tag: 'identifier'; }
			else: { tag: 'other'; }
		}
		if (tag == 'symbol') {
			output:line('[PASS] when-dispatch on TokenKind');
		} else {
			output:line('[FAIL] when-dispatch on TokenKind');
			failures: failures + 1;
		}

		if (sym:describe() == "SYMBOL '{' at 3:14") {
			output:line('[PASS] describe template');
		} else {
			output:line('[FAIL] describe template: ' . sym:describe());
			failures: failures + 1;
		}

		if (failures == 0) {
			output:line('[PASS] new-tree token test complete');
		} else {
			output:line('[FAIL] new-tree token test: ' . (failures as String) . ' failures');
		}
	}
}
