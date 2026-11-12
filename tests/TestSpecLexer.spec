#! SpecUnit sweep (from spec_lexer_test.spec): every token family scanned
#! by the new lexer under the frozen toolchain — numbers (bases,
#! separators), strings (all families), comments, line/col tracking,
#! EOF, and lexical error provenance.

Class of SpecUnitTest is TestSpecLexer{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'lexer', TokenKind],
		['base', 'compiler', 'lexer', Token],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'sys', Output],
		['base', 'sys', as Output()],
		['base', 'compiler', Error],
		['base', 'sys', as Conditional()]
	];

	## The frozen multi-family scan fixture: base-prefixed numbers with
	## separators, every string family, a comment line, and a heredoc.
	Function of String is fixtureSource(){
		return 'local Int is n: 0xff + 1_000;' . "\n" . '# a comment
local String is s: \'it\\\'s\';
local String is r: "raw \\n stays \{\{x\}\}";
local String is h: ' . "'''\nheredoc\n'''" . ';';
	}

	Function of Array of Token is scanFixture(){
		local Lexer is lx: Lexer:init(source: self:fixtureSource());
		return lx:tokenize();
	}

	Function is testCleanScanAndCount(){
		local Lexer is lx: Lexer:init(source: self:fixtureSource());
		local Array of Token is toks: lx:tokenize();
		Assert:isTrue(!lx:hasErrors());
		Assert:areEqualInt(31, toks:length());
	}

	# Base-prefixed numbers normalize to decimal; separators strip.
	Function is testNumberNormalization(){
		local Array of Token is toks: self:scanFixture();
		local Token is hex: toks:get(index: 5);
		local Token is sep: toks:get(index: 7);
		Assert:areEqualString('255', hex:getValue());
		Assert:isTrue(hex:getTokenKind() == TokenKind:INT);
		Assert:areEqualString('1000', sep:getValue());
	}

	# Families: single-quote minimal escape, fancy raw content, raw heredoc.
	Function is testStringFamilies(){
		local Array of Token is toks: self:scanFixture();
		local Token is sq: toks:get(index: 14);
		local Token is fq: toks:get(index: 21);
		local Token is hd: toks:get(index: 28);
		Assert:isTrue(sq:getTokenKind() == TokenKind:STRING);
		Assert:areEqualString('it\'s', sq:getValue());
		Assert:isTrue(fq:getTokenKind() == TokenKind:TEMPLATESTRING);
		Assert:areEqualString("raw \\n stays \\{\\{x\\}\\}", fq:getValue());
		Assert:isTrue(hd:getTokenKind() == TokenKind:RAWSTRING);
		Assert:areEqualString("heredoc\n", hd:getValue());
	}

	# Reserved words carry their Keyword classification for enum dispatch.
	Function is testKeywordClassification(){
		local Array of Token is toks: self:scanFixture();
		local Token is kwTok: toks:get(index: 0);
		Assert:isTrue(kwTok:getKeyword() == Keyword:LOCAL);
	}

	# Line/col tracking across the comment line and the multi-line heredoc.
	Function is testLineTracking(){
		local Array of Token is toks: self:scanFixture();
		local Token is afterComment: toks:get(index: 9);
		local Token is end: toks:get(index: 30);
		Assert:areEqualInt(3, afterComment:getLine());
		Assert:isTrue(end:getTokenKind() == TokenKind:EOF);
		Assert:areEqualInt(7, end:getLine());
	}

	# Errors carry provenance: message plus a trace frame at the scan
	# position. The wording's template hole must be SUBSTITUTED (the
	# fancy-family contract) and the frame names come from Reflection,
	# so they always match the real enclosing class/method.
	Function is testErrorProvenance(){
		local Lexer is bad: Lexer:init(source: "``` unterminated");
		local Array of Token is dead: bad:tokenize();
		local Error is first: bad:getErrors():get(index: 0);
		local String is rendered: first:toString();
		Assert:isTrue(bad:hasErrors());
		Assert:isTrue(rendered:contains(needle: 'missing closing ```'));
		Assert:isTrue(rendered:contains(needle: 'at Lexer:addError'));
	}
}
