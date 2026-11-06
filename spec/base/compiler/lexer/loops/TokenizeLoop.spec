#! Package base:compiler:lexer:loops
#! Drives the scan: skips separators, classifies the next character, and
## hands off to the matching scanner.

Class of Loop is TokenizeLoop{
	replace Array of String is namespace: ['base', 'compiler', 'lexer', 'loops'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'lexer', Lexer],
		['spec', 'base', 'compiler', 'lexer', Token],
		['spec', 'base', 'compiler', 'lexer', TokenKind],
		['lib', 'base', 'iterator']
	];

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
			# The template heredoc: raw content now, escapes and templates
			# interpreted by the parser's desugar.
			local String is triple: self:lexer:source:substring(start: self:lexer:pos, end: self:lexer:pos + 3);
			if (triple == "```") {
				self:tokens:add(item: self:lexer:readTriple(quote: "```", kind: TokenKind:TEMPLATESTRING));
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
