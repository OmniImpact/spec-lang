#! Token port check: enum dispatch surface, accessors, the keyword
#! classification, and the diagnostic template.

Class of SpecUnitTest is TestSpecToken{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'compiler', 'lexer', TokenKind],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'compiler', 'lexer', Operator],
		['base', 'compiler', 'lexer', Token]
	];

	Function is testAccessorsRoundTrip(){
		local Token is sym: Token:init(kind: TokenKind:SYMBOL, value: '{', line: 3, col: 14);
		Assert:isTrue(sym:getTokenKind() == TokenKind:SYMBOL);
		Assert:areEqualString('{', sym:getValue());
		Assert:areEqualInt(3, sym:getLine());
		Assert:areEqualInt(14, sym:getCol());
	}

	Function is testNonKeywordCarriesNone(){
		local Token is sym: Token:init(kind: TokenKind:SYMBOL, value: '{', line: 3, col: 14);
		Assert:isTrue(sym:getKeyword() == Keyword:NONE);
	}

	Function is testKeywordClassificationRoundTrip(){
		local Token is kw: Token:init(kind: TokenKind:KEYWORD, value: 'local', line: 1, col: 1);
		kw:setKeyword(kw: Keyword:LOCAL);
		Assert:isTrue(kw:getKeyword() == Keyword:LOCAL);
	}

	Function is testOperatorClassificationRoundTrip(){
		local Token is sym: Token:init(kind: TokenKind:SYMBOL, value: '{', line: 3, col: 14);
		local Token is op: Token:init(kind: TokenKind:SYMBOL, value: '==', line: 2, col: 7);
		op:setOperator(op: Operator:EQ);
		Assert:isTrue(op:getOperator() == Operator:EQ);
		Assert:isTrue(sym:getOperator() == Operator:NONE);
	}

	Function is testDescribeTemplate(){
		local Token is sym: Token:init(kind: TokenKind:SYMBOL, value: '{', line: 3, col: 14);
		Assert:areEqualString("SYMBOL '{' at 3:14", sym:describe());
	}
}
