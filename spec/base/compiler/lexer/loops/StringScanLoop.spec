#! Package base:compiler:lexer:loops
#! Copies literal content until the closing quote, keeping the scan
## escape-aware so an escaped quote cannot terminate the literal.

Class of Loop is StringScanLoop{
	replace Array of String is namespace: ['base', 'compiler', 'lexer', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'lexer', Lexer],
		['base', 'iterator'],
		['base', 'sys', as Conditional()]
	];

	local Lexer is lexer;
	local String is quote: '';
	local String is res: '';

	replace Function is init(Lexer is lexer, String is quote){
		self:lexer: lexer;
		self:quote: quote;
		self:res: '';
	}

	replace Function of Boolean is evaluate(){
		return self:lexer:pos < self:lexer:length;
	}

	replace Function of Boolean is iteration(LoopControl is control){
		local String is ch: self:lexer:source:charAt(index: self:lexer:pos, default: '');
		if (ch == self:quote) {
			return false;
		}
		if (ch == "\\") {
			if (self:quote == '\'') {
				# Single-quote family: two minimal escapes, everything
				# else passes through with its backslash.
				self:lexer:advance();
				if (self:lexer:pos < self:lexer:length) {
					local String is nextCh: self:lexer:advance();
					if (nextCh == '\'' || nextCh == "\\") {
						self:res: self:res . nextCh;
					} else {
						self:res: self:res . "\\" . nextCh;
					}
				}
				return true;
			}
			# Template family: raw content; the backslash and its follower
			# are copied verbatim.
			self:res: self:res . "\\";
			self:lexer:advance();
			if (self:lexer:pos < self:lexer:length) {
				local String is nextCh: self:lexer:advance();
				self:res: self:res . nextCh;
			}
			return true;
		}
		self:res: self:res . ch;
		self:lexer:advance();
		return true;
	}
}
