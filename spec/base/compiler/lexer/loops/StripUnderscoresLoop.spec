#! Package base:compiler:lexer:loops
#! Builds the underscore-free form of a numeric literal's text.

Class of Loop is StripUnderscoresLoop{
	replace Array of String is namespace: ['base', 'compiler', 'lexer', 'loops'];

	replace Array of Array of String is using: [
		['base', 'iterator']
	];

	local String is src;
	local Int is pos: 0;
	local String is res: '';

	replace Function is init(String is src){
		self:src: src;
		self:pos: 0;
		self:res: '';
	}

	replace Function of Boolean is evaluate(){
		return self:pos < self:src:length();
	}

	replace Function of Boolean is iteration(LoopControl is control){
		local String is ch: self:src:charAt(index: self:pos, default: '');
		self:pos: self:pos + 1;
		if (ch != '_') {
			self:res: self:res . ch;
		}
		return true;
	}
}
