#! Package base:compiler:parser:loops
#! Consumes call arguments: positional or `name: value` pairs.
##
## The named-argument heuristic: a lowercase identifier followed by ':'
## names the argument — unless the colon is glued to a path or the next
## token continues an expression. Uppercase-leading identifiers never bind
## as names (they start constructor chains like Color:RED).

Class of Loop is ArgLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'lexer', Token],
		['base', 'compiler', 'lexer', TokenKind],
		['base', 'compiler', 'utils', Chars],
		['base', 'iterator'],
		['base', 'sys', as Conditional()]
	];

	local Parser is parser;
	local Array of NamedArg is args: [];

	## Character classification (the uppercase heuristic for named args).
	local Chars is chars: Chars:init();

	replace Function is init(Parser is parser, Array of NamedArg is args){
		self:parser: parser;
		self:args: args;
	}

	replace Function of Boolean is evaluate(){
		return !self:parser:checkPunct(p: Punctuation:GROUP_CLOSE) && !self:parser:check(kind: TokenKind:EOF, value: '');
	}

	replace Function of Boolean is iteration(LoopControl is control){
		local String is argName: '';
		local Token is tok0: self:parser:peekAhead(offset: 0);
		# FUNCTIONS.md Part II: the flip renames the branch param to `else`
		# while Keyword:ELSE still exists in the preceding generation — the
		# named-arg position accepts those keywords so the seed can parse
		# the flipped spelling. Ordinary keywords still bind only as names
		# when followed by the named-arg punctuation.
		local Boolean is nameLike: tok0:getTokenKind() == TokenKind:IDENTIFIER || (tok0:getTokenKind() == TokenKind:KEYWORD && (tok0:getValue() == 'if' || tok0:getValue() == 'else'));
		Conditional:if(check: { nameLike && self:parser:peekAhead(offset: 1):getValue() == Punctuation:NAMED_ARG:value() }, then: {
			local String is nameVal: tok0:getValue();
			local Boolean is isUpper: self:chars:isUpper(ch: nameVal:charAt(index: 0, default: ''));
			Conditional:if(check: { !isUpper }, then: {
				local Token is nextTok: self:parser:peekAhead(offset: 2);
				local Boolean is isNamed: false;
				Conditional:if(check: { nextTok:getTokenKind() != TokenKind:IDENTIFIER }, then: {
					isNamed: true;
				}, else: {
					isNamed: self:parser:hasWhitespaceAfter(offset: 1);
				});
				Conditional:if(check: { isNamed }, then: {
					local Token is aTok: self:parser:advance();
					argName: aTok:getValue();
					self:parser:advance();
				});
			});
		});
		local Expression is val: self:parser:parseExpression();
		self:args:add(item: NamedArg:init(name: argName, value: val));
		Conditional:if(check: { self:parser:checkPunct(p: Punctuation:SEPARATOR) }, then: {
			self:parser:advance();
			return true;
		});
		return false;
	}

}
