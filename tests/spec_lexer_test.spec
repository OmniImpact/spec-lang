#! New-tree Lexer port check: every token family scanned by the new
#! lexer under the frozen toolchain — numbers (bases, separators), strings
#! (all families), comments, line/col tracking, and EOF.

Class is SpecLexerTest{

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'lexer', Lexer],
		['spec', 'base', 'compiler', 'lexer', TokenKind],
		['spec', 'base', 'compiler', 'lexer', Token],
		['spec', 'base', 'compiler', 'lexer', Keyword],
		['lib', 'base', 'io', Output]
	];

	replace Function is init(Map of String to String is args){
		output:line('=== Spec Lexer Test ===');
		local Int is failures: 0;

		local String is src: 'local Int is n: 0xff + 1_000;' . "\n" . '# a comment
local String is s: \'it\\\'s\';
local String is r: "raw \\n stays \{\{x\}\}";
local String is h: ' . "'''\nheredoc\n'''" . ';';
		local Lexer is lx: Lexer:init(source: src);
		local Array of Token is toks: lx:tokenize();

		if (!lx:hasErrors() && toks:length() == 31) {
			output:line('[PASS] clean scan, expected token count');
		} else {
			output:line('[FAIL] scan errors or token count: ' . (toks:length() as String));
			failures: failures + 1;
		}

		# Base-prefixed numbers normalize to decimal; separators strip.
		local Token is hex: toks:get(index: 5);
		local Token is sep: toks:get(index: 7);
		if (hex:getValue() == '255' && hex:getTokenKind() == TokenKind:INT && sep:getValue() == '1000') {
			output:line('[PASS] number normalization');
		} else {
			output:line('[FAIL] number normalization');
			failures: failures + 1;
		}

		# Families: single-quote minimal escape, fancy raw content, raw heredoc.
		local Token is sq: toks:get(index: 14);
		local Token is fq: toks:get(index: 21);
		local Token is hd: toks:get(index: 28);
		if (sq:getValue() == 'it\'s' && sq:getTokenKind() == TokenKind:STRING) {
			output:line('[PASS] single-quote minimal escape');
		} else {
			output:line('[FAIL] single-quote minimal escape');
			failures: failures + 1;
		}
		if (fq:getValue() == "raw \\n stays \\{\\{x\\}\\}" && fq:getTokenKind() == TokenKind:TEMPLATESTRING) {
			output:line('[PASS] fancy string carries raw content incl. escapes');
		} else {
			output:line('[FAIL] fancy string raw content');
			failures: failures + 1;
		}
		if (hd:getValue() == "heredoc\n" && hd:getTokenKind() == TokenKind:RAWSTRING) {
			output:line('[PASS] raw heredoc with delimiter-newline strip');
		} else {
			output:line('[FAIL] raw heredoc content');
			failures: failures + 1;
		}

		# Reserved words carry their Keyword classification for enum dispatch.
		local Token is kwTok: toks:get(index: 0);
		if (kwTok:getKeyword() == Keyword:LOCAL) {
			output:line('[PASS] keyword classification on scanned token');
		} else {
			output:line('[FAIL] keyword classification on scanned token');
			failures: failures + 1;
		}

		# Line/col tracking across the comment line and the multi-line heredoc.
		local Token is afterComment: toks:get(index: 9);
		local Token is end: toks:get(index: 30);
		if (afterComment:getLine() == 3 && end:getTokenKind() == TokenKind:EOF && end:getLine() == 7) {
			output:line('[PASS] line tracking across comment and heredoc');
		} else {
			output:line('[FAIL] line tracking');
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
			output:line('[PASS] lexical errors carry substituted wording and reflection provenance');
		} else {
			output:line('[FAIL] lexical error provenance: ' . rendered);
			failures: failures + 1;
		}

		if (failures == 0) {
			output:line('[PASS] spec lexer test complete');
		} else {
			output:line('[FAIL] spec lexer test: ' . (failures as String) . ' failures');
		}
	}
}
