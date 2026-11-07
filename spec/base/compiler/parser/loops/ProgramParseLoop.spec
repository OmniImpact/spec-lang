#! Package base:compiler:parser:loops
#! Consumes top-level declarations (classes and enums) until end of input.

Class of Loop is ProgramParseLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'iterator']
	];

	local Parser is parser;
	local Array of ClassInfo is classes: [];

	replace Function is init(Parser is parser, Array of ClassInfo is classes){
		self:parser: parser;
		self:classes: classes;
	}

	replace Function of Boolean is evaluate(){
		return !self:parser:check(kind: TokenKind:EOF, value: '');
	}

	replace Function of Boolean is iteration(LoopControl is control){
		if (self:parser:atEnumHeader()) {
			self:classes:add(item: self:parser:parseEnum());
		} else {
			self:classes:add(item: self:parser:parseClass());
		}
		return true;
	}
}
