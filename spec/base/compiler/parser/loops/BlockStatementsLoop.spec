#! Package base:compiler:parser:loops
#! Consumes statements until the closing brace of a block.

Class of Loop is BlockStatementsLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'parser', Parser],
		['spec', 'base', 'compiler', 'ast', Statement],
		['lib', 'base', 'iterator']
	];

	local Parser is parser;
	local Array of Statement is stmts: [];

	replace Function is init(Parser is parser, Array of Statement is stmts){
		self:parser: parser;
		self:stmts: stmts;
	}

	replace Function of Boolean is evaluate(){
		return !self:parser:checkPunct(p: Punctuation:BLOCK_CLOSE) && !self:parser:check(kind: TokenKind:EOF, value: '');
	}

	replace Function of Boolean is iteration(LoopControl is control){
		self:stmts:add(item: self:parser:parseStatement());
		return true;
	}
}
