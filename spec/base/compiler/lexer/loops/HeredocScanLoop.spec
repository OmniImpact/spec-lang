#! Package base:compiler:lexer:loops
#! Copies heredoc bytes until the closing triple delimiter.

Class of Loop is HeredocScanLoop{
	replace Array of String is namespace: ['base', 'compiler', 'lexer', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'lexer', Lexer],
		['base', 'iterator']
	];

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
