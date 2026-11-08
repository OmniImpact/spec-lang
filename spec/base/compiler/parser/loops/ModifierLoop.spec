#! Package base:compiler:parser:loops
#! Consumes the modifier run preceding a member declaration
## (local, contained, replace, merge).

Class of Loop is ModifierLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'iterator']
,
		['base', 'compiler', 'lexer', Token]
	];

	local Parser is parser;
	local Array of String is mods: [];

	replace Function is init(Parser is parser, Array of String is mods){
		self:parser: parser;
		self:mods: mods;
	}

	replace Function of Boolean is evaluate(){
		return self:parser:checkKeyword(kw: Keyword:LOCAL) || self:parser:checkKeyword(kw: Keyword:CONTAINED) ||
			self:parser:checkKeyword(kw: Keyword:REPLACE) || self:parser:checkKeyword(kw: Keyword:MERGE);
	}

	replace Function of Boolean is iteration(LoopControl is control){
		local Token is tok: self:parser:advance();
		self:mods:add(item: tok:getValue());
		return true;
	}
}
