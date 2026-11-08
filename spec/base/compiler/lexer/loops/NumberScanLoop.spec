#! Package base:compiler:lexer:loops
#! Consumes decimal digits, one float point, and `_` separators (a
## separator must sit between digits).

Class of Loop is NumberScanLoop{
	replace Array of String is namespace: ['base', 'compiler', 'lexer', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'lexer', Lexer],
		['base', 'iterator'],
		['base', 'sys', as Conditional()]
	];

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
		Conditional:if(check: { ch == '_' }, then: {
			local String is nextCh: self:lexer:source:charAt(index: self:lexer:pos + 1, default: '');
			Conditional:if(check: { nextCh:isDigit() }, then: {
				self:lexer:advance();
				return true;
			});
			return false;
		});
		Conditional:if(check: { ch:isDigit() }, then: {
			self:lexer:advance();
			return true;
		});
		Conditional:if(check: { ch == '.' && !self:isFloat }, then: {
			local String is nextCh: self:lexer:source:charAt(index: self:lexer:pos + 1, default: '');
			Conditional:if(check: { nextCh:isDigit() }, then: {
				self:isFloat: true;
				self:lexer:advance();
				return true;
			});
		});
		return false;
	}
}
