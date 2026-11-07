#! Package base:compiler:parser:loops
#! Consumes enum variant declarations: `Name`, `Name(params)`, and an
## optional `: value` override. Untagged variants receive their ordinal.

Class of Loop is EnumVariantsLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'parser', 'loops', ParamLoop],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'iterator']
	];

	local Parser is parser;
	local Array of Member is members: [];
	local String is backingType: 'Int';
	local Int is count: 0;

	replace Function is init(Parser is parser, Array of Member is members, String is backingType){
		self:parser: parser;
		self:members: members;
		self:backingType: backingType;
		self:count: 0;
	}

	replace Function of Boolean is evaluate(){
		return !self:parser:checkPunct(p: Punctuation:BLOCK_CLOSE) && !self:parser:check(kind: TokenKind:EOF, value: '');
	}

	replace Function of Boolean is iteration(LoopControl is control){
		local Token is vTok: self:parser:advance();
		local String is vName: vTok:getValue();
		local Array of Parameter is vParams: [];
		if (self:parser:checkPunct(p: Punctuation:GROUP_OPEN)) {
			self:parser:advance();
			While:run(loop: ParamLoop:init(parser: self:parser, params: vParams));
			self:parser:matchPunct(p: Punctuation:GROUP_CLOSE);
		}
		local Expression is valExpr: Expression:init(kind: ExpressionKind:NUMBER);
		local Boolean is hasInit: false;
		if (self:parser:checkPunct(p: Punctuation:TAG)) {
			self:parser:advance();
			valExpr: self:parser:parseExpression();
			hasInit: true;
		} else {
			# Untagged variant: its ordinal is the value.
			valExpr:stringValue: '' . self:count;
			valExpr:intValue: self:count;
			hasInit: true;
		}
		self:count: self:count + 1;

		local Member is m: Member:init(kind: MemberKind:FIELD);
		m:modifiers: ['static', 'local'];
		m:memberType: Type:init(name: self:backingType);
		m:name: vName;
		m:params: vParams;
		m:initExpr: valExpr;
		m:hasInit: hasInit;
		self:members:add(item: m);

		if (self:parser:checkPunct(p: Punctuation:SEPARATOR)) {
			self:parser:advance();
			return true;
		}
		return false;
	}
}
