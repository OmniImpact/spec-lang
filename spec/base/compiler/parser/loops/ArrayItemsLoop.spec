#! Package base:compiler:parser:loops
#! Consumes comma-separated array literal items.

Class of Loop is ArrayItemsLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'ast', Expression],
		['base', 'iterator']
,
		['base', 'compiler', 'lexer', Token]
	];

	local Parser is parser;
	local Array of Expression is items: [];

	replace Function is init(Parser is parser, Array of Expression is items){
		self:parser: parser;
		self:items: items;
	}

	replace Function of Boolean is evaluate(){
		return !self:parser:checkPunct(p: Punctuation:BRACKET_CLOSE) && !self:parser:check(kind: TokenKind:EOF, value: '');
	}

	replace Function of Boolean is iteration(LoopControl is control){
		self:items:add(item: self:parser:parseExpression());
		if (self:parser:checkPunct(p: Punctuation:SEPARATOR)) {
			self:parser:advance();
			return true;
		}
		return false;
	}
}
