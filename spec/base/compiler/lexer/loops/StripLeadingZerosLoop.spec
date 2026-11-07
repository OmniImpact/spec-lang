#! Package base:compiler:lexer:loops
#! Strips bare leading zeros from an integer's text (one zero is kept).

Class of Loop is StripLeadingZerosLoop{
	replace Array of String is namespace: ['base', 'compiler', 'lexer', 'loops'];

	replace Array of Array of String is using: [
		['base', 'iterator']
	];

	local String is src;
	local String is res: '';

	replace Function is init(String is src){
		self:src: src;
		self:res: src;
	}

	replace Function of Boolean is evaluate(){
		return self:res:length() > 1 && self:res:charAt(index: 0, default: '') == '0';
	}

	replace Function of Boolean is iteration(LoopControl is control){
		self:res: self:res:substring(start: 1, end: self:res:length());
		return true;
	}
}
