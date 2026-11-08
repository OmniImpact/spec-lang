#! Package base:compiler:parser:loops
#! Consumes comma-separated `key: value` map literal pairs.

Class of Loop is MapItemsLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'ast', Expression],
		['base', 'iterator']
,
		['base', 'compiler', 'lexer', Token],
		['base', 'sys', as Conditional()]
	];

	local Parser is parser;
	local Array of Expression is keys: [];
	local Array of Expression is values: [];

	replace Function is init(Parser is parser, Array of Expression is keys, Array of Expression is values){
		self:parser: parser;
		self:keys: keys;
		self:values: values;
	}

	replace Function of Boolean is evaluate(){
		return !self:parser:checkPunct(p: Punctuation:BRACKET_CLOSE) && !self:parser:check(kind: TokenKind:EOF, value: '');
	}

	replace Function of Boolean is iteration(LoopControl is control){
		local Expression is k: self:parser:parseExpression();
		self:parser:matchPunct(p: Punctuation:PAIR);
		local Expression is v: self:parser:parseExpression();
		self:keys:add(item: k);
		self:values:add(item: v);
		if (self:parser:checkPunct(p: Punctuation:SEPARATOR)) {
			self:parser:advance();
			return true;
		}
		return false;
	}
}
