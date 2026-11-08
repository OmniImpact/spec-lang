#! Package base:compiler:lexer:loops
#! Drives the scan: skips separators, classifies the next character, and
## hands off to the matching scanner.

Class of Loop is TokenizeLoop{
	replace Array of String is namespace: ['base', 'compiler', 'lexer', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'lexer', Token],
		['base', 'compiler', 'lexer', TokenKind],
		['base', 'iterator'],
		['base', 'sys', as Conditional()]
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
		Conditional:branch(check: { self:lexer:pos >= self:lexer:length }, then: {
			return false;
		});

		local String is ch: self:lexer:source:charAt(index: self:lexer:pos, default: '');
		Conditional:branch(check: { ch == '"' || ch == '\'' }, then: {
			# The raw heredoc claims precedence over single quotes.
			local String is triple: self:lexer:source:substring(start: self:lexer:pos, end: self:lexer:pos + 3);
			Conditional:branch(check: { triple == "'''" }, then: {
				self:tokens:add(item: self:lexer:readTriple(quote: "'''", kind: TokenKind:RAWSTRING));
			}, otherwise: {
				self:tokens:add(item: self:lexer:readString(quote: ch));
			});
		}, otherwise: {
			Conditional:branch(check: { ch == '`' }, then: {
				# The template heredoc: raw content now, escapes and templates
				# interpreted by the parser's desugar.
				local String is triple: self:lexer:source:substring(start: self:lexer:pos, end: self:lexer:pos + 3);
				Conditional:branch(check: { triple == "```" }, then: {
					self:tokens:add(item: self:lexer:readTriple(quote: "```", kind: TokenKind:TEMPLATESTRING));
				}, otherwise: {
					self:tokens:add(item: self:lexer:readSymbol());
				});
			}, otherwise: {
				Conditional:branch(check: { ch:isDigit() }, then: {
					self:tokens:add(item: self:lexer:readNumber());
				}, otherwise: {
					Conditional:branch(check: { self:lexer:isIdentifierStart(ch: ch) }, then: {
						self:tokens:add(item: self:lexer:readIdentifierOrKeyword());
					}, otherwise: {
						self:tokens:add(item: self:lexer:readSymbol());
					});
				});
			});
		});
		return true;
	}
}
