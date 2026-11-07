#! Package base:compiler:lexer:loops
#! Accumulates a base-prefixed integer's value while scanning. An
## alphanumeric character that is not a valid digit for the base flags an
## error and is consumed so scanning can continue.

Class of Loop is BaseDigitsLoop{
	replace Array of String is namespace: ['base', 'compiler', 'lexer', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'lexer', Lexer],
		['base', 'iterator']
	];

	local Lexer is lexer;
	local Int is base: 16;
	local Int is value: 0;
	local Int is digitCount: 0;
	local Boolean is hadInvalid: false;

	replace Function is init(Lexer is lexer, Int is base){
		self:lexer: lexer;
		self:base: base;
		self:value: 0;
		self:digitCount: 0;
		self:hadInvalid: false;
	}

	replace Function of Boolean is evaluate(){
		return self:lexer:pos < self:lexer:length;
	}

	replace Function of Boolean is iteration(LoopControl is control){
		local String is ch: self:lexer:source:charAt(index: self:lexer:pos, default: '');
		if (ch == '_') {
			self:lexer:advance();
			return true;
		}
		local Int is d: self:lexer:digitValue(ch: ch);
		if (d >= 0 && d < self:base) {
			self:value: (self:value * self:base) + d;
			self:digitCount: self:digitCount + 1;
			self:lexer:advance();
			return true;
		}
		if (self:lexer:chars:isIdentifierContinue(ch: ch)) {
			self:hadInvalid: true;
			self:lexer:advance();
			return true;
		}
		return false;
	}
}
