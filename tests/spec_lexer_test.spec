#! New-tree Lexer port check: every token family scanned by the new
#! lexer under the frozen toolchain — numbers (bases, separators), strings
#! (all families), comments, line/col tracking, and EOF.

Class is SpecLexerTest{

	replace Array of Array of String is using: [
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'lexer', TokenKind],
		['base', 'compiler', 'lexer', Token],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'io', Output],
		['base', 'io', as Output()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Spec Lexer Test ===');
		local Int is failures: 0;

		local String is src: 'local Int is n: 0xff + 1_000;' . "\n" . '# a comment
local String is s: \'it\\\'s\';
local String is r: "raw \\n stays \{\{x\}\}";
local String is h: ' . "'''\nheredoc\n'''" . ';';
		local Lexer is lx: Lexer:init(source: src);
		local Array of Token is toks: lx:tokenize();

		if (!lx:hasErrors() && toks:length() == 31) {
			Output:line('[PASS] clean scan, expected token count');
		} else {
			Output:line('[FAIL] scan errors or token count: ' . (toks:length() as String));
			failures: failures + 1;
		}

		# Base-prefixed numbers normalize to decimal; separators strip.
		local Token is hex: toks:get(index: 5);
		local Token is sep: toks:get(index: 7);
		if (hex:getValue() == '255' && hex:getTokenKind() == TokenKind:INT && sep:getValue() == '1000') {
			Output:line('[PASS] number normalization');
		} else {
			Output:line('[FAIL] number normalization');
			failures: failures + 1;
		}

		# Families: single-quote minimal escape, fancy raw content, raw heredoc.
		local Token is sq: toks:get(index: 14);
		local Token is fq: toks:get(index: 21);
		local Token is hd: toks:get(index: 28);
		if (sq:getValue() == 'it\'s' && sq:getTokenKind() == TokenKind:STRING) {
			Output:line('[PASS] single-quote minimal escape');
		} else {
			Output:line('[FAIL] single-quote minimal escape');
			failures: failures + 1;
		}
		if (fq:getValue() == "raw \\n stays \\{\\{x\\}\\}" && fq:getTokenKind() == TokenKind:TEMPLATESTRING) {
			Output:line('[PASS] fancy string carries raw content incl. escapes');
		} else {
			Output:line('[FAIL] fancy string raw content');
			failures: failures + 1;
		}
		if (hd:getValue() == "heredoc\n" && hd:getTokenKind() == TokenKind:RAWSTRING) {
			Output:line('[PASS] raw heredoc with delimiter-newline strip');
		} else {
			Output:line('[FAIL] raw heredoc content');
			failures: failures + 1;
		}

		# Reserved words carry their Keyword classification for enum dispatch.
		local Token is kwTok: toks:get(index: 0);
		if (kwTok:getKeyword() == Keyword:LOCAL) {
			Output:line('[PASS] keyword classification on scanned token');
		} else {
			Output:line('[FAIL] keyword classification on scanned token');
			failures: failures + 1;
		}

		# Line/col tracking across the comment line and the multi-line heredoc.
		local Token is afterComment: toks:get(index: 9);
		local Token is end: toks:get(index: 30);
		if (afterComment:getLine() == 3 && end:getTokenKind() == TokenKind:EOF && end:getLine() == 7) {
			Output:line('[PASS] line tracking across comment and heredoc');
		} else {
			Output:line('[FAIL] line tracking');
			failures: failures + 1;
		}

		# Errors carry provenance: message plus a trace frame at the scan
		# position. The wording's template hole must be SUBSTITUTED (the
		# fancy-family contract) and the frame names come from Reflection,
		# so they always match the real enclosing class/method.
		local Lexer is bad: Lexer:init(source: "``` unterminated");
		local Array of Token is dead: bad:tokenize();
		local Error is first: bad:getErrors():get(index: 0);
		local String is rendered: first:toString();
		if (bad:hasErrors() && rendered:contains(needle: 'missing closing ```') && rendered:contains(needle: 'at Lexer:addError')) {
			Output:line('[PASS] lexical errors carry substituted wording and reflection provenance');
		} else {
			Output:line('[FAIL] lexical error provenance: ' . rendered);
			failures: failures + 1;
		}

		if (failures == 0) {
			Output:line('[PASS] spec lexer test complete');
		} else {
			Output:line('[FAIL] spec lexer test: ' . (failures as String) . ' failures');
		}
	}
}
