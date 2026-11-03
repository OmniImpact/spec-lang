#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, and Linter.

## Lexical scanner converting Spec source code strings into a stream of [Token] items.
##
## Employs decoupled iterator loops for skipping whitespace, comments, identifiers,
## numbers, and string literals.
class Lexer{

	replace local Array of String is using: [
		base:struct:Array,
		base:iterator:*,
		compiler:Token
	];

	local String is source: "";
	local Int is length: 0;
	local Int is pos: 0;
	local Int is line: 1;
	local Int is col: 1;

	# Internal Loop Classes
	class SkipWhitespaceLoop extends Loop{
		local Lexer is lexer;

		replace local Function is init(Lexer is lexer){
			self:lexer: lexer;
		}

		replace local Function of Boolean is evaluate(){
			return lexer:pos < lexer:length;
		}

		replace local Function of Boolean is iteration(LoopControl is control){
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

	class SkipCommentLoop extends Loop{
		local Lexer is lexer;

		replace local Function is init(Lexer is lexer){
			self:lexer: lexer;
		}

		replace local Function of Boolean is evaluate(){
			return lexer:pos < lexer:length && lexer:source:charAt(index: lexer:pos, default: "") != "\n";
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			lexer:advance();
			return true;
		}
	}

	class IdentScanLoop extends Loop{
		local Lexer is lexer;

		replace local Function is init(Lexer is lexer){
			self:lexer: lexer;
		}

		replace local Function of Boolean is evaluate(){
			return lexer:pos < lexer:length;
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local String is ch: lexer:source:charAt(index: lexer:pos, default: "");
			if (lexer:isIdentifierContinue(ch: ch)) {
				lexer:advance();
				return true;
			}
			return false;
		}
	}

	class NumberScanLoop extends Loop{
		local Lexer is lexer;
		local Boolean is isFloat: false;

		replace local Function is init(Lexer is lexer){
			self:lexer: lexer;
			self:isFloat: false;
		}

		replace local Function of Boolean is evaluate(){
			return lexer:pos < lexer:length;
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local String is ch: lexer:source:charAt(index: lexer:pos, default: "");
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

	class StringScanLoop extends Loop{
		local Lexer is lexer;
		local String is quote: "";

		replace local Function is init(Lexer is lexer, String is quote){
			self:lexer: lexer;
			self:quote: quote;
		}

		replace local Function of Boolean is evaluate(){
			return lexer:pos < lexer:length;
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local String is ch: lexer:source:charAt(index: lexer:pos, default: "");
			if (ch == "\\") {
				lexer:advance();
				if (lexer:pos < lexer:length) {
					lexer:advance();
				}
				return true;
			}
			if (ch == quote) {
				return false;
			}
			lexer:advance();
			return true;
		}
	}

	class TokenizeLoop extends Loop{
		local Lexer is lexer;
		local Array of Token is tokens;

		replace local Function is init(Lexer is lexer, Array of Token is tokens){
			self:lexer: lexer;
			self:tokens: tokens;
		}

		replace local Function of Boolean is evaluate(){
			return lexer:pos < lexer:length;
		}

		replace local Function of Boolean is iteration(LoopControl is control){
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
	replace local Function is init(String is source){
		self:source: source;
		self:length: source:length();
		self:pos: 0;
		self:line: 1;
		self:col: 1;
	}

	replace local Function of Boolean is isAtEnd(){
		return self:pos >= self:length;
	}

	replace local Function of String is advance(){
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

	replace local Function is skipWhitespaceAndComments(){
		While:run(loop: SkipWhitespaceLoop:init(lexer: self));
	}

	replace local Function of Boolean is isIdentifierStart(String is ch){
		return ch:isAlpha() || ch == "_";
	}

	replace local Function of Boolean is isIdentifierContinue(String is ch){
		return ch:isAlpha() || ch:isDigit() || ch == "_";
	}

	replace local Function of Boolean is isKeyword(String is text){
		return when (text) {
			is "class", "extends", "local", "replace", "is", "of", "to", "return", "if", "else", "when": true;
			else: false;
		};
	}

	replace local Function of Token is readIdentifierOrKeyword(){
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

	replace local Function of Token is readNumber(){
		local Int is startLine: self:line;
		local Int is startCol: self:col;
		local Int is startPos: self:pos;

		local NumberScanLoop is numLoop: NumberScanLoop:init(lexer: self);
		While:run(loop: numLoop);

		local String is text: self:source:substring(start: startPos, end: self:pos);
		local TokenKind is kind: if (numLoop:isFloat) TokenKind:FLOAT else TokenKind:INT;
		return Token:init(kind: kind, value: text, line: startLine, col: startCol);
	}

	replace local Function of Token is readString(String is quote){
		local Int is startLine: self:line;
		local Int is startCol: self:col;
		self:advance();
		local Int is startPos: self:pos;

		While:run(loop: StringScanLoop:init(lexer: self, quote: quote));

		local String is val: self:source:substring(start: startPos, end: self:pos);
		if (self:pos < self:length) {
			self:advance();
		}
		return Token:init(kind: TokenKind:STRING, value: val, line: startLine, col: startCol);
	}

	replace local Function of Token is readSymbol(){
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
		if (ch == ":" && nextCh == ":") {
			self:advance();
			return Token:init(kind: TokenKind:SYMBOL, value: "::", line: startLine, col: startCol);
		}

		return Token:init(kind: TokenKind:SYMBOL, value: ch, line: startLine, col: startCol);
	}

	## Tokenizes the entire source string, returning an array of scanned tokens ending with EOF.
	##
	## @return: [Array] of [Token] items.
	replace local Function of Array of Token is tokenize(){
		local Array of Token is tokens: [];
		While:run(loop: TokenizeLoop:init(lexer: self, tokens: tokens));
		tokens:add(item: Token:init(kind: TokenKind:EOF, value: "", line: self:line, col: self:col));
		return tokens;
	}

}
