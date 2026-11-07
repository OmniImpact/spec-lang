#! Package base:compiler:lexer:loops
#! Skips runs of whitespace and `#` comment lines.

Class of Loop is SkipWhitespaceLoop{
	replace Array of String is namespace: ['base', 'compiler', 'lexer', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'lexer', 'loops', SkipCommentLoop],
		['base', 'iterator']
	];

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
