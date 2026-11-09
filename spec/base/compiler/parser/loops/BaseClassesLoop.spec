#! Package base:compiler:parser:loops
#! Consumes the pre-binder parent-class list of a class declaration
## (Class of A, B is Name).

Class of Loop is BaseClassesLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', Parser],
		['base', 'iterator']
,
		['base', 'iterator', as Loops()],
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
		# FUNCTIONS.md Part VI: the parents may be QUALIFIED — the
		# glued-colon path ('base:sys:Loadable') consumes as one parent,
		# the same spelling the type references use.
		local String is base: tok:getValue();
		while(
			evaluate: local Function of Boolean(){ return self:parser:checkPunct(p: Punctuation:DEFAULT); },
			iteration: local Function of Boolean(){
				self:parser:advance();
				base: base . ':' . self:parser:advance():getValue();
				return true;
			}
		);
		self:bases:add(item: base);
		Conditional:if(check: { self:parser:checkPunct(p: Punctuation:SEPARATOR) }, then: {
			self:parser:advance();
			return true;
		});
		return false;
	}
}
