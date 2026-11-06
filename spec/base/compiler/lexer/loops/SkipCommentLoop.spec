#! Package base:compiler:lexer:loops
#! Consumes one `#` comment line, stopping at the newline.

Class of Loop is SkipCommentLoop{
	replace Array of String is namespace: ['base', 'compiler', 'lexer', 'loops'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'lexer', Lexer],
		['lib', 'base', 'iterator']
	];

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
