#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, and Linter.

## Lexical scanner converting Spec source code strings into a stream of [Token] items.
##
## Employs decoupled iterator loops for skipping whitespace, comments, identifiers,
## numbers, and string literals.
Class is Lexer{

	replace Array of String is using: [
		base:struct:Array,
		base:iterator:*,
		compiler:Token
	];

	local String is source: "";
	local Int is length: 0;
	local Int is pos: 0;
	local Int is line: 1;
	local Int is col: 1;
	local Array of String is errors: [];

	# Internal Loop Classes
	Class is SkipWhitespaceLoop extends Loop{
		local Lexer is lexer;

		replace Function is init(Lexer is lexer){
			self:lexer: lexer;
		}

		replace Function of Boolean is evaluate(){
			return lexer:pos < lexer:length;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: lexer:source:charAt(index: lexer:pos, default: "");
			if (ch:isWhitespace()) {
				lexer:advance();
				return true;
			}
			if (ch == "#") {
				While:run(loop: SkipCommentLoop:init(lexer: lexer));
				return true;
			}
			return false;
		}
	}

	Class is SkipCommentLoop extends Loop{
		local Lexer is lexer;

		replace Function is init(Lexer is lexer){
			self:lexer: lexer;
		}

		replace Function of Boolean is evaluate(){
			return lexer:pos < lexer:length && lexer:source:charAt(index: lexer:pos, default: "") != "\n";
		}

		replace Function of Boolean is iteration(LoopControl is control){
			lexer:advance();
			return true;
		}
	}

	Class is IdentScanLoop extends Loop{
		local Lexer is lexer;

		replace Function is init(Lexer is lexer){
			self:lexer: lexer;
		}

		replace Function of Boolean is evaluate(){
			return lexer:pos < lexer:length;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: lexer:source:charAt(index: lexer:pos, default: "");
			if (lexer:isIdentifierContinue(ch: ch)) {
				lexer:advance();
				return true;
			}
			return false;
		}
	}

	## Scans the digits of a base-prefixed literal (2, 8, or 16), accumulating
	## the decimal value. Underscore separators are skipped; an alphanumeric
	## character that is not a valid digit for the base flags an error and is
	## consumed so scanning can continue.
	Class is BaseDigitsLoop extends Loop{
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
			local String is ch: self:lexer:source:charAt(index: self:lexer:pos, default: "");
			if (ch == "_") {
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
			if (ch:isAlpha() || ch:isDigit()) {
				self:hadInvalid: true;
				self:lexer:advance();
				return true;
			}
			return false;
		}
	}

	Class is NumberScanLoop extends Loop{
		local Lexer is lexer;
		local Boolean is isFloat: false;

		replace Function is init(Lexer is lexer){
			self:lexer: lexer;
			self:isFloat: false;
		}

		replace Function of Boolean is evaluate(){
			return lexer:pos < lexer:length;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: lexer:source:charAt(index: lexer:pos, default: "");
			if (ch == "_") {
				local String is nextCh: lexer:source:charAt(index: lexer:pos + 1, default: "");
				if (nextCh:isDigit()) {
					lexer:advance();
					return true;
				}
				return false;
			}
			if (ch:isDigit()) {
				lexer:advance();
				return true;
			}
			if (ch == "." && !isFloat) {
				local String is nextCh: lexer:source:charAt(index: lexer:pos + 1, default: "");
				if (nextCh:isDigit()) {
					self:isFloat: true;
					lexer:advance();
					return true;
				}
			}
			return false;
		}
	}

	Class is StringScanLoop extends Loop{
		local Lexer is lexer;
		local String is quote: "";
		local String is res: "";

		replace Function is init(Lexer is lexer, String is quote){
			self:lexer: lexer;
			self:quote: quote;
			self:res: "";
		}

		replace Function of Boolean is evaluate(){
			return self:lexer:pos < self:lexer:length;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:lexer:source:charAt(index: self:lexer:pos, default: "");
			if (ch == self:quote) {
				return false;
			}
			if (ch == "\\") {
				self:lexer:advance();
				if (self:lexer:pos < self:lexer:length) {
					local String is nextCh: self:lexer:advance();
					if (self:quote == "\"") {
						when (nextCh) {
							is "n": { self:res: self:res . "\n"; }
							is "t": { self:res: self:res . "\t"; }
							is "r": { self:res: self:res . "\r"; }
							is "e": { self:res: self:res . String:fromCharCode(code: 27); }
							is "\"": { self:res: self:res . "\""; }
							is "\\": { self:res: self:res . "\\"; }
							else: { self:res: self:res . nextCh; }
						}
					} else {
						if (nextCh == "'" || nextCh == "\\") {
							self:res: self:res . nextCh;
						} else {
							self:res: self:res . "\\" . nextCh;
						}
					}
				}
				return true;
			}
			self:res: self:res . ch;
			self:lexer:advance();
			return true;
		}
	}

	Class is TokenizeLoop extends Loop{
		local Lexer is lexer;
		local Array of Token is tokens;

		replace Function is init(Lexer is lexer, Array of Token is tokens){
			self:lexer: lexer;
			self:tokens: tokens;
		}

		replace Function of Boolean is evaluate(){
			return lexer:pos < lexer:length;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			lexer:skipWhitespaceAndComments();
			if (lexer:pos >= lexer:length) {
				return false;
			}

			local String is ch: lexer:source:charAt(index: lexer:pos, default: "");
			if (ch == '"' || ch == "'") {
				tokens:add(item: lexer:readString(quote: ch));
			} else if (ch:isDigit()) {
				tokens:add(item: lexer:readNumber());
			} else if (lexer:isIdentifierStart(ch: ch)) {
				tokens:add(item: lexer:readIdentifierOrKeyword());
			} else {
				tokens:add(item: lexer:readSymbol());
			}
			return true;
		}
	}

	## Initializes a lexer instance for the given source string.
	##
	## @param source: Spec source code string to tokenize.
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
	local Function is addError(String is msg){
		self:errors:add(item: "Line " . self:line . ": " . msg);
	}

	## Returns whether any lexical errors were recorded.
	Function of Boolean is hasErrors(){
		return self:errors:length() > 0;
	}

	## Returns all recorded lexical error messages.
	Function of Array of String is getErrors(){
		return self:errors;
	}

	## Maps a hexadecimal digit character to its value (0..15), or -1.
	##
	## @param ch: Digit character.
	## @return: Digit value, or -1 when not a hex digit.
	Function of Int is digitValue(String is ch){
		local String is lower: "0123456789abcdef";
		local Int is d: lower:indexOf(needle: ch, default: -1);
		if (d >= 0) {
			return d;
		}
		local String is upper: "ABCDEF";
		local Int is u: upper:indexOf(needle: ch, default: -1);
		if (u >= 0) {
			return u + 10;
		}
		return -1;
	}

	local Function of Boolean is isAtEnd(){
		return self:pos >= self:length;
	}

	Function of String is advance(){
		local String is ch: self:source:charAt(index: self:pos, default: "");
		self:pos: self:pos + 1;
		if (ch == "\n") {
			self:line: self:line + 1;
			self:col: 1;
		} else {
			self:col: self:col + 1;
		}
		return ch;
	}

	Function is skipWhitespaceAndComments(){
		While:run(loop: SkipWhitespaceLoop:init(lexer: self));
	}

	Function of Boolean is isIdentifierStart(String is ch){
		return ch:isAlpha() || ch == "_";
	}

	Function of Boolean is isIdentifierContinue(String is ch){
		return ch:isAlpha() || ch:isDigit() || ch == "_";
	}

	local Function of Boolean is isKeyword(String is text){
		return when (text) {
			is "extends", "local", "contained", "replace", "merge", "is", "as", "of", "to", "return", "if", "else", "when": true;
			else: false;
		};
	}

	Function of Token is readIdentifierOrKeyword(){
		local Int is startLine: self:line;
		local Int is startCol: self:col;
		local Int is startPos: self:pos;

		While:run(loop: IdentScanLoop:init(lexer: self));

		local String is text: self:source:substring(start: startPos, end: self:pos);
		local TokenKind is kind: when (text) {
			is "true", "false": TokenKind:BOOL;
			else: if (self:isKeyword(text: text)) TokenKind:KEYWORD else TokenKind:IDENTIFIER;
		};
		return Token:init(kind: kind, value: text, line: startLine, col: startCol);
	}

	Function of Token is readNumber(){
		local Int is startLine: self:line;
		local Int is startCol: self:col;

		# Base-prefixed integers (0x / 0b / 0o), normalized to a decimal value so
		# the generated C stays portable C11. A bare leading zero stays decimal.
		local String is ch: self:source:charAt(index: self:pos, default: "");
		local String is nextCh: self:source:charAt(index: self:pos + 1, default: "");
		if (ch == "0" && nextCh != "" && nextCh != "." && nextCh:isDigit() == false) {
			if (nextCh == "x" || nextCh == "X" || nextCh == "b" || nextCh == "B" || nextCh == "o" || nextCh == "O") {
				local Int is base: 16;
				if (nextCh == "b" || nextCh == "B") {
					base: 2;
				}
				if (nextCh == "o" || nextCh == "O") {
					base: 8;
				}
				self:advance();
				self:advance();
				local BaseDigitsLoop is digitLoop: BaseDigitsLoop:init(lexer: self, base: base);
				While:run(loop: digitLoop);
				if (digitLoop:hadInvalid) {
					self:addError(msg: "Invalid digit in base-" . base . " number literal");
				}
				if (digitLoop:digitCount == 0) {
					self:addError(msg: "Missing digits after base prefix");
				}
				return Token:init(kind: TokenKind:INT, value: "" . digitLoop:value, line: startLine, col: startCol);
			}
		}

		local Int is startPos: self:pos;
		local NumberScanLoop is numLoop: NumberScanLoop:init(lexer: self);
		While:run(loop: numLoop);

		local String is text: self:source:substring(start: startPos, end: self:pos);
		if (text:contains(needle: "_")) {
			# Strip separators: underscore digit groups are not valid C11.
			local String is stripped: "";
			local Int is ti: 0;
			While:condition(
				evaluate: local Function of Boolean(){
					return ti < text:length();
				},
				iteration: local Function of Boolean(){
					local String is tc: text:charAt(index: ti, default: "");
					if (tc != "_") {
						stripped: stripped . tc;
					}
					ti: ti + 1;
					return true;
				}
			);
			text: stripped;
		}
		local TokenKind is kind: if (numLoop:isFloat) TokenKind:FLOAT else TokenKind:INT;
		if (kind == TokenKind:INT && text:length() > 1 && text:charAt(index: 0, default: "") == "0") {
			# A bare leading zero stays decimal in Spec; strip it so C does not
			# reinterpret the emitted literal as octal.
			local Int is z: 0;
			While:condition(
				evaluate: local Function of Boolean(){
					return text:length() > 1 && text:charAt(index: 0, default: "") == "0";
				},
				iteration: local Function of Boolean(){
					text: text:substring(start: 1, end: text:length());
					z: z + 1;
					return true;
				}
			);
		}
		return Token:init(kind: kind, value: text, line: startLine, col: startCol);
	}

	Function of Token is readString(String is quote){
		local Int is startLine: self:line;
		local Int is startCol: self:col;
		self:advance();

		local StringScanLoop is loop: StringScanLoop:init(lexer: self, quote: quote);
		While:run(loop: loop);

		if (self:pos < self:length) {
			self:advance();
		}
		return Token:init(kind: TokenKind:STRING, value: loop:res, line: startLine, col: startCol);
	}

	Function of Token is readSymbol(){
		local Int is startLine: self:line;
		local Int is startCol: self:col;
		local String is ch: self:advance();
		local String is nextCh: self:source:charAt(index: self:pos, default: "");

		if (ch == "=" && nextCh == "=") {
			self:advance();
			return Token:init(kind: TokenKind:SYMBOL, value: "==", line: startLine, col: startCol);
		}
		if (ch == "!" && nextCh == "=") {
			self:advance();
			return Token:init(kind: TokenKind:SYMBOL, value: "!=", line: startLine, col: startCol);
		}
		if (ch == "<" && nextCh == "=") {
			self:advance();
			return Token:init(kind: TokenKind:SYMBOL, value: "<=", line: startLine, col: startCol);
		}
		if (ch == ">" && nextCh == "=") {
			self:advance();
			return Token:init(kind: TokenKind:SYMBOL, value: ">=", line: startLine, col: startCol);
		}
		if (ch == "&" && nextCh == "&") {
			self:advance();
			return Token:init(kind: TokenKind:SYMBOL, value: "&&", line: startLine, col: startCol);
		}
		if (ch == "|" && nextCh == "|") {
			self:advance();
			return Token:init(kind: TokenKind:SYMBOL, value: "||", line: startLine, col: startCol);
		}
		if (ch == "<" && nextCh == "<") {
			self:advance();
			return Token:init(kind: TokenKind:SYMBOL, value: "<<", line: startLine, col: startCol);
		}
		if (ch == ">" && nextCh == ">") {
			self:advance();
			return Token:init(kind: TokenKind:SYMBOL, value: ">>", line: startLine, col: startCol);
		}
		if (ch == ":" && nextCh == ":") {
			self:advance();
			return Token:init(kind: TokenKind:SYMBOL, value: "::", line: startLine, col: startCol);
		}

		return Token:init(kind: TokenKind:SYMBOL, value: ch, line: startLine, col: startCol);
	}

	## Tokenizes the entire source string, returning an array of scanned tokens ending with EOF.
	##
	## @return: [Array] of [Token] items.
	Function of Array of Token is tokenize(){
		local Array of Token is tokens: [];
		While:run(loop: TokenizeLoop:init(lexer: self, tokens: tokens));
		tokens:add(item: Token:init(kind: TokenKind:EOF, value: "", line: self:line, col: self:col));
		return tokens;
	}

}
