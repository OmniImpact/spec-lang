class Lexer{

	replace local Array of String is using: [
		base:struct:Array,
		compiler:Token
	];

	local String is source: "";
	local Int is length: 0;
	local Int is pos: 0;
	local Int is line: 1;
	local Int is col: 1;

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
		while (self:pos < self:length) {
			local String is ch: self:source:charAt(index: self:pos, default: "");
			if (ch:isWhitespace()) {
				self:advance();
			} else if (ch == "#") {
				while (self:pos < self:length && self:source:charAt(index: self:pos, default: "") != "\n") {
					self:advance();
				}
			} else {
				break;
			}
		}
	}

	replace local Function of Boolean is isIdentifierStart(String is ch){
		return ch:isAlpha() || ch == "_";
	}

	replace local Function of Boolean is isIdentifierContinue(String is ch){
		return ch:isAlpha() || ch:isDigit() || ch == "_";
	}

	replace local Function of Boolean is isKeyword(String is text){
		if (text == "class" || text == "extends" || text == "local" || text == "replace") {
			return true;
		}
		if (text == "is" || text == "of" || text == "to" || text == "return") {
			return true;
		}
		if (text == "if" || text == "else" || text == "while" || text == "break") {
			return true;
		}
		return false;
	}

	replace local Function of Token is readIdentifierOrKeyword(){
		local Int is startLine: self:line;
		local Int is startCol: self:col;
		local Int is startPos: self:pos;

		while (self:pos < self:length) {
			local String is ch: self:source:charAt(index: self:pos, default: "");
			if (self:isIdentifierContinue(ch: ch)) {
				self:advance();
			} else {
				break;
			}
		}

		local String is text: self:source:substring(start: startPos, end: self:pos);
		if (text == "true" || text == "false") {
			return Token:init(kind: "BOOL", value: text, line: startLine, col: startCol);
		}
		if (self:isKeyword(text: text)) {
			return Token:init(kind: "KEYWORD", value: text, line: startLine, col: startCol);
		}
		return Token:init(kind: "IDENTIFIER", value: text, line: startLine, col: startCol);
	}

	replace local Function of Token is readNumber(){
		local Int is startLine: self:line;
		local Int is startCol: self:col;
		local Int is startPos: self:pos;
		local Boolean is isFloat: false;

		while (self:pos < self:length) {
			local String is ch: self:source:charAt(index: self:pos, default: "");
			if (ch:isDigit()) {
				self:advance();
			} else if (ch == "." && !isFloat) {
				local String is nextCh: self:source:charAt(index: self:pos + 1, default: "");
				if (nextCh:isDigit()) {
					isFloat: true;
					self:advance();
				} else {
					break;
				}
			} else {
				break;
			}
		}

		local String is text: self:source:substring(start: startPos, end: self:pos);
		if (isFloat) {
			return Token:init(kind: "FLOAT", value: text, line: startLine, col: startCol);
		}
		return Token:init(kind: "INT", value: text, line: startLine, col: startCol);
	}

	replace local Function of Token is readString(String is quote){
		local Int is startLine: self:line;
		local Int is startCol: self:col;
		self:advance();
		local Int is startPos: self:pos;

		while (self:pos < self:length) {
			local String is ch: self:source:charAt(index: self:pos, default: "");
			if (ch == "\\") {
				self:advance();
				if (self:pos < self:length) {
					self:advance();
				}
			} else if (ch == quote) {
				break;
			} else {
				self:advance();
			}
		}

		local String is val: self:source:substring(start: startPos, end: self:pos);
		if (self:pos < self:length) {
			self:advance();
		}
		return Token:init(kind: "STRING", value: val, line: startLine, col: startCol);
	}

	replace local Function of Token is readSymbol(){
		local Int is startLine: self:line;
		local Int is startCol: self:col;
		local String is ch: self:advance();
		local String is nextCh: self:source:charAt(index: self:pos, default: "");

		if (ch == "=" && nextCh == "=") {
			self:advance();
			return Token:init(kind: "SYMBOL", value: "==", line: startLine, col: startCol);
		}
		if (ch == "!" && nextCh == "=") {
			self:advance();
			return Token:init(kind: "SYMBOL", value: "!=", line: startLine, col: startCol);
		}
		if (ch == "<" && nextCh == "=") {
			self:advance();
			return Token:init(kind: "SYMBOL", value: "<=", line: startLine, col: startCol);
		}
		if (ch == ">" && nextCh == "=") {
			self:advance();
			return Token:init(kind: "SYMBOL", value: ">=", line: startLine, col: startCol);
		}
		if (ch == "&" && nextCh == "&") {
			self:advance();
			return Token:init(kind: "SYMBOL", value: "&&", line: startLine, col: startCol);
		}
		if (ch == "|" && nextCh == "|") {
			self:advance();
			return Token:init(kind: "SYMBOL", value: "||", line: startLine, col: startCol);
		}
		if (ch == ":" && nextCh == ":") {
			self:advance();
			return Token:init(kind: "SYMBOL", value: "::", line: startLine, col: startCol);
		}

		return Token:init(kind: "SYMBOL", value: ch, line: startLine, col: startCol);
	}

	replace local Function of Array of Token is tokenize(){
		local Array of Token is tokens: [];

		while (self:pos < self:length) {
			self:skipWhitespaceAndComments();
			if (self:pos >= self:length) {
				break;
			}

			local String is ch: self:source:charAt(index: self:pos, default: "");
			if (ch == '"' || ch == "'") {
				tokens:add(item: self:readString(quote: ch));
			} else if (ch:isDigit()) {
				tokens:add(item: self:readNumber());
			} else if (self:isIdentifierStart(ch: ch)) {
				tokens:add(item: self:readIdentifierOrKeyword());
			} else {
				tokens:add(item: self:readSymbol());
			}
		}

		tokens:add(item: Token:init(kind: "EOF", value: "", line: self:line, col: self:col));
		return tokens;
	}

}
