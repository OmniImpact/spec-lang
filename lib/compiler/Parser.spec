#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, and Linter.

## Recursive-descent AST parser converting token streams into [base:meta:ProgramNode] trees.
Class is Parser{

	replace Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:*,
		base:reflect:Type,
		base:reflect:ClassInfo,
		base:reflect:Member,
		base:reflect:Parameter,
		compiler:Token,
		base:meta:*
	];

	local Array of Token is tokens: [];
	local Int is pos: 0;
	local Int is length: 0;
	local String is sourceFile: '';
	local Array of String is errors: [];
	# Nesting depth of fancy-string desugaring: 0 at statement level, >= 1
	# inside a template hole (where inner strings stay plain — no nested
	# template expansion).
	local Int is templateDepth: 0;

	Function is setTemplateDepth(Int is depth){
		self:templateDepth: depth;
	}

	Class of Loop is EnumVariantsLoop{
		local Parser is parser;
		local Array of Member is members;
		local String is backingType;
		local Int is count: 0;

		replace Function is init(Parser is parser, Array of Member is members, String is backingType){
			self:parser: parser;
			self:members: members;
			self:backingType: backingType;
			self:count: 0;
		}

		replace Function of Boolean is evaluate(){
			return !self:parser:check(kind: 'SYMBOL', value: '}') && !self:parser:check(kind: 'EOF', value: '');
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local Token is vTok: self:parser:advance();
			local String is vName: vTok:getValue();
			local Array of Parameter is vParams: [];
			if (self:parser:check(kind: 'SYMBOL', value: '(')) {
				self:parser:advance();
				While:run(loop: ParamLoop:init(parser: self:parser, params: vParams));
				self:parser:matchToken(kind: 'SYMBOL', value: ')');
			}
			local Expression is valExpr: Expression:init(kind: 'NUMBER');
			local Boolean is hasInit: false;
			if (self:parser:check(kind: 'SYMBOL', value: ':')) {
				self:parser:advance();
				valExpr: self:parser:parseExpression();
				hasInit: true;
			} else {
				valExpr: Expression:init(kind: 'NUMBER');
				valExpr:stringValue: '' . self:count;
				valExpr:intValue: self:count;
				hasInit: true;
			}
			self:count: self:count + 1;

			local Member is m: Member:init(kind: 'FIELD');
			m:modifiers: ['static', 'local'];
			m:memberType: Type:init(name: self:backingType);
			m:name: vName;
			m:params: vParams;
			m:initExpr: valExpr;
			m:hasInit: hasInit;
			self:members:add(item: m);

			if (self:parser:check(kind: 'SYMBOL', value: ',')) {
				self:parser:advance();
				return true;
			}
			return false;
		}
	}

	Class of Loop is ProgramParseLoop{
		local Parser is parser;
		local Array of ClassInfo is classes;

		replace Function is init(Parser is parser, Array of ClassInfo is classes){
			self:parser: parser;
			self:classes: classes;
		}

		replace Function of Boolean is evaluate(){
			return !parser:check(kind: 'EOF', value: '');
		}

		replace Function of Boolean is iteration(LoopControl is control){
			if (self:parser:check(kind: 'KEYWORD', value: 'Enum') || self:parser:peek():getValue() == 'Enum') {
				self:classes:add(item: self:parser:parseEnum());
			} else {
				self:classes:add(item: self:parser:parseClass());
			}
			return true;
		}
	}

	Class of Loop is ClassMembersLoop{
		local Parser is parser;
		local Array of Member is members;

		replace Function is init(Parser is parser, Array of Member is members){
			self:parser: parser;
			self:members: members;
		}

		replace Function of Boolean is evaluate(){
			return !parser:check(kind: 'SYMBOL', value: '}') && !parser:check(kind: 'EOF', value: '');
		}

		replace Function of Boolean is iteration(LoopControl is control){
			members:add(item: parser:parseMember());
			return true;
		}
	}

	Class of Loop is BaseClassesLoop{
		local Parser is parser;
		local Array of String is bases;

		replace Function is init(Parser is parser, Array of String is bases){
			self:parser: parser;
			self:bases: bases;
		}

		replace Function of Boolean is evaluate(){
			return !parser:check(kind: 'SYMBOL', value: '{') && !parser:check(kind: 'EOF', value: '');
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local Token is tok: parser:advance();
			bases:add(item: tok:getValue());
			if (parser:check(kind: 'SYMBOL', value: ',')) {
				parser:advance();
				return true;
			}
			return false;
		}
	}

	Class of Loop is BlockStatementsLoop{
		local Parser is parser;
		local Array of Statement is stmts;

		replace Function is init(Parser is parser, Array of Statement is stmts){
			self:parser: parser;
			self:stmts: stmts;
		}

		replace Function of Boolean is evaluate(){
			return !parser:check(kind: 'SYMBOL', value: '}') && !parser:check(kind: 'EOF', value: '');
		}

		replace Function of Boolean is iteration(LoopControl is control){
			stmts:add(item: parser:parseStatement());
			return true;
		}
	}

	Class of Loop is WhenConditionsLoop{
		local Parser is parser;
		local Array of Expression is conditions;

		replace Function is init(Parser is parser, Array of Expression is conditions){
			self:parser: parser;
			self:conditions: conditions;
		}

		replace Function of Boolean is evaluate(){
			return !self:parser:check(kind: 'SYMBOL', value: ':') && !self:parser:check(kind: 'EOF', value: '');
		}

		replace Function of Boolean is iteration(LoopControl is control){
			self:conditions:add(item: self:parser:parseExpression());
			if (self:parser:check(kind: 'SYMBOL', value: ',')) {
				self:parser:advance();
				return true;
			}
			return false;
		}
	}

	Class of Loop is WhenArmsLoop{
		local Parser is parser;
		local Array of WhenArm is arms;

		replace Function is init(Parser is parser, Array of WhenArm is arms){
			self:parser: parser;
			self:arms: arms;
		}

		replace Function of Boolean is evaluate(){
			return !self:parser:check(kind: 'SYMBOL', value: '}') && !self:parser:check(kind: 'EOF', value: '');
		}

		replace Function of Boolean is iteration(LoopControl is control){
			if (self:parser:check(kind: 'KEYWORD', value: 'is')) {
				self:parser:advance();
				local Array of Expression is conds: [];
				While:run(loop: WhenConditionsLoop:init(parser: self:parser, conditions: conds));
				self:parser:matchToken(kind: 'SYMBOL', value: ':');

				if (self:parser:check(kind: 'SYMBOL', value: '{')) {
					self:parser:advance();
					local Array of Statement is body: [];
					While:run(loop: BlockStatementsLoop:init(parser: self:parser, stmts: body));
					self:parser:matchToken(kind: 'SYMBOL', value: '}');
					local WhenArm is arm: WhenArm:init();
					arm:arm(conditions: conds, body: body);
					self:arms:add(item: arm);
				} else {
					local Expression is exprVal: self:parser:parseExpression();
					if (self:parser:check(kind: 'SYMBOL', value: ';')) {
						self:parser:advance();
					}
					local WhenArm is arm: WhenArm:init();
					arm:exprArm(conditions: conds, value: exprVal);
					self:arms:add(item: arm);
				}
				return true;
			}

			if (self:parser:check(kind: 'KEYWORD', value: 'else')) {
				self:parser:advance();
				self:parser:matchToken(kind: 'SYMBOL', value: ':');

				if (self:parser:check(kind: 'SYMBOL', value: '{')) {
					self:parser:advance();
					local Array of Statement is body: [];
					While:run(loop: BlockStatementsLoop:init(parser: self:parser, stmts: body));
					self:parser:matchToken(kind: 'SYMBOL', value: '}');
					local WhenArm is arm: WhenArm:init();
					arm:elseArm(body: body);
					self:arms:add(item: arm);
				} else {
					local Expression is exprVal: self:parser:parseExpression();
					if (self:parser:check(kind: 'SYMBOL', value: ';')) {
						self:parser:advance();
					}
					local WhenArm is arm: WhenArm:init();
					arm:elseExprArm(value: exprVal);
					self:arms:add(item: arm);
				}
				return true;
			}

			self:parser:advance();
			return false;
		}
	}

	Class of Loop is ArrayItemsLoop{
		local Parser is parser;
		local Array of Expression is items;

		replace Function is init(Parser is parser, Array of Expression is items){
			self:parser: parser;
			self:items: items;
		}

		replace Function of Boolean is evaluate(){
			return !parser:check(kind: 'SYMBOL', value: ']') && !parser:check(kind: 'EOF', value: '');
		}

		replace Function of Boolean is iteration(LoopControl is control){
			items:add(item: parser:parseExpression());
			if (parser:check(kind: 'SYMBOL', value: ',')) {
				parser:advance();
				return true;
			}
			return false;
		}
	}

	Class of Loop is MapItemsLoop{
		local Parser is parser;
		local Array of Expression is keys;
		local Array of Expression is values;

		replace Function is init(Parser is parser, Array of Expression is keys, Array of Expression is values){
			self:parser: parser;
			self:keys: keys;
			self:values: values;
		}

		replace Function of Boolean is evaluate(){
			return !self:parser:check(kind: 'SYMBOL', value: ']') && !self:parser:check(kind: 'EOF', value: '');
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local Expression is k: self:parser:parseExpression();
			self:parser:matchToken(kind: 'SYMBOL', value: ':');
			local Expression is v: self:parser:parseExpression();
			self:keys:add(item: k);
			self:values:add(item: v);
			if (self:parser:check(kind: 'SYMBOL', value: ',')) {
				self:parser:advance();
				return true;
			}
			return false;
		}
	}

	Class of Loop is ModifierLoop{
		local Parser is parser;
		local Array of String is mods;

		replace Function is init(Parser is parser, Array of String is mods){
			self:parser: parser;
			self:mods: mods;
		}

		replace Function of Boolean is evaluate(){
			return parser:check(kind: 'KEYWORD', value: 'local') || parser:check(kind: 'KEYWORD', value: 'contained') ||
				parser:check(kind: 'KEYWORD', value: 'replace') || parser:check(kind: 'KEYWORD', value: 'merge');
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local Token is tok: parser:advance();
			mods:add(item: tok:getValue());
			return true;
		}
	}

	Class of Loop is ParamLoop{
		local Parser is parser;
		local Array of Parameter is params;

		replace Function is init(Parser is parser, Array of Parameter is params){
			self:parser: parser;
			self:params: params;
		}

		replace Function of Boolean is evaluate(){
			return !parser:check(kind: 'SYMBOL', value: ')') && !parser:check(kind: 'EOF', value: '');
		}

		replace Function of Boolean is iteration(LoopControl is control){
			if (self:parser:peek():getValue() == 'self' && self:parser:peekAhead(offset: 1):getValue() == ':') {
				self:parser:advance();
				self:parser:advance();
				local Token is fTok: self:parser:advance();
				local Parameter is param: Parameter:init(name: fTok:getValue(), paramType: Type:init(name: 'SELF_FIELD'));
				if (self:parser:check(kind: 'SYMBOL', value: ':')) {
					self:parser:advance();
					param:setDefault(expr: self:parser:parseExpression());
				}
				self:params:add(item: param);
				if (self:parser:check(kind: 'SYMBOL', value: ',')) {
					self:parser:advance();
					return true;
				}
				return false;
			}
			if (self:parser:peekAhead(offset: 1):getValue() == ',' || self:parser:peekAhead(offset: 1):getValue() == ')') {
				local Token is pTok: self:parser:advance();
				local String is pName: pTok:getValue();
				self:params:add(item: Parameter:init(name: pName, paramType: Type:init(name: 'Any')));
				if (self:parser:check(kind: 'SYMBOL', value: ',')) {
					self:parser:advance();
					return true;
				}
				return false;
			}
			local Type is pType: self:parser:parseType();
			self:parser:matchToken(kind: 'KEYWORD', value: 'is');
			local Token is pTok: self:parser:advance();
			local Parameter is param: Parameter:init(name: pTok:getValue(), paramType: pType);
			if (self:parser:check(kind: 'SYMBOL', value: ':')) {
				self:parser:advance();
				param:setDefault(expr: self:parser:parseExpression());
			}
			self:params:add(item: param);
			if (self:parser:check(kind: 'SYMBOL', value: ',')) {
				self:parser:advance();
				return true;
			}
			return false;
		}
	}

	Class of Loop is ArgLoop{
		local Parser is parser;
		local Array of NamedArg is args;

		replace Function is init(Parser is parser, Array of NamedArg is args){
			self:parser: parser;
			self:args: args;
		}

		replace Function of Boolean is evaluate(){
			return !parser:check(kind: 'SYMBOL', value: ')') && !parser:check(kind: 'EOF', value: '');
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is argName: '';
			local Token is tok0: self:parser:peekAhead(offset: 0);
			if (tok0:getKind() == 'IDENTIFIER' && self:parser:peekAhead(offset: 1):getValue() == ':') {
				local String is nameVal: tok0:getValue();
				local String is firstChar: nameVal:charAt(index: 0, default: '');
				local String is uppers: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
				local Boolean is isUpper: uppers:indexOf(search: firstChar, default: -1) != -1;
				if (!isUpper) {
					local Token is nextTok: self:parser:peekAhead(offset: 2);
					local Boolean is isNamed: false;
					if (nextTok:getKind() != 'IDENTIFIER') {
						isNamed: true;
					} else {
						isNamed: self:parser:hasWhitespaceAfter(offset: 1);
					}
					if (isNamed) {
						local Token is aTok: self:parser:advance();
						argName: aTok:getValue();
						self:parser:advance();
					}
				}
			}
			local Expression is val: self:parser:parseExpression();
			self:args:add(item: NamedArg:init(name: argName, value: val));
			if (self:parser:check(kind: 'SYMBOL', value: ',')) {
				self:parser:advance();
				return true;
			}
			return false;
		}
	}

	Class of Loop is PostfixLoop{
		local Parser is parser;
		local Expression is currentExpr;

		replace Function is init(Parser is parser, Expression is expr){
			self:parser: parser;
			self:currentExpr: expr;
		}

		replace Function of Boolean is evaluate(){
			if (self:parser:check(kind: 'SYMBOL', value: '(')) {
				return true;
			}
			if (self:parser:check(kind: 'SYMBOL', value: '[')) {
				return true;
			}
			if (self:parser:check(kind: 'SYMBOL', value: ':')) {
				if (self:parser:hasWhitespaceAfter(offset: 0)) {
					return false;
				}
				local Token is nextTok: self:parser:peekAhead(offset: 1);
				local String is nKind: nextTok:getKind();
				return nKind == 'IDENTIFIER' || nKind == 'KEYWORD' || nextTok:getValue() == '*';
			}
			return false;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			if (self:parser:check(kind: 'SYMBOL', value: '(')) {
				self:parser:advance();
				local Array of NamedArg is args: [];
				While:run(loop: ArgLoop:init(parser: self:parser, args: args));
				self:parser:matchToken(kind: 'SYMBOL', value: ')');

				local Expression is callExpr: Expression:init(kind: 'CALL');
				if (self:currentExpr:getKind() == 'IDENT') {
					local Expression is selfTarget: Expression:init(kind: 'IDENT');
					selfTarget:stringValue: 'self';
					callExpr:methodTarget: selfTarget;
					callExpr:methodName: self:currentExpr:stringValue;
				} else {
					callExpr:methodTarget: self:currentExpr;
					callExpr:methodName: '';
				}
				callExpr:methodArgs: args;
				self:currentExpr: callExpr;
				return true;
			}
			if (self:parser:check(kind: 'SYMBOL', value: '[')) {
				self:parser:advance();
				local Expression is idxExpr: self:parser:parseExpression();
				self:parser:matchToken(kind: 'SYMBOL', value: ']');

				local Expression is indexNode: Expression:init(kind: 'INDEX');
				indexNode:leftExpr: self:currentExpr;
				indexNode:rightExpr: idxExpr;
				self:currentExpr: indexNode;
				return true;
			}
			if (self:parser:check(kind: 'SYMBOL', value: ':')) {
				self:parser:advance();
				local Token is mTok: self:parser:advance();
				local String is method: mTok:getValue();

				if (self:parser:check(kind: 'SYMBOL', value: '(')) {
					self:parser:advance();
					local Array of NamedArg is args: [];
					While:run(loop: ArgLoop:init(parser: self:parser, args: args));
					self:parser:matchToken(kind: 'SYMBOL', value: ')');

					local Expression is callExpr: Expression:init(kind: 'CALL');
					callExpr:methodTarget: self:currentExpr;
					callExpr:methodName: method;
					callExpr:methodArgs: args;
					self:currentExpr: callExpr;
					return true;
				}

				local Array of String is segs: [];
				if (self:currentExpr:getKind() == 'PATH') {
					self:currentExpr:pathSegments:each(action: local Function(String is s){
						segs:add(item: s);
					});
				} else if (self:currentExpr:getKind() == 'IDENT') {
					segs:add(item: self:currentExpr:stringValue);
				}
				segs:add(item: method);
				local Expression is pathExpr: Expression:init(kind: 'PATH');
				pathExpr:pathSegments: segs;
				pathExpr:stringValue: self:currentExpr:stringValue . ':' . method;
				self:currentExpr: pathExpr;
				return true;
			}
			return false;
		}
	}

	Class of Loop is LogicalOrLoop{
		local Parser is parser;
		local Expression is currentExpr;

		replace Function is init(Parser is parser, Expression is expr){
			self:parser: parser;
			self:currentExpr: expr;
		}

		replace Function of Boolean is evaluate(){
			local Token is tok: self:parser:peek();
			return tok:getValue() == '||';
		}

		replace Function of Boolean is iteration(LoopControl is control){
			self:parser:advance();
			local Expression is right: self:parser:parseLogicalAnd();

			local Expression is binExpr: Expression:init(kind: 'BINARY');
			binExpr:binaryOp: '||';
			binExpr:leftExpr: self:currentExpr;
			binExpr:rightExpr: right;
			self:currentExpr: binExpr;
			return true;
		}
	}

	Class of Loop is LogicalAndLoop{
		local Parser is parser;
		local Expression is currentExpr;

		replace Function is init(Parser is parser, Expression is expr){
			self:parser: parser;
			self:currentExpr: expr;
		}

		replace Function of Boolean is evaluate(){
			local Token is tok: self:parser:peek();
			return tok:getValue() == '&&';
		}

		replace Function of Boolean is iteration(LoopControl is control){
			self:parser:advance();
			local Expression is right: self:parser:parseEquality();

			local Expression is binExpr: Expression:init(kind: 'BINARY');
			binExpr:binaryOp: '&&';
			binExpr:leftExpr: self:currentExpr;
			binExpr:rightExpr: right;
			self:currentExpr: binExpr;
			return true;
		}
	}

	Class of Loop is ShiftLoop{
		local Parser is parser;
		local Expression is currentExpr;

		replace Function is init(Parser is parser, Expression is expr){
			self:parser: parser;
			self:currentExpr: expr;
		}

		replace Function of Boolean is evaluate(){
			local String is val: self:parser:peek():getValue();
			return val == '<<' || val == '>>';
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is op: self:parser:advance():getValue();
			local Expression is right: self:parser:parseAdditive();
			local Expression is binExpr: Expression:init(kind: 'BINARY');
			binExpr:binaryOp: op;
			binExpr:leftExpr: self:currentExpr;
			binExpr:rightExpr: right;
			self:currentExpr: binExpr;
			return true;
		}
	}

	Class of Loop is BitAndLoop{
		local Parser is parser;
		local Expression is currentExpr;

		replace Function is init(Parser is parser, Expression is expr){
			self:parser: parser;
			self:currentExpr: expr;
		}

		replace Function of Boolean is evaluate(){
			return self:parser:peek():getValue() == '&';
		}

		replace Function of Boolean is iteration(LoopControl is control){
			self:parser:advance();
			local Expression is right: self:parser:parseEquality();
			local Expression is binExpr: Expression:init(kind: 'BINARY');
			binExpr:binaryOp: '&';
			binExpr:leftExpr: self:currentExpr;
			binExpr:rightExpr: right;
			self:currentExpr: binExpr;
			return true;
		}
	}

	Class of Loop is BitXorLoop{
		local Parser is parser;
		local Expression is currentExpr;

		replace Function is init(Parser is parser, Expression is expr){
			self:parser: parser;
			self:currentExpr: expr;
		}

		replace Function of Boolean is evaluate(){
			return self:parser:peek():getValue() == '^';
		}

		replace Function of Boolean is iteration(LoopControl is control){
			self:parser:advance();
			local Expression is right: self:parser:parseBitAnd();
			local Expression is binExpr: Expression:init(kind: 'BINARY');
			binExpr:binaryOp: '^';
			binExpr:leftExpr: self:currentExpr;
			binExpr:rightExpr: right;
			self:currentExpr: binExpr;
			return true;
		}
	}

	Class of Loop is BitOrLoop{
		local Parser is parser;
		local Expression is currentExpr;

		replace Function is init(Parser is parser, Expression is expr){
			self:parser: parser;
			self:currentExpr: expr;
		}

		replace Function of Boolean is evaluate(){
			return self:parser:peek():getValue() == '|';
		}

		replace Function of Boolean is iteration(LoopControl is control){
			self:parser:advance();
			local Expression is right: self:parser:parseBitXor();
			local Expression is binExpr: Expression:init(kind: 'BINARY');
			binExpr:binaryOp: '|';
			binExpr:leftExpr: self:currentExpr;
			binExpr:rightExpr: right;
			self:currentExpr: binExpr;
			return true;
		}
	}

	Class of Loop is EqualityLoop{
		local Parser is parser;
		local Expression is currentExpr;

		replace Function is init(Parser is parser, Expression is expr){
			self:parser: parser;
			self:currentExpr: expr;
		}

		replace Function of Boolean is evaluate(){
			local Token is tok: self:parser:peek();
			local String is val: tok:getValue();
			return val == '==' || val == '!=' || val == 'is';
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local Token is opTok: self:parser:advance();
			local String is op: opTok:getValue();
			if (op == 'is') {
				op: '==';
			}
			local Expression is right: self:parser:parseRelational();

			local Expression is binExpr: Expression:init(kind: 'BINARY');
			binExpr:binaryOp: op;
			binExpr:leftExpr: self:currentExpr;
			binExpr:rightExpr: right;
			self:currentExpr: binExpr;
			return true;
		}
	}

	Class of Loop is RelationalLoop{
		local Parser is parser;
		local Expression is currentExpr;

		replace Function is init(Parser is parser, Expression is expr){
			self:parser: parser;
			self:currentExpr: expr;
		}

		replace Function of Boolean is evaluate(){
			local Token is tok: self:parser:peek();
			local String is val: tok:getValue();
			return val == '<' || val == '<=' || val == '>' || val == '>=';
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local Token is opTok: self:parser:advance();
			local String is op: opTok:getValue();
			local Expression is right: self:parser:parseConcat();

			local Expression is binExpr: Expression:init(kind: 'BINARY');
			binExpr:binaryOp: op;
			binExpr:leftExpr: self:currentExpr;
			binExpr:rightExpr: right;
			self:currentExpr: binExpr;
			return true;
		}
	}

	Class of Loop is ConcatLoop{
		local Parser is parser;
		local Expression is currentExpr;

		replace Function is init(Parser is parser, Expression is expr){
			self:parser: parser;
			self:currentExpr: expr;
		}

		replace Function of Boolean is evaluate(){
			local Token is tok: self:parser:peek();
			return tok:getValue() == '.';
		}

		replace Function of Boolean is iteration(LoopControl is control){
			self:parser:advance();
			local Expression is right: self:parser:parseAdditive();

			local Expression is binExpr: Expression:init(kind: 'BINARY');
			binExpr:binaryOp: '.';
			binExpr:leftExpr: self:currentExpr;
			binExpr:rightExpr: right;
			self:currentExpr: binExpr;
			return true;
		}
	}

	Class of Loop is AdditiveLoop{
		local Parser is parser;
		local Expression is currentExpr;

		replace Function is init(Parser is parser, Expression is expr){
			self:parser: parser;
			self:currentExpr: expr;
		}

		replace Function of Boolean is evaluate(){
			local Token is tok: self:parser:peek();
			local String is val: tok:getValue();
			return val == '+' || val == '-';
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local Token is opTok: self:parser:advance();
			local String is op: opTok:getValue();
			local Expression is right: self:parser:parseMultiplicative();

			local Expression is binExpr: Expression:init(kind: 'BINARY');
			binExpr:binaryOp: op;
			binExpr:leftExpr: self:currentExpr;
			binExpr:rightExpr: right;
			self:currentExpr: binExpr;
			return true;
		}
	}

	Class of Loop is MultiplicativeLoop{
		local Parser is parser;
		local Expression is currentExpr;

		replace Function is init(Parser is parser, Expression is expr){
			self:parser: parser;
			self:currentExpr: expr;
		}

		replace Function of Boolean is evaluate(){
			local Token is tok: self:parser:peek();
			local String is val: tok:getValue();
			return val == '*' || val == '/' || val == '%';
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local Token is opTok: self:parser:advance();
			local String is op: opTok:getValue();
			local Expression is right: self:parser:parseUnary();

			local Expression is binExpr: Expression:init(kind: 'BINARY');
			binExpr:binaryOp: op;
			binExpr:leftExpr: self:currentExpr;
			binExpr:rightExpr: right;
			self:currentExpr: binExpr;
			return true;
		}
	}

	## Initializes a parser with a token array emitted by [Lexer].
	##
	## @param tokens: Array of [Token] items.
	replace Function is init(Array of Token is tokens){
		self:tokens: tokens;
		self:length: tokens:length();
		self:pos: 0;
		self:sourceFile: '';
		self:errors: [];
	}

	Function is setSourceFile(String is file){
		self:sourceFile: file;
	}

	Function of Array of String is getErrors(){
		return self:errors;
	}

	## Desugars fancy-family string content ("..." and backtick heredocs):
	## splits literal chunks from {{expr}} holes with escape processing applied
	## inline, sub-parses each hole, and folds everything into the same concat
	## chain a programmer would have written by hand. Hole-free content yields
	## a single string literal (zero runtime cost). At depth >= 1 — inside a
	## template hole — inner strings stay plain: escapes only, no expansion.
	Function of Expression is expandFancyString(String is raw, Token is originTok, Int is depth){
		local Expression is plainE: Expression:init(kind: 'STRING');
		plainE:stringValue: '';
		if (depth > 0) {
			local FancyEscapeLoop is dEsc: FancyEscapeLoop:init(src: raw);
			While:run(loop: dEsc);
			plainE:stringValue: dEsc:res;
			return plainE;
		}
		local TemplateSplitLoop is split: TemplateSplitLoop:init(raw: raw);
		While:run(loop: split);
		split:lits:add(item: split:lit);
		if (split:inHole) {
			self:addError(tok: originTok, message: 'Unterminated template hole (missing closing }})');
			return plainE;
		}
		local Expression is acc: Expression:init(kind: 'STRING');
		acc:stringValue: split:lits:get(index: 0);
		if (split:holes:length() == 0) {
			return acc;
		}
		local TemplateFoldLoop is fold: TemplateFoldLoop:init(parser: self, split: split, originTok: originTok, acc0: acc);
		While:run(loop: fold);
		return fold:acc;
	}

	## Parses one template hole's text as a full Spec expression using a
	## sub-lexer and sub-parser; the hole text must be exactly one expression.
	Function of Expression is parseTemplateExpression(String is text, Token is originTok){
		local Expression is emptyE: Expression:init(kind: 'STRING');
		emptyE:stringValue: '';
		if (text:trim():length() == 0) {
			self:addError(tok: originTok, message: 'Empty expression in string template');
			return emptyE;
		}
		local Lexer is subLexer: Lexer:init(source: text);
		local Array of Token is subTokens: subLexer:tokenize();
		if (subLexer:hasErrors()) {
			self:addError(tok: originTok, message: 'Invalid expression in string template');
			return emptyE;
		}
		local Parser is subParser: Parser:init(tokens: subTokens);
		subParser:setTemplateDepth(depth: 1);
		local Expression is e: subParser:parseExpression();
		if (subParser:hasErrors() || subParser:peek():getKind() != 'EOF') {
			self:addError(tok: originTok, message: 'Invalid expression in string template');
			return emptyE;
		}
		return e;
	}

	## Splits raw fancy-string content at unescaped {{ }} pairs into literal
	## chunks and hole texts. Quote- and brace-aware inside holes so holes may
	## contain string literals and nested braces. Literal escapes are processed
	## inline (every backslash consumes its follower, so a {{ reached in
	## literal state is always a template start; \{\{ renders as literal
	## braces via the escape rule).
	Class of Loop is TemplateSplitLoop{
		local String is raw;
		local Int is pos: 0;
		local Boolean is inHole: false;
		local String is lit: '';
		local Array of String is lits: [];
		local String is hole: '';
		local Array of String is holes: [];
		local String is quoteCh: '';
		local Int is braceDepth: 0;

		replace Function is init(String is raw){
			self:raw: raw;
			self:pos: 0;
			self:inHole: false;
			self:lit: '';
			self:lits: [];
			self:hole: '';
			self:holes: [];
			self:quoteCh: '';
			self:braceDepth: 0;
		}

		replace Function of Boolean is evaluate(){
			return self:pos < self:raw:length();
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:raw:charAt(index: self:pos, default: '');
			if (!self:inHole) {
				if (ch == "{" && self:pos + 1 < self:raw:length() && self:raw:charAt(index: self:pos + 1, default: '') == "{") {
					self:lits:add(item: self:lit);
					self:lit: '';
					self:inHole: true;
					self:hole: '';
					self:quoteCh: '';
					self:braceDepth: 0;
					self:pos: self:pos + 2;
					return true;
				}
				if (ch == "\\") {
					if (self:pos + 1 < self:raw:length()) {
						local String is nextCh: self:raw:charAt(index: self:pos + 1, default: '');
						when (nextCh) {
							is 'n': { self:lit: self:lit . "\n"; }
							is 't': { self:lit: self:lit . "\t"; }
							is 'r': { self:lit: self:lit . "\r"; }
							is 'e': { self:lit: self:lit . String:fromCharCode(code: 27); }
							is '"': { self:lit: self:lit . '"'; }
							is "\\": { self:lit: self:lit . "\\"; }
							is '`': { self:lit: self:lit . '`'; }
							is '{': { self:lit: self:lit . '{'; }
							else: { self:lit: self:lit . nextCh; }
						}
						self:pos: self:pos + 2;
					} else {
						self:lit: self:lit . "\\";
						self:pos: self:pos + 1;
					}
					return true;
				}
				self:lit: self:lit . ch;
				self:pos: self:pos + 1;
				return true;
			}
			if (self:quoteCh != '') {
				if (ch == "\\") {
					self:hole: self:hole . ch;
					self:pos: self:pos + 1;
					if (self:pos < self:raw:length()) {
						self:hole: self:hole . self:raw:charAt(index: self:pos, default: '');
						self:pos: self:pos + 1;
					}
					return true;
				}
				if (ch == self:quoteCh) {
					self:quoteCh: '';
				}
				self:hole: self:hole . ch;
				self:pos: self:pos + 1;
				return true;
			}
			if (ch == '\'' || ch == '"') {
				self:quoteCh: ch;
				self:hole: self:hole . ch;
				self:pos: self:pos + 1;
				return true;
			}
			if (ch == "{") {
				self:braceDepth: self:braceDepth + 1;
				self:hole: self:hole . ch;
				self:pos: self:pos + 1;
				return true;
			}
			if (ch == "}") {
				if (self:braceDepth > 0) {
					self:braceDepth: self:braceDepth - 1;
				} else if (self:pos + 1 < self:raw:length() && self:raw:charAt(index: self:pos + 1, default: '') == "}") {
					self:holes:add(item: self:hole);
					self:hole: '';
					self:inHole: false;
					self:pos: self:pos + 2;
					return true;
				}
				self:hole: self:hole . ch;
				self:pos: self:pos + 1;
				return true;
			}
			self:hole: self:hole . ch;
			self:pos: self:pos + 1;
			return true;
		}
	}

	## Folds holes and their following literal chunks into a left-associated
	## concat chain ('.' binary expressions), matching hand-written code.
	Class of Loop is TemplateFoldLoop{
		local Parser is parser;
		local TemplateSplitLoop is split;
		local Token is originTok;
		local Int is k: 0;
		local Expression is acc;

		replace Function is init(Parser is parser, TemplateSplitLoop is split, Token is originTok, Expression is acc0){
			self:parser: parser;
			self:split: split;
			self:originTok: originTok;
			self:k: 0;
			self:acc: acc0;
		}

		replace Function of Boolean is evaluate(){
			return self:k < self:split:holes:length();
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local Expression is holeE: self:parser:parseTemplateExpression(text: self:split:holes:get(index: self:k), originTok: self:originTok);
			local Expression is withHole: Expression:init(kind: 'BINARY');
			withHole:binaryOp: '.';
			withHole:leftExpr: self:acc;
			withHole:rightExpr: holeE;
			local Expression is litE: Expression:init(kind: 'STRING');
			litE:stringValue: self:split:lits:get(index: self:k + 1);
			local Expression is withLit: Expression:init(kind: 'BINARY');
			withLit:binaryOp: '.';
			withLit:leftExpr: withHole;
			withLit:rightExpr: litE;
			self:acc: withLit;
			self:k: self:k + 1;
			return true;
		}
	}

	## Applies the fancy escape set (n, t, r, e, ", \, `, {; unknown escapes
	## pass the escaped character through) over raw content without expansion.
	Class of Loop is FancyEscapeLoop{
		local String is src;
		local Int is pos: 0;
		local String is res: '';

		replace Function is init(String is src){
			self:src: src;
			self:pos: 0;
			self:res: '';
		}

		replace Function of Boolean is evaluate(){
			return self:pos < self:src:length();
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local String is ch: self:src:charAt(index: self:pos, default: '');
			self:pos: self:pos + 1;
			if (ch == "\\") {
				if (self:pos < self:src:length()) {
					local String is nextCh: self:src:charAt(index: self:pos, default: '');
					self:pos: self:pos + 1;
					when (nextCh) {
						is 'n': { self:res: self:res . "\n"; }
						is 't': { self:res: self:res . "\t"; }
						is 'r': { self:res: self:res . "\r"; }
						is 'e': { self:res: self:res . String:fromCharCode(code: 27); }
						is '"': { self:res: self:res . '"'; }
						is "\\": { self:res: self:res . "\\"; }
						is '`': { self:res: self:res . '`'; }
						is '{': { self:res: self:res . '{'; }
						else: { self:res: self:res . nextCh; }
					}
				} else {
					self:res: self:res . "\\";
				}
				return true;
			}
			self:res: self:res . ch;
			return true;
		}
	}

	Function of Boolean is hasErrors(){
		return self:errors:length() > 0;
	}

	local Function is addError(Token is tok, String is message){
		local String is prefix: if (self:sourceFile != '') self:sourceFile . ':' else 'Line ';
		local String is errStr: '  [SyntaxError] [' . prefix . tok:getLine() . ':' . tok:getCol() . '] ' . message;
		self:errors:add(item: errStr);
	}

	local Function is synchronize(){
		While:condition(
			evaluate: local Function of Boolean(){
				local Token is t: self:peek();
				if (t:getTokenKind() == TokenKind:EOF) {
					return false;
				}
				if (t:getValue() == ';' || t:getValue() == '}') {
					return false;
				}
				return true;
			},
			iteration: local Function of Boolean(){
				self:advance();
				return true;
			}
		);
		if (self:peek():getValue() == ';') {
			self:advance();
		}
	}

	Function of Token is peek(){
		if (self:pos < self:length) {
			return self:tokens:get(index: self:pos);
		}
		return Token:init(kind: TokenKind:EOF, value: '', line: 0, col: 0);
	}

	Function of Token is peekAhead(Int is offset){
		local Int is idx: self:pos + offset;
		if (idx < self:length) {
			return self:tokens:get(index: idx);
		}
		return Token:init(kind: TokenKind:EOF, value: '', line: 0, col: 0);
	}

	Function of Token is advance(){
		local Token is tok: self:peek();
		if (self:pos < self:length) {
			self:pos: self:pos + 1;
		}
		return tok;
	}

	Function of Boolean is hasWhitespaceAfter(Int is offset){
		local Token is cur: self:peekAhead(offset: offset);
		local Token is nxt: self:peekAhead(offset: offset + 1);
		if (nxt:getTokenKind() == TokenKind:EOF) {
			return true;
		}
		return nxt:getLine() > cur:getLine() || nxt:getCol() > (cur:getCol() + cur:getValue():length());
	}

	Function of Boolean is check(String is kind, String is value){
		local Token is tok: self:peek();
		if (kind != '' && tok:getKind() != kind) {
			return false;
		}
		if (value != '' && tok:getValue() != value) {
			return false;
		}
		return true;
	}

	Function of Boolean is matchToken(String is kind, String is value){
		if (self:check(kind: kind, value: value)) {
			self:advance();
			return true;
		}
		local Token is tok: self:peek();
		local String is exp: if (value != '') '\'' . value . '\'' else kind;
		self:addError(tok: tok, message: 'Expected ' . exp . ', found \'' . tok:getValue() . '\'');
		return false;
	}

	Function of Type is parseType(){
		if (self:check(kind: 'SYMBOL', value: '[')) {
			self:advance();
			local Type is elem: self:parseType();
			self:matchToken(kind: 'SYMBOL', value: ']');
			local Type is lnode: Type:init(name: 'List');
			local Array of Type is lparams: [];
			lparams:add(item: elem);
			lnode:params: lparams;
			return lnode;
		}
		local Token is baseTok: self:advance();
		local String is typeName: baseTok:getValue();

		if (self:check(kind: 'KEYWORD', value: 'of')) {
			self:advance();
			local Array of Type is params: [];
			params:add(item: self:parseType());

			if (self:check(kind: 'KEYWORD', value: 'to')) {
				self:advance();
				params:add(item: self:parseType());
			}

			local Type is node: Type:init(name: typeName);
			node:params: params;
			return node;
		}

		return Type:init(name: typeName);
	}

	Function of Member is parseMember(){
		local Int is startLine: self:peek():getLine();
		local Array of String is modifiers: [];
		While:run(loop: ModifierLoop:init(parser: self, mods: modifiers));

		if (self:check(kind: 'IDENTIFIER', value: 'Class')) {
			local ClassInfo is nested: self:parseClass();
			local Member is m: Member:init(kind: 'CLASS');
			m:setLine(line: startLine);
			m:nestedClass: nested;
			return m;
		}

		if (self:check(kind: 'IDENTIFIER', value: 'Enum') || self:check(kind: 'KEYWORD', value: 'Enum')) {
			local ClassInfo is edef: self:parseEnum();
			local Member is m: Member:init(kind: 'CLASS');
			m:setLine(line: startLine);
			m:nestedClass: edef;
			return m;
		}

		if (self:peek():getKind() == 'IDENTIFIER' && self:peekAhead(offset: 1):getValue() == '(') {
			local Token is nameTok: self:advance();
			local String is name: nameTok:getValue();
			self:advance();

			local Array of Parameter is params: [];
			While:run(loop: ParamLoop:init(parser: self, params: params));
			self:matchToken(kind: 'SYMBOL', value: ')');
			self:matchToken(kind: 'SYMBOL', value: '{');

			local Array of Statement is body: [];
			params:each(action: local Function(Parameter is p){
				if (p:getType():getName() == 'SELF_FIELD') {
					local Expression is lhs: Expression:init(kind: 'PATH');
					lhs:makePath(segments: ['self', p:getName()]);
					local Expression is rhs: Expression:init(kind: 'IDENT');
					rhs:makeIdent(name: p:getName());
					local Statement is assignS: Statement:init(kind: 'ASSIGN');
					assignS:assign(target: lhs, value: rhs);
					body:add(item: assignS);
				}
			});
			While:run(loop: BlockStatementsLoop:init(parser: self, stmts: body));
			self:matchToken(kind: 'SYMBOL', value: '}');

			local Member is m: Member:init(kind: 'METHOD');
			m:setLine(line: nameTok:getLine());
			m:modifiers: modifiers;
			m:memberType: Type:init(name: 'void');
			m:name: name;
			m:params: params;
			m:body: body;
			return m;
		}

		local Type is mType: self:parseType();
		self:matchToken(kind: 'KEYWORD', value: 'is');
		local Token is nameTok: self:advance();
		local String is name: nameTok:getValue();

		if (self:check(kind: 'SYMBOL', value: '(')) {
			self:advance();
			local Array of Parameter is params: [];
			While:run(loop: ParamLoop:init(parser: self, params: params));
			self:matchToken(kind: 'SYMBOL', value: ')');
			self:matchToken(kind: 'SYMBOL', value: '{');

			local Array of Statement is body: [];
			params:each(action: local Function(Parameter is p){
				if (p:getType():getName() == 'SELF_FIELD') {
					local Expression is lhs: Expression:init(kind: 'PATH');
					lhs:makePath(segments: ['self', p:getName()]);
					local Expression is rhs: Expression:init(kind: 'IDENT');
					rhs:makeIdent(name: p:getName());
					local Statement is assignS: Statement:init(kind: 'ASSIGN');
					assignS:assign(target: lhs, value: rhs);
					body:add(item: assignS);
				}
			});
			While:run(loop: BlockStatementsLoop:init(parser: self, stmts: body));
			self:matchToken(kind: 'SYMBOL', value: '}');

			local Member is m: Member:init(kind: 'METHOD');
			m:setLine(line: nameTok:getLine());
			m:modifiers: modifiers;
			m:memberType: mType;
			m:name: name;
			m:params: params;
			m:body: body;
			return m;
		}

		# Field
		local Expression is initExpr;
		local Boolean is hasInit: false;
		if (self:check(kind: 'SYMBOL', value: ':')) {
			self:advance();
			initExpr: self:parseExpression();
			hasInit: true;
		}
		self:matchToken(kind: 'SYMBOL', value: ';');

		local Member is m: Member:init(kind: 'FIELD');
		m:setLine(line: nameTok:getLine());
		m:modifiers: modifiers;
		m:memberType: mType;
		m:name: name;
		m:initExpr: initExpr;
		m:hasInit: hasInit;
		return m;
	}

	## Parses a merge-forward statement: `(arg, name: arg, ...)`.
	##
	## An argument beginning with `identifier :` is a named forward argument;
	## all others are positional. Valid only inside `merge` methods (enforced
	## by the TypeChecker).
	##
	## @param startLine: Source line of the opening parenthesis.
	## @return: A "FORWARD" [Statement].
	local Function of Statement is parseForwardStatement(Int is startLine){
		self:advance();
		local Array of NamedArg is args: [];
		While:condition(
			evaluate: local Function of Boolean(){
				return !self:check(kind: 'SYMBOL', value: ')') && !self:check(kind: 'EOF', value: '');
			},
			iteration: local Function of Boolean(){
				local String is argName: '';
				local Token is tok0: self:peekAhead(offset: 0);
				if (tok0:getKind() == 'IDENTIFIER' && self:peekAhead(offset: 1):getValue() == ':') {
					argName: tok0:getValue();
					self:advance();
					self:advance();
				}
				local Expression is val: self:parseExpression();
				args:add(item: NamedArg:init(name: argName, value: val));
				if (self:check(kind: 'SYMBOL', value: ',')) {
					self:advance();
					return true;
				}
				return false;
			}
		);
		self:matchToken(kind: 'SYMBOL', value: ')');
		if (self:check(kind: 'SYMBOL', value: ';')) {
			self:advance();
		}
		local Statement is s: Statement:init(kind: 'FORWARD');
		s:setLine(line: startLine);
		s:forwardArgs: args;
		return s;
	}

	Function of Statement is parseStatement(){
		local Int is startLine: self:peek():getLine();

		# Merge-forward statement: `(arg, name: arg, ...)`.
		if (self:check(kind: 'SYMBOL', value: '(')) {
			return self:parseForwardStatement(startLine: startLine);
		}

		if (self:check(kind: 'IDENTIFIER', value: 'Class')) {
			local ClassInfo is cls: self:parseClass();
			local Statement is s: Statement:init(kind: 'CLASS');
			s:setLine(line: startLine);
			s:nestedClass: cls;
			return s;
		}

		if (self:check(kind: 'IDENTIFIER', value: 'Enum') || self:check(kind: 'KEYWORD', value: 'Enum')) {
			local ClassInfo is edef: self:parseEnum();
			local Statement is s: Statement:init(kind: 'CLASS');
			s:setLine(line: startLine);
			s:nestedClass: edef;
			return s;
		}

		if (self:check(kind: 'KEYWORD', value: 'when')) {
			self:advance();
			self:matchToken(kind: 'SYMBOL', value: '(');
			local Expression is subject: self:parseExpression();
			self:matchToken(kind: 'SYMBOL', value: ')');
			self:matchToken(kind: 'SYMBOL', value: '{');

			local Array of WhenArm is arms: [];
			While:run(loop: WhenArmsLoop:init(parser: self, arms: arms));
			self:matchToken(kind: 'SYMBOL', value: '}');

			local Statement is s: Statement:init(kind: 'WHEN');
			s:setLine(line: startLine);
			s:whenStmt(subject: subject, arms: arms);
			return s;
		}

		if (self:check(kind: 'KEYWORD', value: 'if')) {
			self:advance();
			self:matchToken(kind: 'SYMBOL', value: '(');
			local Expression is cond: self:parseExpression();
			self:matchToken(kind: 'SYMBOL', value: ')');
			self:matchToken(kind: 'SYMBOL', value: '{');

			local Array of Statement is thenBranch: [];
			While:run(loop: BlockStatementsLoop:init(parser: self, stmts: thenBranch));
			self:matchToken(kind: 'SYMBOL', value: '}');

			local Array of Statement is elseBranch: [];
			local Boolean is hasElse: false;
			if (self:check(kind: 'KEYWORD', value: 'else')) {
				self:advance();
				hasElse: true;
				if (self:check(kind: 'KEYWORD', value: 'if')) {
					elseBranch:add(item: self:parseStatement());
				} else {
					self:matchToken(kind: 'SYMBOL', value: '{');
					While:run(loop: BlockStatementsLoop:init(parser: self, stmts: elseBranch));
					self:matchToken(kind: 'SYMBOL', value: '}');
				}
			}

			local Statement is s: Statement:init(kind: 'IF');
			s:setLine(line: startLine);
			s:ifCondition: cond;
			s:thenBranch: thenBranch;
			s:elseBranch: elseBranch;
			s:hasElse: hasElse;
			return s;
		}

		if (self:check(kind: 'KEYWORD', value: 'return')) {
			self:advance();
			local Expression is retExpr;
			local Boolean is hasExpr: false;
			if (!self:check(kind: 'SYMBOL', value: ';')) {
				retExpr: self:parseExpression();
				hasExpr: true;
			}
			self:matchToken(kind: 'SYMBOL', value: ';');

			local Statement is s: Statement:init(kind: 'RETURN');
			s:setLine(line: startLine);
			s:returnExpr: retExpr;
			s:hasReturnExpr: hasExpr;
			return s;
		}

		if (self:check(kind: 'KEYWORD', value: 'local')) {
			self:advance();
			local Array of String is modifiers: ['local'];
			local Type is vType: self:parseType();
			self:matchToken(kind: 'KEYWORD', value: 'is');
			local Token is nameTok: self:advance();
			local String is name: nameTok:getValue();

			local Expression is initExpr;
			local Boolean is hasInit: false;
			if (self:check(kind: 'SYMBOL', value: ':')) {
				self:advance();
				initExpr: self:parseExpression();
				hasInit: true;
			}
			self:matchToken(kind: 'SYMBOL', value: ';');

			local Statement is s: Statement:init(kind: 'VAR_DECL');
			s:setLine(line: startLine);
			s:modifiers: modifiers;
			s:varType: vType;
			s:varName: name;
			s:initExpr: initExpr;
			s:hasInit: hasInit;
			return s;
		}

		# Expression or Assignment
		local Expression is expr: self:parseExpression();

		if (self:check(kind: 'SYMBOL', value: ':') && !self:check(kind: 'SYMBOL', value: ';')) {
			self:advance();
			local Expression is val: self:parseExpression();
			self:matchToken(kind: 'SYMBOL', value: ';');

			local Statement is s: Statement:init(kind: 'ASSIGN');
			s:setLine(line: startLine);
			s:assignTarget: expr;
			s:assignValue: val;
			return s;
		}

		self:matchToken(kind: 'SYMBOL', value: ';');
		local Statement is s: Statement:init(kind: 'EXPR');
		s:setLine(line: startLine);
		s:exprStmt: expr;
		return s;
	}

	local Function of Expression is parsePrimary(){
		local Boolean is isAnonFn: false;
		if (self:check(kind: 'KEYWORD', value: 'local') && self:peekAhead(offset: 1):getValue() == 'Function') {
			isAnonFn: true;
		}
		if (self:peek():getValue() == 'Function' && (self:peekAhead(offset: 1):getValue() == '(' || self:peekAhead(offset: 1):getValue() == 'of')) {
			isAnonFn: true;
		}

		if (isAnonFn) {
			if (self:check(kind: 'KEYWORD', value: 'local')) {
				self:advance();
			}
			self:advance();
			local Type is returnType: Type:init(name: 'Void');
			if (self:check(kind: 'KEYWORD', value: 'of')) {
				self:advance();
				returnType: self:parseType();
			}
			self:matchToken(kind: 'SYMBOL', value: '(');
			local Array of Parameter is params: [];
			While:run(loop: ParamLoop:init(parser: self, params: params));
			self:matchToken(kind: 'SYMBOL', value: ')');
			self:matchToken(kind: 'SYMBOL', value: '{');
			local Array of Statement is body: [];
			params:each(action: local Function(Parameter is p){
				if (p:getType():getName() == 'SELF_FIELD') {
					local Expression is lhs: Expression:init(kind: 'PATH');
					lhs:makePath(segments: ['self', p:getName()]);
					local Expression is rhs: Expression:init(kind: 'IDENT');
					rhs:makeIdent(name: p:getName());
					local Statement is assignS: Statement:init(kind: 'ASSIGN');
					assignS:assign(target: lhs, value: rhs);
					body:add(item: assignS);
				}
			});
			While:run(loop: BlockStatementsLoop:init(parser: self, stmts: body));
			self:matchToken(kind: 'SYMBOL', value: '}');

			local Expression is e: Expression:init(kind: 'ANON_FN');
			e:anonReturnType: returnType;
			e:anonParams: params;
			e:anonBody: body;
			return e;
		}

		if (self:check(kind: 'KEYWORD', value: 'when')) {
			self:advance();
			self:matchToken(kind: 'SYMBOL', value: '(');
			local Expression is subject: self:parseExpression();
			self:matchToken(kind: 'SYMBOL', value: ')');
			self:matchToken(kind: 'SYMBOL', value: '{');

			local Array of WhenArm is arms: [];
			While:run(loop: WhenArmsLoop:init(parser: self, arms: arms));
			self:matchToken(kind: 'SYMBOL', value: '}');

			local Expression is e: Expression:init(kind: 'WHEN');
			e:makeWhen(subject: subject, arms: arms);
			return e;
		}

		if (self:check(kind: 'KEYWORD', value: 'if')) {
			self:advance();
			self:matchToken(kind: 'SYMBOL', value: '(');
			local Expression is cond: self:parseExpression();
			self:matchToken(kind: 'SYMBOL', value: ')');
			local Expression is thenExpr: self:parseExpression();
			self:matchToken(kind: 'KEYWORD', value: 'else');
			local Expression is elseExpr: self:parseExpression();
			local Expression is e: Expression:init(kind: 'IF_ELSE');
			e:condExpr: cond;
			e:thenExpr: thenExpr;
			e:elseExpr: elseExpr;
			return e;
		}

		local Token is tok: self:peek();

		when (tok:getTokenKind()) {
			is STRING: {
				self:advance();
				local Expression is e: Expression:init(kind: 'STRING');
				e:stringValue: tok:getValue();
				return e;
			}
			is RAWSTRING: {
				self:advance();
				local Expression is e: Expression:init(kind: 'STRING');
				e:stringValue: tok:getValue();
				return e;
			}
			is FANCYSTRING: {
				self:advance();
				return self:expandFancyString(raw: tok:getValue(), originTok: tok, depth: self:templateDepth);
			}
			is INT: {
				self:advance();
				local Expression is e: Expression:init(kind: 'NUMBER');
				e:stringValue: tok:getValue();
				return e;
			}
			is FLOAT: {
				self:advance();
				local Expression is e: Expression:init(kind: 'FLOAT');
				e:stringValue: tok:getValue();
				return e;
			}
			is BOOL: {
				self:advance();
				local Expression is e: Expression:init(kind: 'BOOL');
				e:boolValue: tok:getValue() == 'true';
				e:stringValue: tok:getValue();
				return e;
			}
			is IDENTIFIER, KEYWORD: {
				self:advance();
				local Expression is e: Expression:init(kind: 'IDENT');
				e:stringValue: tok:getValue();
				return e;
			}
			else: {
				if (self:check(kind: 'SYMBOL', value: '(')) {
					self:advance();
					local Expression is inner: self:parseExpression();
					self:matchToken(kind: 'SYMBOL', value: ')');
					return inner;
				}

				if (self:check(kind: 'SYMBOL', value: '[')) {
					self:advance();
					if (self:check(kind: 'SYMBOL', value: ']')) {
						self:advance();
						local Expression is e: Expression:init(kind: 'ARRAY');
						e:arrayItems: [];
						return e;
					}
					if (self:check(kind: 'SYMBOL', value: ':')) {
						self:advance();
						self:matchToken(kind: 'SYMBOL', value: ']');
						local Expression is e: Expression:init(kind: 'MAP');
						e:makeMap(keys: [], values: []);
						return e;
					}
					local Expression is firstItem: self:parseExpression();
					if (self:check(kind: 'SYMBOL', value: ':')) {
						self:advance();
						local Expression is firstVal: self:parseExpression();
						local Array of Expression is mKeys: [firstItem];
						local Array of Expression is mVals: [firstVal];
						if (self:check(kind: 'SYMBOL', value: ',')) {
							self:advance();
							While:run(loop: MapItemsLoop:init(parser: self, keys: mKeys, values: mVals));
						}
						self:matchToken(kind: 'SYMBOL', value: ']');
						local Expression is e: Expression:init(kind: 'MAP');
						e:makeMap(keys: mKeys, values: mVals);
						return e;
					}
					local Array of Expression is items: [firstItem];
					if (self:check(kind: 'SYMBOL', value: ',')) {
						self:advance();
						While:run(loop: ArrayItemsLoop:init(parser: self, items: items));
					}
					self:matchToken(kind: 'SYMBOL', value: ']');
					local Expression is e: Expression:init(kind: 'ARRAY');
					e:arrayItems: items;
					return e;
				}

				self:addError(tok: tok, message: 'Unexpected token \'' . tok:getValue() . '\' in expression');
				self:advance();
				return Expression:init(kind: 'UNKNOWN');
			}
		}
	}

	local Function of Expression is parsePostfix(){
		local Expression is expr: self:parsePrimary();
		local PostfixLoop is postLoop: PostfixLoop:init(parser: self, expr: expr);
		While:run(loop: postLoop);
		return postLoop:currentExpr;
	}

	## Parses a type cast: `value as Target` or `value as Target(width)`.
	##
	## Targets: class names, Int, Float, String, and the base pseudo-types
	## Hex, Bin, Oct. Binding is tighter than every binary operator; chaining
	## (`x as A as B`) is rejected.
	local Function of Expression is parseAs(){
		local Expression is left: self:parsePostfix();
		if (self:check(kind: 'KEYWORD', value: 'as')) {
			self:advance();
			local Token is targetTok: self:advance();
			local Array of Expression is args: [];
			if (self:check(kind: 'SYMBOL', value: '(')) {
				self:advance();
				if (!self:check(kind: 'SYMBOL', value: ')')) {
					args:add(item: self:parseExpression());
				}
				self:matchToken(kind: 'SYMBOL', value: ')');
			}
			if (self:check(kind: 'KEYWORD', value: 'as')) {
				self:addError(tok: self:peek(), message: 'Chained \'as\' casts are not supported; cast in separate steps.');
			}
			local Expression is c: Expression:init(kind: 'CAST');
			c:makeCast(inner: left, target: targetTok:getValue(), args: args);
			return c;
		}
		return left;
	}

	Function of Expression is parseUnary(){
		if (self:check(kind: 'SYMBOL', value: '~')) {
			self:advance();
			local Expression is expr: self:parseUnary();
			local Expression is u: Expression:init(kind: 'UNARY');
			u:unaryOp: '~';
			u:unaryExpr: expr;
			return u;
		}
		if (self:check(kind: 'SYMBOL', value: '-')) {
			self:advance();
			local Expression is expr: self:parseUnary();
			local Expression is u: Expression:init(kind: 'UNARY');
			u:unaryOp: '-';
			u:unaryExpr: expr;
			return u;
		}
		if (self:check(kind: 'SYMBOL', value: '!')) {
			self:advance();
			local Expression is expr: self:parseUnary();
			local Expression is u: Expression:init(kind: 'UNARY');
			u:unaryOp: '!';
			u:unaryExpr: expr;
			return u;
		}
		return self:parseAs();
	}

	Function of Expression is parseMultiplicative(){
		local Expression is left: self:parseUnary();
		local MultiplicativeLoop is loopInst: MultiplicativeLoop:init(parser: self, expr: left);
		While:run(loop: loopInst);
		return loopInst:currentExpr;
	}

	Function of Expression is parseAdditive(){
		local Expression is left: self:parseMultiplicative();
		local AdditiveLoop is loopInst: AdditiveLoop:init(parser: self, expr: left);
		While:run(loop: loopInst);
		return loopInst:currentExpr;
	}

	## Parses shift expressions (`<<`, `>>`), binding looser than addition
	## and tighter than concatenation (C precedence: `1 << 2 + 1` is 8).
	local Function of Expression is parseShift(){
		local Expression is left: self:parseAdditive();
		local ShiftLoop is loopInst: ShiftLoop:init(parser: self, expr: left);
		While:run(loop: loopInst);
		return loopInst:currentExpr;
	}

	Function of Expression is parseConcat(){
		local Expression is left: self:parseShift();
		local ConcatLoop is loopInst: ConcatLoop:init(parser: self, expr: left);
		While:run(loop: loopInst);
		return loopInst:currentExpr;
	}

	Function of Expression is parseRelational(){
		local Expression is left: self:parseConcat();
		local RelationalLoop is loopInst: RelationalLoop:init(parser: self, expr: left);
		While:run(loop: loopInst);
		return loopInst:currentExpr;
	}

	Function of Expression is parseEquality(){
		local Expression is left: self:parseRelational();
		local EqualityLoop is loopInst: EqualityLoop:init(parser: self, expr: left);
		While:run(loop: loopInst);
		return loopInst:currentExpr;
	}

	Function of Expression is parseLogicalAnd(){
		local Expression is left: self:parseBitOr();
		local LogicalAndLoop is loopInst: LogicalAndLoop:init(parser: self, expr: left);
		While:run(loop: loopInst);
		return loopInst:currentExpr;
	}

	## Parses bitwise OR (`|`), between `&&` and `^` (C precedence).
	local Function of Expression is parseBitOr(){
		local Expression is left: self:parseBitXor();
		local BitOrLoop is loopInst: BitOrLoop:init(parser: self, expr: left);
		While:run(loop: loopInst);
		return loopInst:currentExpr;
	}

	## Parses bitwise XOR (`^`), between `|` and `&`.
	Function of Expression is parseBitXor(){
		local Expression is left: self:parseBitAnd();
		local BitXorLoop is loopInst: BitXorLoop:init(parser: self, expr: left);
		While:run(loop: loopInst);
		return loopInst:currentExpr;
	}

	## Parses bitwise AND (`&`), between `^` and equality comparisons.
	Function of Expression is parseBitAnd(){
		local Expression is left: self:parseEquality();
		local BitAndLoop is loopInst: BitAndLoop:init(parser: self, expr: left);
		While:run(loop: loopInst);
		return loopInst:currentExpr;
	}

	local Function of Expression is parseLogicalOr(){
		local Expression is left: self:parseLogicalAnd();
		local LogicalOrLoop is loopInst: LogicalOrLoop:init(parser: self, expr: left);
		While:run(loop: loopInst);
		return loopInst:currentExpr;
	}

	Function of Expression is parseExpression(){
		return self:parseLogicalOr();
	}

	Function of ClassInfo is parseClass(){
		# Canonical declaration: `Class of Parent is Name` (inheritance, mirroring
		# `Enum of Int is Status`); generic parameters post-name (`Class is Box of T`).
		if (self:check(kind: 'IDENTIFIER', value: 'class')) {
			self:addError(tok: self:peek(), message: 'The \'class\' keyword is no longer valid; declare classes as \'Class of Parent is Name\'.');
		}
		self:advance();

		# Pre-binder `of`: parent classes.
		local Array of String is baseClasses: [];
		if (self:check(kind: 'KEYWORD', value: 'of')) {
			self:advance();
			While:run(loop: BaseClassesLoop:init(parser: self, bases: baseClasses));
		}

		self:matchToken(kind: 'KEYWORD', value: 'is');
		local Token is nameTok: self:advance();
		local String is name: nameTok:getValue();

		# Post-name `of`: generic type parameters.
		local Array of String is typeParams: [];
		if (self:check(kind: 'KEYWORD', value: 'of')) {
			self:advance();
			local Token is tp1: self:advance();
			typeParams:add(item: tp1:getValue());
			if (self:check(kind: 'KEYWORD', value: 'to')) {
				self:advance();
				local Token is tp2: self:advance();
				typeParams:add(item: tp2:getValue());
			}
		}

		self:matchToken(kind: 'SYMBOL', value: '{');
		local Array of Member is members: [];
		While:run(loop: ClassMembersLoop:init(parser: self, members: members));
		self:matchToken(kind: 'SYMBOL', value: '}');

		local ClassInfo is c: ClassInfo:init(name: name, baseClass: '', members: members);
		c:setLine(line: nameTok:getLine());
		c:setSourceFile(file: self:sourceFile);
		c:setTypeParams(params: typeParams);
		c:withBaseClasses(name: name, baseClasses: baseClasses, members: members);
		return c;
	}

	Function of ClassInfo is parseEnum(){
		self:advance();
		local String is backingType: 'Int';
		if (self:check(kind: 'KEYWORD', value: 'of')) {
			self:advance();
			local Type is bt: self:parseType();
			backingType: bt:getName();
		}
		self:matchToken(kind: 'KEYWORD', value: 'is');
		local Token is nameTok: self:advance();
		local String is name: nameTok:getValue();
		self:matchToken(kind: 'SYMBOL', value: '{');

		local Array of Member is members: [];
		While:run(loop: EnumVariantsLoop:init(parser: self, members: members, backingType: backingType));
		self:matchToken(kind: 'SYMBOL', value: '}');
		if (self:check(kind: 'SYMBOL', value: ';')) {
			self:advance();
		}

		local ClassInfo is c: ClassInfo:init(name: name, baseClass: 'Enum', members: members);
		c:setLine(line: nameTok:getLine());
		c:setSourceFile(file: self:sourceFile);
		c:withBaseClasses(name: name, baseClasses: ['Enum'], members: members);
		return c;
	}

	## Parses the token stream into a root [base:meta:ProgramNode] AST.
	##
	## @return: Root [ProgramNode] containing all parsed class definitions.
	Function of ProgramNode is parseProgram(){
		local Array of ClassInfo is classes: [];
		While:run(loop: ProgramParseLoop:init(parser: self, classes: classes));
		return ProgramNode:init(classes: classes);
	}

}
