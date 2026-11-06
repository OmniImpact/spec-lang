#! Package newc:lexer
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

Class is Lexer{
	namespace: ['newc', 'lexer'];

	replace Array of Array of String is using: [
		['newc', 'util', Chars],
		['newc', 'lexer', Token],
		['newc', 'lexer', TokenKind],
		['lib', 'base', 'iterator']
	];

	## The full source text being scanned.
	local String is source: '';

	## Source length, cached to keep loop guards cheap.
	local Int is length: 0;

	## Byte cursor into [source].
	local Int is pos: 0;

	## One-based line of the cursor.
	local Int is line: 1;

	## One-based column of the cursor.
	local Int is col: 1;

	## Lexical errors, one human-readable string each.
	local Array of String is errors: [];

	## Stateless character classification (letters, digits, case).
	local Chars is chars: Chars:init();

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

	## Records a lexical error at the current line.
	##
	## @param msg: Error description.
	Function is addError(String is msg){
		self:errors:add(item: 'Line ' . self:line . ': ' . msg);
	}

	## Returns whether any lexical errors were recorded.
	##
	## @return: true when [errors] is non-empty.
	Function of Boolean is hasErrors(){
		return self:errors:length() > 0;
	}

	## Returns all recorded lexical error messages.
	##
	## @return: The error strings, in scan order.
	Function of Array of String is getErrors(){
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

	## True when [text] is a reserved word.
	##
	## @param text: Candidate identifier text.
	## @return: Keyword classification.
	Function of Boolean is isKeyword(String is text){
		return when (text) {
			is 'local', 'contained', 'replace', 'merge', 'is', 'as', 'of', 'to', 'return', 'if', 'else', 'when': true;
			else: false;
		};
	}

	## Skips whitespace and `#` comment lines before the next token.
	Function is skipWhitespaceAndComments(){
		While:run(loop: SkipWhitespaceLoop:init(lexer: self));
	}

	## Scans an identifier or reserved word into a token.
	##
	## @return: KEYWORD or IDENTIFIER token.
	Function of Token is readIdentifierOrKeyword(){
		local Int is startLine: self:line;
		local Int is startCol: self:col;
		local Int is startPos: self:pos;

		While:run(loop: IdentScanLoop:init(lexer: self));

		local String is text: self:source:substring(start: startPos, end: self:pos);
		local TokenKind is kind: TokenKind:IDENTIFIER;
		if (self:isKeyword(text: text)) {
			kind: TokenKind:KEYWORD;
		}
		return Token:init(kind: kind, value: text, line: startLine, col: startCol);
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
					self:addError(msg: 'Invalid digit in base-' . base . ' number literal');
				}
				if (digitLoop:digitCount == 0) {
					self:addError(msg: 'Missing digits after base prefix');
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
	## double-quote family carries raw content (its escapes and templates
	## are the parser's desugar), single quotes keep their two minimal
	## escapes (\' and \\) here.
	##
	## @param quote: The quote character being scanned.
	## @return: FANCYSTRING for double quotes, STRING otherwise.
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
			return Token:init(kind: TokenKind:FANCYSTRING, value: loop:res, line: startLine, col: startCol);
		}
		return Token:init(kind: TokenKind:STRING, value: loop:res, line: startLine, col: startCol);
	}

	## Scans a triple-delimiter heredoc. The delimiter line's own newline is
	## not content (shell heredoc convention); the first closing triple ends
	## the block.
	##
	## @param quote: The three-character delimiter.
	## @param kind: RAWSTRING for '''''' or FANCYSTRING for backticks.
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
			self:addError(msg: 'Unterminated heredoc (missing closing ' . quote . ')');
		}
		return Token:init(kind: kind, value: loop:res, line: startLine, col: startCol);
	}

	## Scans one symbol token: two-character operators take precedence over
	## their one-character prefixes.
	##
	## @return: SYMBOL token.
	Function of Token is readSymbol(){
		local Int is startLine: self:line;
		local Int is startCol: self:col;
		local String is ch: self:advance();
		local String is nextCh: self:source:charAt(index: self:pos, default: '');
		local String is pair: ch . nextCh;

		when (pair) {
			is '==', '!=', '<=', '>=', '&&', '||', '<<', '>>', '::': {
				self:advance();
				return Token:init(kind: TokenKind:SYMBOL, value: pair, line: startLine, col: startCol);
			}
			else: {}
		}
		return Token:init(kind: TokenKind:SYMBOL, value: ch, line: startLine, col: startCol);
	}

	## Drives the scan: skips separators, classifies the next character, and
	## hands off to the matching scanner.
	Class of Loop is TokenizeLoop{
		local Lexer is lexer;
		local Array of Token is tokens;

		replace Function is init(Lexer is lexer, Array of Token is tokens){
			self:lexer: lexer;
			self:tokens: tokens;
		}

		replace Function of Boolean is evaluate(){
			return self:lexer:pos < self:lexer:length;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			self:lexer:skipWhitespaceAndComments();
			if (self:lexer:pos >= self:lexer:length) {
				return false;
			}

			local String is ch: self:lexer:source:charAt(index: self:lexer:pos, default: '');
			if (ch == '"' || ch == '\'') {
				# The raw heredoc claims precedence over single quotes.
				local String is triple: self:lexer:source:substring(start: self:lexer:pos, end: self:lexer:pos + 3);
				if (triple == "'''") {
					self:tokens:add(item: self:lexer:readTriple(quote: "'''", kind: TokenKind:RAWSTRING));
				} else {
					self:tokens:add(item: self:lexer:readString(quote: ch));
				}
			} else if (ch == '`') {
				# The fancy heredoc: raw content now, escapes and templates
				# interpreted by the parser's desugar.
				local String is triple: self:lexer:source:substring(start: self:lexer:pos, end: self:lexer:pos + 3);
				if (triple == "```") {
					self:tokens:add(item: self:lexer:readTriple(quote: "```", kind: TokenKind:FANCYSTRING));
				} else {
					self:tokens:add(item: self:lexer:readSymbol());
				}
			} else if (ch:isDigit()) {
				self:tokens:add(item: self:lexer:readNumber());
			} else if (self:lexer:isIdentifierStart(ch: ch)) {
				self:tokens:add(item: self:lexer:readIdentifierOrKeyword());
			} else {
				self:tokens:add(item: self:lexer:readSymbol());
			}
			return true;
		}
	}

	## Skips runs of whitespace and `#` comment lines.
	Class of Loop is SkipWhitespaceLoop{
		local Lexer is lexer;

		replace Function is init(Lexer is lexer){
			self:lexer: lexer;
		}

		replace Function of Boolean is evaluate(){
			return self:lexer:pos < self:lexer:length;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:lexer:source:charAt(index: self:lexer:pos, default: '');
			if (ch:isWhitespace()) {
				self:lexer:advance();
				return true;
			}
			if (ch == '#') {
				While:run(loop: SkipCommentLoop:init(lexer: self:lexer));
				return true;
			}
			return false;
		}
	}

	## Consumes one `#` comment line, stopping at the newline.
	Class of Loop is SkipCommentLoop{
		local Lexer is lexer;

		replace Function is init(Lexer is lexer){
			self:lexer: lexer;
		}

		replace Function of Boolean is evaluate(){
			return self:lexer:pos < self:lexer:length && self:lexer:source:charAt(index: self:lexer:pos, default: '') != "\n";
		}

		replace Function of Boolean is iteration(LoopControl is control){
			self:lexer:advance();
			return true;
		}
	}

	## Consumes identifier-continue characters.
	Class of Loop is IdentScanLoop{
		local Lexer is lexer;

		replace Function is init(Lexer is lexer){
			self:lexer: lexer;
		}

		replace Function of Boolean is evaluate(){
			return self:lexer:pos < self:lexer:length;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:lexer:source:charAt(index: self:lexer:pos, default: '');
			if (self:lexer:isIdentifierContinue(ch: ch)) {
				self:lexer:advance();
				return true;
			}
			return false;
		}
	}

	## Accumulates a base-prefixed integer's value while scanning. An
	## alphanumeric character that is not a valid digit for the base flags
	## an error and is consumed so scanning can continue.
	Class of Loop is BaseDigitsLoop{
		local Lexer is lexer;
		local Int is base: 16;
		local Int is value: 0;
		local Int is digitCount: 0;
		local Boolean is hadInvalid: false;

		replace Function is init(Lexer is lexer, Int is base){
			self:lexer: lexer;
			self:base: base;
			self:value: 0;
			self:digitCount: 0;
			self:hadInvalid: false;
		}

		replace Function of Boolean is evaluate(){
			return self:lexer:pos < self:lexer:length;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:lexer:source:charAt(index: self:lexer:pos, default: '');
			if (ch == '_') {
				self:lexer:advance();
				return true;
			}
			local Int is d: self:lexer:digitValue(ch: ch);
			if (d >= 0 && d < self:base) {
				self:value: (self:value * self:base) + d;
				self:digitCount: self:digitCount + 1;
				self:lexer:advance();
				return true;
			}
			if (self:lexer:chars:isIdentifierContinue(ch: ch)) {
				self:hadInvalid: true;
				self:lexer:advance();
				return true;
			}
			return false;
		}
	}

	## Consumes decimal digits, one float point, and `_` separators (a
	## separator must sit between digits).
	Class of Loop is NumberScanLoop{
		local Lexer is lexer;
		local Boolean is isFloat: false;

		replace Function is init(Lexer is lexer){
			self:lexer: lexer;
			self:isFloat: false;
		}

		replace Function of Boolean is evaluate(){
			return self:lexer:pos < self:lexer:length;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:lexer:source:charAt(index: self:lexer:pos, default: '');
			if (ch == '_') {
				local String is nextCh: self:lexer:source:charAt(index: self:lexer:pos + 1, default: '');
				if (nextCh:isDigit()) {
					self:lexer:advance();
					return true;
				}
				return false;
			}
			if (ch:isDigit()) {
				self:lexer:advance();
				return true;
			}
			if (ch == '.' && !self:isFloat) {
				local String is nextCh: self:lexer:source:charAt(index: self:lexer:pos + 1, default: '');
				if (nextCh:isDigit()) {
					self:isFloat: true;
					self:lexer:advance();
					return true;
				}
			}
			return false;
		}
	}

	## Copies literal content until the closing quote, keeping the scan
	## escape-aware so an escaped quote cannot terminate the literal.
	Class of Loop is StringScanLoop{
		local Lexer is lexer;
		local String is quote: '';
		local String is res: '';

		replace Function is init(Lexer is lexer, String is quote){
			self:lexer: lexer;
			self:quote: quote;
			self:res: '';
		}

		replace Function of Boolean is evaluate(){
			return self:lexer:pos < self:lexer:length;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:lexer:source:charAt(index: self:lexer:pos, default: '');
			if (ch == self:quote) {
				return false;
			}
			if (ch == "\\") {
				if (self:quote == '\'') {
					# Single-quote family: two minimal escapes, everything
					# else passes through with its backslash.
					self:lexer:advance();
					if (self:lexer:pos < self:lexer:length) {
						local String is nextCh: self:lexer:advance();
						if (nextCh == '\'' || nextCh == "\\") {
							self:res: self:res . nextCh;
						} else {
							self:res: self:res . "\\" . nextCh;
						}
					}
					return true;
				}
				# Double-quote family: raw content; the backslash and its
				# follower are copied verbatim.
				self:res: self:res . "\\";
				self:lexer:advance();
				if (self:lexer:pos < self:lexer:length) {
					local String is nextCh: self:lexer:advance();
					self:res: self:res . nextCh;
				}
				return true;
			}
			self:res: self:res . ch;
			self:lexer:advance();
			return true;
		}
	}

	## Copies heredoc bytes until the closing triple delimiter.
	Class of Loop is HeredocScanLoop{
		local Lexer is lexer;
		local String is quote: '';
		local String is res: '';
		local Boolean is closed: false;

		replace Function is init(Lexer is lexer, String is quote){
			self:lexer: lexer;
			self:quote: quote;
			self:res: '';
			self:closed: false;
		}

		replace Function of Boolean is evaluate(){
			return !self:closed && self:lexer:pos < self:lexer:length;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is triple: self:lexer:source:substring(start: self:lexer:pos, end: self:lexer:pos + 3);
			if (triple == self:quote) {
				self:lexer:advance();
				self:lexer:advance();
				self:lexer:advance();
				self:closed: true;
				return false;
			}
			self:res: self:res . self:lexer:advance();
			return true;
		}
	}

	## Builds the underscore-free form of a numeric literal's text.
	Class of Loop is StripUnderscoresLoop{
		local String is src;
		local Int is pos: 0;
		local String is res: '';

		replace Function is init(String is src){
			self:src: src;
			self:pos: 0;
			self:res: '';
		}

		replace Function of Boolean is evaluate(){
			return self:pos < self:src:length();
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:src:charAt(index: self:pos, default: '');
			self:pos: self:pos + 1;
			if (ch != '_') {
				self:res: self:res . ch;
			}
			return true;
		}
	}

	## Strips bare leading zeros from an integer's text (one zero is kept).
	Class of Loop is StripLeadingZerosLoop{
		local String is src;
		local String is res: '';

		replace Function is init(String is src){
			self:src: src;
			self:res: src;
		}

		replace Function of Boolean is evaluate(){
			return self:res:length() > 1 && self:res:charAt(index: 0, default: '') == '0';
		}

		replace Function of Boolean is iteration(LoopControl is control){
			self:res: self:res:substring(start: 1, end: self:res:length());
			return true;
		}
	}
}
