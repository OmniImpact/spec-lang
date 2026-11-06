#! Package base:compiler:parser:loops
#! Consumes `when` arms: guarded `is` arms and the `else` arm, each with a
## statement block or a value expression.

Class of Loop is WhenArmsLoop{
	namespace: ['base', 'compiler', 'parser', 'loops'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'parser', Parser],
		['spec', 'base', 'compiler', 'parser', 'loops', WhenConditionsLoop],
		['spec', 'base', 'compiler', 'parser', 'loops', BlockStatementsLoop],
		['spec', 'base', 'compiler', 'ast', WhenArm],
		['spec', 'base', 'compiler', 'ast', Expression],
		['spec', 'base', 'compiler', 'lexer', Keyword],
		['lib', 'base', 'iterator']
	];

	local Parser is parser;
	local Array of WhenArm is arms: [];

	replace Function is init(Parser is parser, Array of WhenArm is arms){
		self:parser: parser;
		self:arms: arms;
	}

	replace Function of Boolean is evaluate(){
		return !self:parser:checkPunct(p: Punctuation:BLOCK_CLOSE) && !self:parser:check(kind: TokenKind:EOF, value: '');
	}

	replace Function of Boolean is iteration(LoopControl is control){
		if (self:parser:checkKeyword(kw: Keyword:IS)) {
			self:parser:advance();
			local Array of Expression is conds: [];
			While:run(loop: WhenConditionsLoop:init(parser: self:parser, conditions: conds));
			self:parser:matchPunct(p: Punctuation:ARM);

			if (self:parser:checkPunct(p: Punctuation:BLOCK_OPEN)) {
				self:parser:advance();
				local Array of Statement is body: [];
				While:run(loop: BlockStatementsLoop:init(parser: self:parser, stmts: body));
				self:parser:matchPunct(p: Punctuation:BLOCK_CLOSE);
				local WhenArm is arm: WhenArm:init();
				arm:arm(conditions: conds, body: body);
				self:arms:add(item: arm);
			} else {
				local Expression is exprVal: self:parser:parseExpression();
				if (self:parser:checkPunct(p: Punctuation:TERMINATOR)) {
					self:parser:advance();
				}
				local WhenArm is arm: WhenArm:init();
				arm:exprArm(conditions: conds, value: exprVal);
				self:arms:add(item: arm);
			}
			return true;
		}

		if (self:parser:checkKeyword(kw: Keyword:ELSE)) {
			self:parser:advance();
			self:parser:matchPunct(p: Punctuation:ARM);

			if (self:parser:checkPunct(p: Punctuation:BLOCK_OPEN)) {
				self:parser:advance();
				local Array of Statement is body: [];
				While:run(loop: BlockStatementsLoop:init(parser: self:parser, stmts: body));
				self:parser:matchPunct(p: Punctuation:BLOCK_CLOSE);
				local WhenArm is arm: WhenArm:init();
				arm:elseArm(body: body);
				self:arms:add(item: arm);
			} else {
				local Expression is exprVal: self:parser:parseExpression();
				if (self:parser:checkPunct(p: Punctuation:TERMINATOR)) {
					self:parser:advance();
				}
				local WhenArm is arm: WhenArm:init();
				arm:elseExprArm(value: exprVal);
				self:arms:add(item: arm);
			}
			return true;
		}

		# Not an arm: stop scanning (the caller reports the stray token).
		self:parser:advance();
		return false;
	}
}
