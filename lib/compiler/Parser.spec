class Parser{

	replace local Array of String is using: [
		base:struct:Array,
		base:iterator:*,
		compiler:Token,
		base:reflect:*,
		base:meta:*
	];

	local Array of Token is tokens: [];
	local Int is pos: 0;
	local Int is length: 0;

	# Internal Loop Classes
	class ProgramParseLoop extends Loop{
		local Parser is parser;
		local Array of Class is classes;

		replace local Function is init(Parser is parser, Array of Class is classes){
			self:parser: parser;
			self:classes: classes;
		}

		replace local Function of Boolean is evaluate(){
			return !parser:check(kind: "EOF", value: "");
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			classes:add(item: parser:parseClass());
			return true;
		}
	}

	class ClassMembersLoop extends Loop{
		local Parser is parser;
		local Array of Member is members;

		replace local Function is init(Parser is parser, Array of Member is members){
			self:parser: parser;
			self:members: members;
		}

		replace local Function of Boolean is evaluate(){
			return !parser:check(kind: "SYMBOL", value: "}") && !parser:check(kind: "EOF", value: "");
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			members:add(item: parser:parseMember());
			return true;
		}
	}

	class BlockStatementsLoop extends Loop{
		local Parser is parser;
		local Array of Statement is stmts;

		replace local Function is init(Parser is parser, Array of Statement is stmts){
			self:parser: parser;
			self:stmts: stmts;
		}

		replace local Function of Boolean is evaluate(){
			return !parser:check(kind: "SYMBOL", value: "}") && !parser:check(kind: "EOF", value: "");
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			stmts:add(item: parser:parseStatement());
			return true;
		}
	}

	class ArrayItemsLoop extends Loop{
		local Parser is parser;
		local Array of Expression is items;

		replace local Function is init(Parser is parser, Array of Expression is items){
			self:parser: parser;
			self:items: items;
		}

		replace local Function of Boolean is evaluate(){
			return !parser:check(kind: "SYMBOL", value: "]") && !parser:check(kind: "EOF", value: "");
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			items:add(item: parser:parseExpression());
			if (parser:check(kind: "SYMBOL", value: ",")) {
				parser:advance();
				return true;
			}
			return false;
		}
	}

	class ModifierLoop extends Loop{
		local Parser is parser;
		local Array of String is mods;

		replace local Function is init(Parser is parser, Array of String is mods){
			self:parser: parser;
			self:mods: mods;
		}

		replace local Function of Boolean is evaluate(){
			return parser:check(kind: "KEYWORD", value: "local") || parser:check(kind: "KEYWORD", value: "replace");
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local Token is tok: parser:advance();
			mods:add(item: tok:getValue());
			return true;
		}
	}

	class ParamLoop extends Loop{
		local Parser is parser;
		local Array of Parameter is params;

		replace local Function is init(Parser is parser, Array of Parameter is params){
			self:parser: parser;
			self:params: params;
		}

		replace local Function of Boolean is evaluate(){
			return !parser:check(kind: "SYMBOL", value: ")") && !parser:check(kind: "EOF", value: "");
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local Type is pType: parser:parseType();
			parser:matchToken(kind: "KEYWORD", value: "is");
			local Token is pTok: parser:advance();
			params:add(item: Parameter:init(name: pTok:getValue(), paramType: pType));
			if (parser:check(kind: "SYMBOL", value: ",")) {
				parser:advance();
				return true;
			}
			return false;
		}
	}

	class ArgLoop extends Loop{
		local Parser is parser;
		local Array of NamedArg is args;

		replace local Function is init(Parser is parser, Array of NamedArg is args){
			self:parser: parser;
			self:args: args;
		}

		replace local Function of Boolean is evaluate(){
			return !parser:check(kind: "SYMBOL", value: ")") && !parser:check(kind: "EOF", value: "");
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local String is argName: "";
			if (parser:peekAhead(offset: 1):getValue() == ":") {
				local Token is aTok: parser:advance();
				argName: aTok:getValue();
				parser:advance();
			}
			local Expression is val: parser:parseExpression();
			args:add(item: NamedArg:init(name: argName, value: val));
			if (parser:check(kind: "SYMBOL", value: ",")) {
				parser:advance();
				return true;
			}
			return false;
		}
	}

	class PostfixLoop extends Loop{
		local Parser is parser;
		local Expression is currentExpr;

		replace local Function is init(Parser is parser, Expression is expr){
			self:parser: parser;
			self:currentExpr: expr;
		}

		replace local Function of Boolean is evaluate(){
			return parser:check(kind: "SYMBOL", value: ":") || parser:check(kind: "SYMBOL", value: "(");
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			if (parser:check(kind: "SYMBOL", value: ":")) {
				parser:advance();
				local Token is mTok: parser:advance();
				local String is method: mTok:getValue();

				if (parser:check(kind: "SYMBOL", value: "(")) {
					parser:advance();
					local Array of NamedArg is args: [];
					While:run(loop: ArgLoop:init(parser: parser, args: args));
					parser:matchToken(kind: "SYMBOL", value: ")");

					local Expression is callExpr: Expression:init(kind: "CALL");
					callExpr:methodTarget: currentExpr;
					callExpr:methodName: method;
					callExpr:methodArgs: args;
					self:currentExpr: callExpr;
					return true;
				}

				local Expression is pathExpr: Expression:init(kind: "PATH");
				pathExpr:stringValue: currentExpr:stringValue . ":" . method;
				self:currentExpr: pathExpr;
				return true;
			}
			return false;
		}
	}

	class BinaryLoop extends Loop{
		local Parser is parser;
		local Expression is currentExpr;

		replace local Function is init(Parser is parser, Expression is expr){
			self:parser: parser;
			self:currentExpr: expr;
		}

		replace local Function of Boolean is evaluate(){
			local Token is tok: parser:peek();
			local String is val: tok:getValue();
			return val == "+" || val == "-" || val == "*" || val == "/" || val == "." || val == "==" || val == "!=" || val == "<" || val == ">" || val == "<=" || val == ">=" || val == "&&" || val == "||";
		}

		replace local Function of Boolean is iteration(LoopControl is control){
			local Token is opTok: parser:advance();
			local String is op: opTok:getValue();
			local Expression is right: parser:parsePostfix();

			local Expression is binExpr: Expression:init(kind: "BINARY");
			binExpr:binaryOp: op;
			binExpr:leftExpr: currentExpr;
			binExpr:rightExpr: right;
			self:currentExpr: binExpr;
			return true;
		}
	}

	replace local Function is init(Array of Token is tokens){
		self:tokens: tokens;
		self:length: tokens:length();
		self:pos: 0;
	}

	replace local Function of Token is peek(){
		if (self:pos < self:length) {
			return self:tokens:get(index: self:pos);
		}
		return Token:init(kind: "EOF", value: "", line: 0, col: 0);
	}

	replace local Function of Token is peekAhead(Int is offset){
		local Int is idx: self:pos + offset;
		if (idx < self:length) {
			return self:tokens:get(index: idx);
		}
		return Token:init(kind: "EOF", value: "", line: 0, col: 0);
	}

	replace local Function of Token is advance(){
		local Token is tok: self:peek();
		if (self:pos < self:length) {
			self:pos: self:pos + 1;
		}
		return tok;
	}

	replace local Function of Boolean is check(String is kind, String is value){
		local Token is tok: self:peek();
		if (kind != "" && tok:getKind() != kind) {
			return false;
		}
		if (value != "" && tok:getValue() != value) {
			return false;
		}
		return true;
	}

	replace local Function of Boolean is matchToken(String is kind, String is value){
		if (self:check(kind: kind, value: value)) {
			self:advance();
			return true;
		}
		return false;
	}

	replace local Function of Type is parseType(){
		local Token is baseTok: self:advance();
		local String is typeName: baseTok:getValue();

		if (self:check(kind: "KEYWORD", value: "of")) {
			self:advance();
			local Array of Type is params: [];
			params:add(item: self:parseType());

			if (self:check(kind: "KEYWORD", value: "to")) {
				self:advance();
				params:add(item: self:parseType());
			}

			local Type is node: Type:init(name: typeName);
			node:params: params;
			return node;
		}

		return Type:init(name: typeName);
	}

	replace local Function of Member is parseMember(){
		local Array of String is modifiers: [];
		While:run(loop: ModifierLoop:init(parser: self, mods: modifiers));

		if (self:check(kind: "KEYWORD", value: "class")) {
			local Class is nested: self:parseClass();
			local Member is m: Member:init(kind: "CLASS");
			m:nestedClass: nested;
			return m;
		}

		local Type is mType: self:parseType();
		self:matchToken(kind: "KEYWORD", value: "is");
		local Token is nameTok: self:advance();
		local String is name: nameTok:getValue();

		if (self:check(kind: "SYMBOL", value: "(")) {
			self:advance();
			local Array of Parameter is params: [];
			While:run(loop: ParamLoop:init(parser: self, params: params));
			self:matchToken(kind: "SYMBOL", value: ")");
			self:matchToken(kind: "SYMBOL", value: "{");

			local Array of Statement is body: [];
			While:run(loop: BlockStatementsLoop:init(parser: self, stmts: body));
			self:matchToken(kind: "SYMBOL", value: "}");

			local Member is m: Member:init(kind: "METHOD");
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
		if (self:check(kind: "SYMBOL", value: ":")) {
			self:advance();
			initExpr: self:parseExpression();
			hasInit: true;
		}
		self:matchToken(kind: "SYMBOL", value: ";");

		local Member is m: Member:init(kind: "FIELD");
		m:modifiers: modifiers;
		m:memberType: mType;
		m:name: name;
		m:initExpr: initExpr;
		m:hasInit: hasInit;
		return m;
	}

	replace local Function of Statement is parseStatement(){
		if (self:check(kind: "KEYWORD", value: "if")) {
			self:advance();
			self:matchToken(kind: "SYMBOL", value: "(");
			local Expression is cond: self:parseExpression();
			self:matchToken(kind: "SYMBOL", value: ")");
			self:matchToken(kind: "SYMBOL", value: "{");

			local Array of Statement is thenBranch: [];
			While:run(loop: BlockStatementsLoop:init(parser: self, stmts: thenBranch));
			self:matchToken(kind: "SYMBOL", value: "}");

			local Array of Statement is elseBranch: [];
			local Boolean is hasElse: false;
			if (self:check(kind: "KEYWORD", value: "else")) {
				self:advance();
				hasElse: true;
				if (self:check(kind: "KEYWORD", value: "if")) {
					elseBranch:add(item: self:parseStatement());
				} else {
					self:matchToken(kind: "SYMBOL", value: "{");
					While:run(loop: BlockStatementsLoop:init(parser: self, stmts: elseBranch));
					self:matchToken(kind: "SYMBOL", value: "}");
				}
			}

			local Statement is s: Statement:init(kind: "IF");
			s:ifCondition: cond;
			s:thenBranch: thenBranch;
			s:elseBranch: elseBranch;
			s:hasElse: hasElse;
			return s;
		}

		if (self:check(kind: "KEYWORD", value: "return")) {
			self:advance();
			local Expression is retExpr;
			local Boolean is hasExpr: false;
			if (!self:check(kind: "SYMBOL", value: ";")) {
				retExpr: self:parseExpression();
				hasExpr: true;
			}
			self:matchToken(kind: "SYMBOL", value: ";");

			local Statement is s: Statement:init(kind: "RETURN");
			s:returnExpr: retExpr;
			s:hasReturnExpr: hasExpr;
			return s;
		}

		if (self:check(kind: "KEYWORD", value: "local")) {
			self:advance();
			local Array of String is modifiers: ["local"];
			local Type is vType: self:parseType();
			self:matchToken(kind: "KEYWORD", value: "is");
			local Token is nameTok: self:advance();
			local String is name: nameTok:getValue();

			local Expression is initExpr;
			local Boolean is hasInit: false;
			if (self:check(kind: "SYMBOL", value: ":")) {
				self:advance();
				initExpr: self:parseExpression();
				hasInit: true;
			}
			self:matchToken(kind: "SYMBOL", value: ";");

			local Statement is s: Statement:init(kind: "VAR_DECL");
			s:modifiers: modifiers;
			s:varType: vType;
			s:varName: name;
			s:initExpr: initExpr;
			s:hasInit: hasInit;
			return s;
		}

		# Expression or Assignment
		local Expression is expr: self:parseExpression();

		if (self:check(kind: "SYMBOL", value: ":") && !self:check(kind: "SYMBOL", value: ";")) {
			self:advance();
			local Expression is val: self:parseExpression();
			self:matchToken(kind: "SYMBOL", value: ";");

			local Statement is s: Statement:init(kind: "ASSIGN");
			s:assignTarget: expr;
			s:assignValue: val;
			return s;
		}

		self:matchToken(kind: "SYMBOL", value: ";");
		local Statement is s: Statement:init(kind: "EXPR");
		s:exprStmt: expr;
		return s;
	}

	replace local Function of Expression is parsePrimary(){
		local Token is tok: self:peek();

		if (tok:getKind() == "STRING") {
			self:advance();
			local Expression is e: Expression:init(kind: "STRING");
			e:stringValue: tok:getValue();
			return e;
		}

		if (tok:getKind() == "INT") {
			self:advance();
			local Expression is e: Expression:init(kind: "NUMBER");
			e:stringValue: tok:getValue();
			return e;
		}

		if (tok:getKind() == "FLOAT") {
			self:advance();
			local Expression is e: Expression:init(kind: "FLOAT");
			e:stringValue: tok:getValue();
			return e;
		}

		if (tok:getKind() == "BOOL") {
			self:advance();
			local Expression is e: Expression:init(kind: "BOOL");
			e:boolValue: tok:getValue() == "true";
			e:stringValue: tok:getValue();
			return e;
		}

		if (tok:getKind() == "IDENTIFIER" || tok:getKind() == "KEYWORD") {
			self:advance();
			local Expression is e: Expression:init(kind: "IDENT");
			e:stringValue: tok:getValue();
			return e;
		}

		if (self:check(kind: "SYMBOL", value: "(")) {
			self:advance();
			local Expression is inner: self:parseExpression();
			self:matchToken(kind: "SYMBOL", value: ")");
			return inner;
		}

		if (self:check(kind: "SYMBOL", value: "[")) {
			self:advance();
			local Array of Expression is items: [];
			While:run(loop: ArrayItemsLoop:init(parser: self, items: items));
			self:matchToken(kind: "SYMBOL", value: "]");
			local Expression is e: Expression:init(kind: "ARRAY");
			e:arrayItems: items;
			return e;
		}

		self:advance();
		return Expression:init(kind: "UNKNOWN");
	}

	replace local Function of Expression is parsePostfix(){
		local Expression is expr: self:parsePrimary();
		local PostfixLoop is postLoop: PostfixLoop:init(parser: self, expr: expr);
		While:run(loop: postLoop);
		return postLoop:currentExpr;
	}

	replace local Function of Expression is parseExpression(){
		local Expression is left: self:parsePostfix();
		local BinaryLoop is binLoop: BinaryLoop:init(parser: self, expr: left);
		While:run(loop: binLoop);
		return binLoop:currentExpr;
	}

	replace local Function of Class is parseClass(){
		self:matchToken(kind: "KEYWORD", value: "class");
		local Token is nameTok: self:advance();
		local String is name: nameTok:getValue();

		local String is baseClass: "";
		if (self:check(kind: "KEYWORD", value: "extends")) {
			self:advance();
			local Token is baseTok: self:advance();
			baseClass: baseTok:getValue();
		}

		self:matchToken(kind: "SYMBOL", value: "{");
		local Array of Member is members: [];
		While:run(loop: ClassMembersLoop:init(parser: self, members: members));
		self:matchToken(kind: "SYMBOL", value: "}");

		return Class:init(name: name, baseClass: baseClass, members: members);
	}

	replace local Function of ProgramNode is parseProgram(){
		local Array of Class is classes: [];
		While:run(loop: ProgramParseLoop:init(parser: self, classes: classes));
		return ProgramNode:init(classes: classes);
	}

}
