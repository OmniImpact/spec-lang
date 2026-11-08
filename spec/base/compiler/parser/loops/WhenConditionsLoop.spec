#! Package base:compiler:parser:loops
#! Consumes the guard conditions of one `when` arm (up to the ':').

Class of Loop is WhenConditionsLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'ast', Expression],
		['base', 'iterator'],
		['base', 'sys', as Conditional()]
	];

	local Parser is parser;
	local Array of Expression is conditions: [];

	replace Function is init(Parser is parser, Array of Expression is conditions){
		self:parser: parser;
		self:conditions: conditions;
	}

	replace Function of Boolean is evaluate(){
		return !self:parser:checkPunct(p: Punctuation:ARM) && !self:parser:check(kind: TokenKind:EOF, value: '');
	}

	replace Function of Boolean is iteration(LoopControl is control){
		self:conditions:add(item: self:parser:parseExpression());
		if (self:parser:checkPunct(p: Punctuation:SEPARATOR)) {
			self:parser:advance();
			return true;
		}
		return false;
	}
}
