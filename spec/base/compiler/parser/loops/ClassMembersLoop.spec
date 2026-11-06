#! Package base:compiler:parser:loops
#! Consumes class member declarations until the closing brace.

Class of Loop is ClassMembersLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'parser', Parser],
		['spec', 'base', 'compiler', 'ast', Member],
		['lib', 'base', 'iterator']
	];

	local Parser is parser;
	local Array of Member is members: [];

	replace Function is init(Parser is parser, Array of Member is members){
		self:parser: parser;
		self:members: members;
	}

	replace Function of Boolean is evaluate(){
		return !self:parser:checkPunct(p: Punctuation:BLOCK_CLOSE) && !self:parser:check(kind: TokenKind:EOF, value: '');
	}

	replace Function of Boolean is iteration(LoopControl is control){
		self:members:add(item: self:parser:parseMember());
		return true;
	}
}
