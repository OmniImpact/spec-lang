#! Package base:compiler:lexer
#! Turns Spec source text into a token stream.
##
## The scanner is pure and position-driven: it holds the source, a cursor,
## and line/col tracking, and produces [Token] values ending with EOF.
## Scan work runs in private [Loop] classes (one concern each); the public
## surface is `init` + `tokenize` + the error accessors. String families
## follow the language's two-family rule: raw ('...' and ''') keep bytes
## exactly as written (minimal quote escapes for single quotes); the fancy
## family ("..." and ```) is scanned raw here and interpreted later by the
## parser's template desugar.
##
## Reported errors are [Error] values carrying provenance; message
## wordings come from an [ErrorText] instance the lexer owns (a lexer uses
## a vocabulary, it is not one).

Class is Lexer{
	replace Array of String is namespace: ['base', 'compiler', 'lexer'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'utils', Chars],
		['spec', 'base', 'compiler', 'lexer', Token],
		['spec', 'base', 'compiler', 'lexer', TokenKind],
		['spec', 'base', 'compiler', 'lexer', Keyword],
		['spec', 'base', 'compiler', WellKnown],
		['spec', 'base', 'compiler', 'lexer', Operator],
		['spec', 'base', 'compiler', 'lexer', 'loops', TokenizeLoop],
		['spec', 'base', 'compiler', 'lexer', 'loops', SkipWhitespaceLoop],
		['spec', 'base', 'compiler', 'lexer', 'loops', IdentScanLoop],
		['spec', 'base', 'compiler', 'lexer', 'loops', BaseDigitsLoop],
		['spec', 'base', 'compiler', 'lexer', 'loops', NumberScanLoop],
		['spec', 'base', 'compiler', 'lexer', 'loops', StringScanLoop],
		['spec', 'base', 'compiler', 'lexer', 'loops', HeredocScanLoop],
		['spec', 'base', 'compiler', 'lexer', 'loops', StripUnderscoresLoop],
		['spec', 'base', 'compiler', 'lexer', 'loops', StripLeadingZerosLoop],
		['spec', 'base', 'compiler', Error],
		['spec', 'base', 'compiler', ErrorText],
		['spec', 'base', 'sysinternal', Reflection],
		['lib', 'base', 'iterator']
	];

	## The full source text being scanned. Public because the scan loops
	## are collaborators that drive the cursor; lifecycle stays with the
	## lexer.
	String is source: '';

	## Source length, cached to keep loop guards cheap.
	Int is length: 0;

	## Byte cursor into [source].
	Int is pos: 0;

	## One-based line of the cursor.
	Int is line: 1;

	## One-based column of the cursor.
	Int is col: 1;

	## Lexical errors, in scan order.
	local Array of Error is errors: [];

	## Well-known names.
	local WellKnown is names: WellKnown:init();

	## Stateless character classification (letters, digits, case). Public
	## for the same reason as the cursor: the digit scan loops consult it.
	Chars is chars: Chars:init();

	## Message wordings, owned by composition.
	local ErrorText is errText: ErrorText:init();

	## Initializes a lexer over the given source text.
	##
	## @param source: Spec source code to tokenize.
	replace Function is init(String is source){
		self:source: source;
		self:length: source:length();
		self:pos: 0;
		self:line: 1;
		self:col: 1;
		self:errors: [];
	}

	## Records a lexical error at the current scan position: the message
	## carries the line, and the first provenance frame records exactly
	## where the scanner observed the problem.
	##
	## @param msg: Error description.
	Function is addError(String is msg){
		local Error is e: Error:init(message: "Line {{self:line}}: {{msg}}");
		e:addTraceAt(className: Reflection:class(), methodName: Reflection:method(), line: self:line, col: self:col);
		self:errors:add(item: e);
	}

	## Returns whether any lexical errors were recorded.
	##
	## @return: true when [errors] is non-empty.
	Function of Boolean is hasErrors(){
		return self:errors:length() > 0;
	}

	## Returns all recorded lexical errors.
	##
	## @return: [Error] values, in scan order.
	Function of Array of Error is getErrors(){
		return self:errors;
	}

	## Tokenizes the entire source, ending with an EOF token at the final
	## cursor position.
	##
	## @return: The token stream.
	Function of Array of Token is tokenize(){
		local Array of Token is tokens: [];
		While:run(loop: TokenizeLoop:init(lexer: self, tokens: tokens));
		tokens:add(item: Token:init(kind: TokenKind:EOF, value: '', line: self:line, col: self:col));
		return tokens;
	}

	## Maps a hexadecimal digit character to its value (0..15), or -1.
	##
	## @param ch: Digit character.
	## @return: Digit value, or -1 when not a hex digit.
	Function of Int is digitValue(String is ch){
		local String is lower: '0123456789abcdef';
		local Int is d: lower:indexOf(search: ch, default: -1);
		if (d >= 0) {
			return d;
		}
		local String is upper: 'ABCDEF';
		local Int is u: upper:indexOf(search: ch, default: -1);
		if (u >= 0) {
			return u + 10;
		}
		return -1;
	}

	## Consumes the current character and updates line/col tracking.
	##
	## @return: The consumed character ('' at end of source).
	Function of String is advance(){
		local String is ch: self:source:charAt(index: self:pos, default: '');
		self:pos: self:pos + 1;
		if (ch == "\n") {
			self:line: self:line + 1;
			self:col: 1;
		} else {
			self:col: self:col + 1;
		}
		return ch;
	}

	## True when [ch] may begin an identifier.
	##
	## @param ch: Candidate character.
	## @return: Classification result.
	Function of Boolean is isIdentifierStart(String is ch){
		return self:chars:isIdentifierStart(ch: ch);
	}

	## True when [ch] may continue an identifier.
	##
	## @param ch: Candidate character.
	## @return: Classification result.
	Function of Boolean is isIdentifierContinue(String is ch){
		return self:chars:isIdentifierContinue(ch: ch);
	}

	## Skips whitespace and `#` comment lines before the next token.
	Function is skipWhitespaceAndComments(){
		While:run(loop: SkipWhitespaceLoop:init(lexer: self));
	}

	## Scans an identifier or reserved word into a token. Reserved words
	## carry their [Keyword] classification for downstream enum dispatch.
	##
	## @return: KEYWORD or IDENTIFIER token.
	Function of Token is readIdentifierOrKeyword(){
		local Int is startLine: self:line;
		local Int is startCol: self:col;
		local Int is startPos: self:pos;

		While:run(loop: IdentScanLoop:init(lexer: self));

		local String is text: self:source:substring(start: startPos, end: self:pos);
		local Keyword is kw: Keyword:of(text);
		local TokenKind is kind: TokenKind:IDENTIFIER;
		if (kw != Keyword:NONE) {
			kind: TokenKind:KEYWORD;
		}
		# Boolean literals are identifier-shaped but scan as their own kind.
		if (text == self:names:boolTrue() || text == 'false') {
			kind: TokenKind:BOOL;
		}
		local Token is t: Token:init(kind: kind, value: text, line: startLine, col: startCol);
		if (kw != Keyword:NONE) {
			t:setKeyword(kw: kw);
		}
		return t;
	}

	## Scans a numeric literal: decimal, base-prefixed (0x/0b/0o), floats,
	## with `_` separators stripped and bare leading zeros normalized so the
	## emitted C literal stays decimal.
	##
	## @return: INT or FLOAT token.
	Function of Token is readNumber(){
		local Int is startLine: self:line;
		local Int is startCol: self:col;

		local String is ch: self:source:charAt(index: self:pos, default: '');
		local String is nextCh: self:source:charAt(index: self:pos + 1, default: '');
		if (ch == '0' && nextCh != '' && nextCh != '.' && !nextCh:isDigit()) {
			if (nextCh == 'x' || nextCh == 'X' || nextCh == 'b' || nextCh == 'B' || nextCh == 'o' || nextCh == 'O') {
				local Int is base: 16;
				if (nextCh == 'b' || nextCh == 'B') {
					base: 2;
				}
				if (nextCh == 'o' || nextCh == 'O') {
					base: 8;
				}
				self:advance();
				self:advance();
				local BaseDigitsLoop is digitLoop: BaseDigitsLoop:init(lexer: self, base: base);
				While:run(loop: digitLoop);
				if (digitLoop:hadInvalid) {
					self:addError(msg: self:errText:errInvalidDigitInBase(base: base));
				}
				if (digitLoop:digitCount == 0) {
					self:addError(msg: self:errText:errMissingDigitsAfterPrefix());
				}
				return Token:init(kind: TokenKind:INT, value: '' . digitLoop:value, line: startLine, col: startCol);
			}
		}

		local Int is startPos: self:pos;
		local NumberScanLoop is numLoop: NumberScanLoop:init(lexer: self);
		While:run(loop: numLoop);

		local String is text: self:source:substring(start: startPos, end: self:pos);
		local StripUnderscoresLoop is strip: StripUnderscoresLoop:init(src: text);
		While:run(loop: strip);
		text: strip:res;

		local TokenKind is kind: TokenKind:INT;
		if (numLoop:isFloat) {
			kind: TokenKind:FLOAT;
		}
		if (kind == TokenKind:INT && text:length() > 1 && text:charAt(index: 0, default: '') == '0') {
			# A bare leading zero stays decimal in Spec; strip it so C does
			# not reinterpret the emitted literal as octal.
			local StripLeadingZerosLoop is zeros: StripLeadingZerosLoop:init(src: text);
			While:run(loop: zeros);
			text: zeros:res;
		}
		return Token:init(kind: kind, value: text, line: startLine, col: startCol);
	}

	## Scans a single- or double-quoted string literal. The scan stays
	## escape-aware so an escaped quote cannot terminate the literal; the
	## template family carries raw content (its escapes and templates are
	## the parser's desugar), single quotes keep their two minimal escapes
	## (\' and \\) here.
	##
	## @param quote: The quote character being scanned.
	## @return: TEMPLATESTRING for double quotes, STRING otherwise.
	Function of Token is readString(String is quote){
		local Int is startLine: self:line;
		local Int is startCol: self:col;
		self:advance();

		local StringScanLoop is loop: StringScanLoop:init(lexer: self, quote: quote);
		While:run(loop: loop);

		if (self:pos < self:length) {
			self:advance();
		}
		if (quote == '"') {
			return Token:init(kind: TokenKind:TEMPLATESTRING, value: loop:res, line: startLine, col: startCol);
		}
		return Token:init(kind: TokenKind:STRING, value: loop:res, line: startLine, col: startCol);
	}

	## Scans a triple-delimiter heredoc. The delimiter line's own newline is
	## not content (shell heredoc convention); the first closing triple ends
	## the block.
	##
	## @param quote: The three-character delimiter.
	## @param kind: RAWSTRING for '''''' or TEMPLATESTRING for backticks.
	## @return: The heredoc token with raw content.
	Function of Token is readTriple(String is quote, TokenKind is kind){
		local Int is startLine: self:line;
		local Int is startCol: self:col;
		self:advance();
		self:advance();
		self:advance();
		if (self:pos < self:length && self:source:charAt(index: self:pos, default: '') == "\n") {
			self:advance();
		}

		local HeredocScanLoop is loop: HeredocScanLoop:init(lexer: self, quote: quote);
		While:run(loop: loop);

		if (!loop:closed) {
			self:addError(msg: self:errText:errUnterminatedHeredoc(quote: quote));
		}
		return Token:init(kind: kind, value: loop:res, line: startLine, col: startCol);
	}

	## Scans one symbol token: two-character operators take precedence over
	## their one-character prefixes and carry their [Operator]
	## classification for downstream enum dispatch.
	##
	## @return: SYMBOL token.
	Function of Token is readSymbol(){
		local Int is startLine: self:line;
		local Int is startCol: self:col;
		local String is ch: self:advance();
		local String is nextCh: self:source:charAt(index: self:pos, default: '');
		local String is pair: ch . nextCh;

		local Operator is op: Operator:of(pair);
		if (op != Operator:NONE) {
			self:advance();
			local Token is t: Token:init(kind: TokenKind:SYMBOL, value: pair, line: startLine, col: startCol);
			t:setOperator(op: op);
			return t;
		}
		return Token:init(kind: TokenKind:SYMBOL, value: ch, line: startLine, col: startCol);
	}

}
