#! Package base:compiler:lexer:loops
#! Consumes identifier-continue characters.

Class of Loop is IdentScanLoop{
	replace Array of String is namespace: ['base', 'compiler', 'lexer', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'lexer', Lexer],
		['base', 'iterator'],
		['base', 'sys', as Conditional()]
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
		if (self:lexer:isIdentifierContinue(ch: ch)) {
			self:lexer:advance();
			return true;
		}
		return false;
	}
}
