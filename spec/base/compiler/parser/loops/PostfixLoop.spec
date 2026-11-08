#! Package base:compiler:parser:loops
#! Consumes postfix trailers: calls, index accesses, and colon-paths.

Class of Loop is PostfixLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'parser', 'loops', ArgLoop],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', WellKnown],
		['base', 'compiler', 'lexer', Token],
		['base', 'compiler', 'lexer', TokenKind],
		['base', 'iterator'],
		['base', 'iterator', as While()],
		['base', 'sys', as Conditional()]
	];

	local Parser is parser;
	local Expression is currentExpr;

	## Well-known names (the implicit receiver).
	local WellKnown is names: WellKnown:init();

	replace Function is init(Parser is parser, Expression is expr){
		self:parser: parser;
		self:currentExpr: expr;
	}

	replace Function of Boolean is evaluate(){
		Conditional:branch(check: { self:parser:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
			return true;
		});
		Conditional:branch(check: { self:parser:checkPunct(p: Punctuation:BRACKET_OPEN) }, then: {
			return true;
		});
		Conditional:branch(check: { self:parser:checkSymbol(value: '++') || self:parser:checkSymbol(value: '--') }, then: {
			return true;
		});
		Conditional:branch(check: { self:parser:checkPunct(p: Punctuation:ACCESSOR) }, then: {
			# Whitespace before ':' means assignment context, not a path.
			Conditional:branch(check: { self:parser:hasWhitespaceAfter(offset: 0) }, then: {
				return false;
			});
			local Token is nextTok: self:parser:peekAhead(offset: 1);
			return nextTok:getTokenKind() == TokenKind:IDENTIFIER || nextTok:getTokenKind() == TokenKind:KEYWORD || nextTok:getValue() == self:names:wildcard();
		});
		return false;
	}

	replace Function of Boolean is iteration(LoopControl is control){
		Conditional:branch(check: { self:parser:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
			self:parser:advance();
			local Array of NamedArg is args: [];
			While:run(loop: ArgLoop:init(parser: self:parser, args: args));
			self:parser:matchPunct(p: Punctuation:GROUP_CLOSE);

			local Expression is callExpr: Expression:init(kind: ExpressionKind:CALL);
			Conditional:branch(check: { self:currentExpr:kind == ExpressionKind:IDENT }, then: {
				Conditional:branch(check: { self:currentExpr:stringValue == 'While' }, then: {
					callExpr:methodTarget: self:currentExpr;
					callExpr:methodName: 'loop';
				}, otherwise: {
					# A bare identifier followed by '(' calls self.
					local Expression is selfTarget: Expression:init(kind: ExpressionKind:IDENT);
					selfTarget:stringValue: self:names:selfIdent();
					callExpr:methodTarget: selfTarget;
					callExpr:methodName: self:currentExpr:stringValue;
				});
			}, otherwise: {
				callExpr:methodTarget: self:currentExpr;
				callExpr:methodName: '';
			});
			callExpr:methodArgs: args;
			self:currentExpr: callExpr;
			return true;
		});
		Conditional:branch(check: { self:parser:checkPunct(p: Punctuation:BRACKET_OPEN) }, then: {
			self:parser:advance();
			local Expression is idxExpr: self:parser:parseExpression();
			self:parser:matchPunct(p: Punctuation:BRACKET_CLOSE);

			local Expression is indexNode: Expression:init(kind: ExpressionKind:INDEX);
			indexNode:leftExpr: self:currentExpr;
			indexNode:rightExpr: idxExpr;
			self:currentExpr: indexNode;
			return true;
		});
		Conditional:branch(check: { self:parser:checkSymbol(value: '++') }, then: {
			self:parser:advance();
			local Expression is u: Expression:init(kind: ExpressionKind:UNARY);
			u:unaryOp: 'post++';
			u:unaryExpr: self:currentExpr;
			self:currentExpr: u;
			return true;
		});
		Conditional:branch(check: { self:parser:checkSymbol(value: '--') }, then: {
			self:parser:advance();
			local Expression is u: Expression:init(kind: ExpressionKind:UNARY);
			u:unaryOp: 'post--';
			u:unaryExpr: self:currentExpr;
			self:currentExpr: u;
			return true;
		});
		Conditional:branch(check: { self:parser:checkPunct(p: Punctuation:ACCESSOR) }, then: {
			self:parser:advance();
			local Token is mTok: self:parser:advance();
			local String is method: mTok:getValue();

			Conditional:branch(check: { self:parser:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
				self:parser:advance();
				local Array of NamedArg is args: [];
				While:run(loop: ArgLoop:init(parser: self:parser, args: args));
				self:parser:matchPunct(p: Punctuation:GROUP_CLOSE);

				local Expression is callExpr: Expression:init(kind: ExpressionKind:CALL);
				callExpr:methodTarget: self:currentExpr;
				callExpr:methodName: method;
				callExpr:methodArgs: args;
				self:currentExpr: callExpr;
				return true;
			});

			# No parenthesis: on a PATH/IDENT root the colon extends a
			# namespace path (Class:member chains); on any other expression
			# it is a FIELD_ACCESS on the result (call():field).
			Conditional:branch(check: { self:currentExpr:kind != ExpressionKind:PATH && self:currentExpr:kind != ExpressionKind:IDENT }, then: {
				local Expression is fa: Expression:init(kind: ExpressionKind:FIELD_ACCESS);
				fa:leftExpr: self:currentExpr;
				fa:stringValue: method;
				self:currentExpr: fa;
				return true;
			});
			local Array of String is segs: [];
			Conditional:branch(check: { self:currentExpr:kind == ExpressionKind:PATH }, then: {
				self:currentExpr:pathSegments:each(action: local Function(String is s){
					segs:add(item: s);
				});
			}, otherwise: {
				Conditional:branch(check: { self:currentExpr:kind == ExpressionKind:IDENT }, then: {
					segs:add(item: self:currentExpr:stringValue);
				});
			});
			segs:add(item: method);
			local Expression is pathExpr: Expression:init(kind: ExpressionKind:PATH);
			pathExpr:pathSegments: segs;
			pathExpr:stringValue: self:currentExpr:stringValue . ':' . method;
			self:currentExpr: pathExpr;
			return true;
		});
		return false;
	}
}
