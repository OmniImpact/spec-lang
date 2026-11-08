#! Package base:compiler:parser:loops
#! Consumes the pre-binder parent-class list of a class declaration
## (Class of A, B is Name).

Class of Loop is BaseClassesLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', Parser],
		['base', 'iterator']
,
		['base', 'compiler', 'lexer', Token],
		['base', 'sys', as Conditional()]
	];

	local Parser is parser;
	local Array of String is bases: [];

	replace Function is init(Parser is parser, Array of String is bases){
		self:parser: parser;
		self:bases: bases;
	}

	replace Function of Boolean is evaluate(){
		return !self:parser:checkPunct(p: Punctuation:BLOCK_OPEN) && !self:parser:check(kind: TokenKind:EOF, value: '');
	}

	replace Function of Boolean is iteration(LoopControl is control){
		local Token is tok: self:parser:advance();
		self:bases:add(item: tok:getValue());
		Conditional:if(check: { self:parser:checkPunct(p: Punctuation:SEPARATOR) }, then: {
			self:parser:advance();
			return true;
		});
		return false;
	}
}
