#! Token port check: enum dispatch surface, accessors, the keyword
#! classification, and the diagnostic template.

Class is SpecTokenTest{

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'lexer', TokenKind],
		['spec', 'base', 'compiler', 'lexer', Keyword],
		['spec', 'base', 'compiler', 'lexer', Token],
		['lib', 'base', 'io', Output]
	];

	replace Function is init(Map of String to String is args){
		output:line('=== Spec Token Test ===');
		local Int is failures: 0;

		local Token is sym: Token:init(kind: TokenKind:SYMBOL, value: '{', line: 3, col: 14);
		if (sym:getTokenKind() == TokenKind:SYMBOL && sym:getValue() == '{' && sym:getLine() == 3 && sym:getCol() == 14) {
			output:line('[PASS] accessors round-trip');
		} else {
			output:line('[FAIL] accessors round-trip');
			failures: failures + 1;
		}

		if (sym:getKeyword() == Keyword:NONE) {
			output:line('[PASS] non-keyword carries NONE');
		} else {
			output:line('[FAIL] non-keyword keyword classification');
			failures: failures + 1;
		}

		local Token is kw: Token:init(kind: TokenKind:KEYWORD, value: 'local', line: 1, col: 1);
		kw:setKeyword(kw: Keyword:LOCAL);
		if (kw:getKeyword() == Keyword:LOCAL) {
			output:line('[PASS] keyword classification round-trip');
		} else {
			output:line('[FAIL] keyword classification round-trip');
			failures: failures + 1;
		}

		if (sym:describe() == "SYMBOL '{' at 3:14") {
			output:line('[PASS] describe template');
		} else {
			output:line('[FAIL] describe template: ' . sym:describe());
			failures: failures + 1;
		}

		if (failures == 0) {
			output:line('[PASS] spec token test complete');
		} else {
			output:line('[FAIL] spec token test: ' . (failures as String) . ' failures');
		}
	}
}
