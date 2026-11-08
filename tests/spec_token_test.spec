#! Token port check: enum dispatch surface, accessors, the keyword
#! classification, and the diagnostic template.

Class is SpecTokenTest{

	replace Array of Array of String is using: [
		['base', 'compiler', 'lexer', TokenKind],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'compiler', 'lexer', Operator],
		['base', 'compiler', 'lexer', Token],
		['base', 'io', Output],
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Spec Token Test ===');
		local Int is failures: 0;

		local Token is sym: Token:init(kind: TokenKind:SYMBOL, value: '{', line: 3, col: 14);
		if (sym:getTokenKind() == TokenKind:SYMBOL && sym:getValue() == '{' && sym:getLine() == 3 && sym:getCol() == 14) {
			Output:line('[PASS] accessors round-trip');
		} else {
			Output:line('[FAIL] accessors round-trip');
			failures: failures + 1;
		}

		if (sym:getKeyword() == Keyword:NONE) {
			Output:line('[PASS] non-keyword carries NONE');
		} else {
			Output:line('[FAIL] non-keyword keyword classification');
			failures: failures + 1;
		}

		local Token is kw: Token:init(kind: TokenKind:KEYWORD, value: 'local', line: 1, col: 1);
		kw:setKeyword(kw: Keyword:LOCAL);
		if (kw:getKeyword() == Keyword:LOCAL) {
			Output:line('[PASS] keyword classification round-trip');
		} else {
			Output:line('[FAIL] keyword classification round-trip');
			failures: failures + 1;
		}

		local Token is op: Token:init(kind: TokenKind:SYMBOL, value: '==', line: 2, col: 7);
		op:setOperator(op: Operator:EQ);
		if (op:getOperator() == Operator:EQ && sym:getOperator() == Operator:NONE) {
			Output:line('[PASS] operator classification round-trip');
		} else {
			Output:line('[FAIL] operator classification round-trip');
			failures: failures + 1;
		}

		if (sym:describe() == "SYMBOL '{' at 3:14") {
			Output:line('[PASS] describe template');
		} else {
			Output:line('[FAIL] describe template: ' . sym:describe());
			failures: failures + 1;
		}

		if (failures == 0) {
			Output:line('[PASS] spec token test complete');
		} else {
			Output:line('[FAIL] spec token test: ' . (failures as String) . ' failures');
		}
	}
}
