#! Package base:compiler:parser:loops
#! Consumes formal parameter lists: `Type is name`, shorthand `name`
## (Any-typed), and `self: field` receiver fields, each with an optional
## declaration-side default.

Class of Loop is ParamLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', WellKnown],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'iterator']
	];

	local Parser is parser;
	local Array of Parameter is params: [];

	## Well-known names (sentinels, builtin types).
	local WellKnown is names: WellKnown:init();

	replace Function is init(Parser is parser, Array of Parameter is params){
		self:parser: parser;
		self:params: params;
	}

	replace Function of Boolean is evaluate(){
		return !self:parser:checkPunct(p: Punctuation:GROUP_CLOSE) && !self:parser:check(kind: TokenKind:EOF, value: '');
	}

	replace Function of Boolean is iteration(LoopControl is control){
		# `self: field` declares a receiver field parameter.
		if (self:parser:peek():getValue() == self:names:selfIdent() && self:parser:peekAhead(offset: 1):getValue() == ':') {
			self:parser:advance();
			self:parser:advance();
			local Token is fTok: self:parser:advance();
			local Parameter is param: Parameter:init(name: fTok:getValue(), paramType: Type:init(name: self:names:selfFieldMarker()));
			if (self:parser:checkPunct(p: Punctuation:DEFAULT)) {
				self:parser:advance();
				param:setDefault(expr: self:parser:parseExpression());
			}
			self:params:add(item: param);
			if (self:parser:checkPunct(p: Punctuation:SEPARATOR)) {
				self:parser:advance();
				return true;
			}
			return false;
		}
		# Shorthand: a bare identifier is an Any-typed parameter.
		if (self:parser:peekAhead(offset: 1):getValue() == Punctuation:SEPARATOR:value() || self:parser:peekAhead(offset: 1):getValue() == Punctuation:GROUP_CLOSE:value()) {
			local Token is pTok: self:parser:advance();
			self:params:add(item: Parameter:init(name: pTok:getValue(), paramType: Type:init(name: self:names:anyName())));
			if (self:parser:checkPunct(p: Punctuation:SEPARATOR)) {
				self:parser:advance();
				return true;
			}
			return false;
		}
		local Type is pType: self:parser:parseType();
		self:parser:matchKeyword(kw: Keyword:IS);
		local Token is pTok: self:parser:advance();
		local Parameter is param: Parameter:init(name: pTok:getValue(), paramType: pType);
		if (self:parser:checkPunct(p: Punctuation:DEFAULT)) {
			self:parser:advance();
			param:setDefault(expr: self:parser:parseExpression());
		}
		self:params:add(item: param);
		if (self:parser:checkPunct(p: Punctuation:SEPARATOR)) {
			self:parser:advance();
			return true;
		}
		return false;
	}
}
