#! Package base:compiler:parser
#! Turns the token stream into the AST.
##
## The parser is a recursive-descent engine: a token cursor, a precedence
## chain for expressions ([PrecedenceLevel] + [BinaryFoldLoop]), and
## dedicated productions for statements, members, classes, and enums.
## Template strings desugar into ordinary concat chains at parse time, so
## the checker and generator never see template nodes.
##
## Parse errors are [Error] values carrying provenance (file plus the
## offending token's coordinates); the parser keeps going where it can to
## report more than one problem per run.

Class is Parser{
	namespace: ['base', 'compiler', 'parser'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'lexer', Token],
		['base', 'compiler', 'lexer', TokenKind],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'compiler', 'lexer', Punctuation],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'ast', Type],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', StatementKind],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ast', WhenArm],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', Error],
		['base', 'sys', as Reflection()],
		['base', 'compiler', WellKnown],
		['base', 'compiler', 'parser', PrecedenceLevel],
		['base', 'compiler', 'parser', 'loops', BinaryFoldLoop],
		['base', 'compiler', 'parser', 'loops', PostfixLoop],
		['base', 'compiler', 'parser', 'loops', ArgLoop],
		['base', 'compiler', 'parser', 'loops', ParamLoop],
		['base', 'compiler', 'parser', 'loops', WhenConditionsLoop],
		['base', 'compiler', 'parser', 'loops', WhenArmsLoop],
		['base', 'compiler', 'parser', 'loops', ArrayItemsLoop],
		['base', 'compiler', 'parser', 'loops', MapItemsLoop],
		['base', 'compiler', 'parser', 'loops', BlockStatementsLoop],
		['base', 'compiler', 'parser', 'loops', ModifierLoop],
		['base', 'compiler', 'parser', 'loops', BaseClassesLoop],
		['base', 'compiler', 'parser', 'loops', ClassMembersLoop],
		['base', 'compiler', 'parser', 'loops', EnumVariantsLoop],
		['base', 'compiler', 'parser', 'loops', ProgramParseLoop],
		['base', 'compiler', 'parser', 'loops', TemplateSplitLoop],
		['base', 'compiler', 'parser', 'loops', TemplateFoldLoop],
		['base', 'compiler', 'parser', 'loops', FancyEscapeLoop],
		['base', 'iterator'],
		['base', 'iterator', as While()],
		['base', 'sys', as Conditional()]
	];

	local Array of Token is tokens: [];
	local Int is pos: 0;
	local Int is length: 0;
	local String is sourceFile: '';
	local Array of Error is errors: [];

	# Nesting depth of template desugaring: 0 at statement level, >= 1
	# inside a template hole (inner strings stay plain — no nested
	# template expansion).
	local Int is templateDepth: 0;

	## Well-known names (builtin types, sentinels).
	local WellKnown is names: WellKnown:init();

	## Initializes a parser over a token stream.
	##
	## @param tokens: Tokens from [Lexer].
	replace Function is init(Array of Token is tokens){
		self:tokens: tokens;
		self:length: tokens:length();
		self:pos: 0;
		self:sourceFile: '';
		self:errors: [];
		self:templateDepth: 0;
	}

	## Attaches the declaring file for provenance.
	##
	## @param file: Source file path.
	Function is setSourceFile(String is file){
		self:sourceFile: file;
	}

	## Sets the template nesting depth (sub-parsers inside holes run at 1).
	##
	## @param depth: The depth to run at.
	Function is setTemplateDepth(Int is depth){
		self:templateDepth: depth;
	}

	## Returns whether any parse errors were recorded.
	##
	## @return: true when [errors] is non-empty.
	Function of Boolean is hasErrors(){
		return self:errors:length() > 0;
	}

	## Returns all recorded parse errors.
	##
	## @return: [Error] values, in discovery order.
	Function of Array of Error is getErrors(){
		return self:errors;
	}

	## Records a parse error at the given token's coordinates.
	##
	## @param tok: The offending token.
	## @param message: What went wrong.
	Function is addError(Token is tok, String is message){
		local String is prefix: Conditional:branch(check: { self:sourceFile != '' }, then: { self:sourceFile . ':' }, otherwise: { 'Line ' });
		local Error is e: Error:init(message: "  [SyntaxError] [{{prefix}}{{tok:getLine()}}:{{tok:getCol()}}] {{message}}");
		e:addTraceAt(className: Reflection:class(), methodName: Reflection:method(), line: tok:getLine(), col: tok:getCol());
		self:errors:add(item: e);
	}

	## Returns the current token without consuming it.
	##
	## @return: The current token; EOF past the end.
	Function of Token is peek(){
		Conditional:branch(check: { self:pos < self:length }, then: {
			return self:tokens:get(index: self:pos);
		});
		return Token:init(kind: TokenKind:EOF, value: '', line: 0, col: 0);
	}

	## Returns the token [offset] positions ahead.
	##
	## @param offset: Lookahead distance.
	## @return: The token; EOF past the end.
	Function of Token is peekAhead(Int is offset){
		local Int is idx: self:pos + offset;
		Conditional:branch(check: { idx < self:length }, then: {
			return self:tokens:get(index: idx);
		});
		return Token:init(kind: TokenKind:EOF, value: '', line: 0, col: 0);
	}

	## Consumes and returns the current token.
	##
	## @return: The consumed token.
	Function of Token is advance(){
		local Token is tok: self:peek();
		Conditional:branch(check: { self:pos < self:length }, then: {
			self:pos: self:pos + 1;
		});
		return tok;
	}

	## True when the token [offset] ahead starts on a new line or column
	## position that implies whitespace separation.
	##
	## @param offset: Lookahead distance.
	## @return: true when whitespace separates the tokens.
	Function of Boolean is hasWhitespaceAfter(Int is offset){
		local Token is cur: self:peekAhead(offset: offset);
		local Token is nxt: self:peekAhead(offset: offset + 1);
		Conditional:branch(check: { nxt:getTokenKind() == TokenKind:EOF }, then: {
			return true;
		});
		return nxt:getLine() > cur:getLine() || nxt:getCol() > (cur:getCol() + cur:getValue():length());
	}

	## Two-sided token test: the current token matches the given kind and,
	## when non-empty, the given value.
	##
	## @param kind: Expected token kind.
	## @param value: Expected lexeme ('' matches any).
	## @return: true on match.
	Function of Boolean is check(TokenKind is kind, String is value){
		local Token is tok: self:peek();
		Conditional:branch(check: { tok:getTokenKind() != kind }, then: {
			return false;
		});
		Conditional:branch(check: { value != '' && tok:getValue() != value }, then: {
			return false;
		});
		return true;
	}

	## Consumes the current symbol token when it matches; records an error
	## when it does not.
	##
	## @param value: Expected symbol lexeme.
	## @return: true on match.
	Function of Boolean is matchSymbol(String is value){
		Conditional:branch(check: { self:check(kind: TokenKind:SYMBOL, value: value) }, then: {
			self:advance();
			return true;
		});
		local Token is tok: self:peek();
		self:addError(tok: tok, message: "Expected '{{value}}', found '{{tok:getValue()}}'");
		return false;
	}

	## Non-consuming symbol test.
	##
	## @param value: Expected symbol lexeme.
	## @return: true on match.
	Function of Boolean is checkSymbol(String is value){
		return self:check(kind: TokenKind:SYMBOL, value: value);
	}

	## Consumes the current punctuation token when it matches; records an
	## error when it does not.
	##
	## @param p: Expected punctuation.
	## @return: true on match.
	Function of Boolean is matchPunct(Punctuation is p){
		Conditional:branch(check: { self:check(kind: TokenKind:SYMBOL, value: p:value()) }, then: {
			self:advance();
			return true;
		});
		local Token is tok: self:peek();
		self:addError(tok: tok, message: "Expected '{{p:value()}}', found '{{tok:getValue()}}'");
		return false;
	}

	## Non-consuming punctuation test.
	##
	## @param p: Expected punctuation.
	## @return: true on match.
	Function of Boolean is checkPunct(Punctuation is p){
		return self:check(kind: TokenKind:SYMBOL, value: p:value());
	}

	## Non-consuming reserved-word test.
	##
	## @param kw: Expected keyword.
	## @return: true on match.
	Function of Boolean is checkKeyword(Keyword is kw){
		return self:check(kind: TokenKind:KEYWORD, value: kw:value());
	}

	## Consumes the current reserved word when it matches; records an error
	## when it does not.
	##
	## @param kw: Expected keyword.
	## @return: true on match.
	Function of Boolean is matchKeyword(Keyword is kw){
		Conditional:branch(check: { self:check(kind: TokenKind:KEYWORD, value: kw:value()) }, then: {
			self:advance();
			return true;
		});
		local Token is tok: self:peek();
		self:addError(tok: tok, message: "Expected '{{kw:value()}}', found '{{tok:getValue()}}'");
		return false;
	}

	## Parses the token stream into a root [ProgramNode].
	##
	## @return: All top-level class definitions.
	Function of ProgramNode is parseProgram(){
		local Array of ClassInfo is classes: [];
		While:run(loop: ProgramParseLoop:init(parser: self, classes: classes));
		return ProgramNode:init(classes: classes);
	}

	## True when the cursor sits on a class declaration header. `Class` is
	## not a keyword: it is the root class every declaration derives from,
	## so the header is recognized by its canonical class name.
	##
	## @return: true when the next tokens begin a class declaration.
	Function of Boolean is atClassHeader(){
		return self:check(kind: TokenKind:IDENTIFIER, value: self:names:classHeader());
	}

	## True when the cursor sits on an enum declaration header — same rule
	## as [atClassHeader]: `Enum` is the root class, recognized by name.
	##
	## @return: true when the next tokens begin an enum declaration.
	Function of Boolean is atEnumHeader(){
		return self:check(kind: TokenKind:IDENTIFIER, value: self:names:enumHeader());
	}

	## Parses the shared `when` arm block (between the braces). Used by both
	## the statement and expression forms, which differ only in their result
	## node.
	##
	## @return: The parsed arms.
	local Function of Array of WhenArm is parseWhenArms(){
		self:matchPunct(p: Punctuation:BLOCK_OPEN);
		local Array of WhenArm is arms: [];
		While:run(loop: WhenArmsLoop:init(parser: self, arms: arms));
		self:matchPunct(p: Punctuation:BLOCK_CLOSE);
		return arms;
	}

	## Parses one class declaration: `Class of Parent is Name` with optional
	## post-name generic parameters.
	##
	## @return: The class descriptor.
	Function of ClassInfo is parseClass(){
		Conditional:branch(check: { self:peek():getValue() == self:names:legacyClassSpelling() }, then: {
			self:addError(tok: self:peek(), message: "The 'class' keyword is no longer valid; declare classes as 'Class of Parent is Name'.");
		});
		self:advance();

		# Pre-binder `of`: parent classes.
		local Array of String is baseClasses: [];
		Conditional:branch(check: { self:checkKeyword(kw: Keyword:OF) }, then: {
			self:advance();
			While:run(loop: BaseClassesLoop:init(parser: self, bases: baseClasses));
		});

		self:matchKeyword(kw: Keyword:IS);
		local Token is nameTok: self:advance();
		local String is name: nameTok:getValue();

		# Post-name `of`: generic type parameters.
		local Array of String is typeParams: [];
		Conditional:branch(check: { self:checkKeyword(kw: Keyword:OF) }, then: {
			self:advance();
			local Token is tp1: self:advance();
			typeParams:add(item: tp1:getValue());
			Conditional:branch(check: { self:checkKeyword(kw: Keyword:TO) }, then: {
				self:advance();
				local Token is tp2: self:advance();
				typeParams:add(item: tp2:getValue());
			});
		});

		self:matchPunct(p: Punctuation:BLOCK_OPEN);
		local Array of Member is members: [];
		While:run(loop: ClassMembersLoop:init(parser: self, members: members));
		self:matchPunct(p: Punctuation:BLOCK_CLOSE);

		local ClassInfo is c: ClassInfo:init(name: name, baseClass: '', members: members);
		c:setLine(line: nameTok:getLine());
		c:setSourceFile(file: self:sourceFile);
		c:setTypeParams(params: typeParams);
		c:withBaseClasses(name: name, baseClasses: baseClasses, members: members);
		return c;
	}

	## Parses one enum declaration: `Enum of Backing is Name` with tagged or
	## ordinal variants.
	##
	## @return: The enum descriptor (base class Enum).
	Function of ClassInfo is parseEnum(){
		self:advance();
		local String is backingType: self:names:intName();
		Conditional:branch(check: { self:checkKeyword(kw: Keyword:OF) }, then: {
			self:advance();
			local Type is bt: self:parseType();
			backingType: bt:name;
		});
		self:matchKeyword(kw: Keyword:IS);
		local Token is nameTok: self:advance();
		local String is name: nameTok:getValue();
		self:matchPunct(p: Punctuation:BLOCK_OPEN);

		local Array of Member is members: [];
		While:run(loop: EnumVariantsLoop:init(parser: self, members: members, backingType: backingType));
		self:matchPunct(p: Punctuation:BLOCK_CLOSE);
		Conditional:branch(check: { self:checkPunct(p: Punctuation:TERMINATOR) }, then: {
			self:advance();
		});

		local ClassInfo is c: ClassInfo:init(name: name, baseClass: self:names:enumHeader(), members: members);
		c:setLine(line: nameTok:getLine());
		c:setSourceFile(file: self:sourceFile);
		c:withBaseClasses(name: name, baseClasses: [self:names:enumHeader()], members: members);
		return c;
	}

	## Parses one class-body member: method, field, nested class, or
	## shorthand metadata property.
	##
	## @return: The member descriptor.
	Function of Member is parseMember(){
		local Int is startLine: self:peek():getLine();
		local Array of String is modifiers: [];
		While:run(loop: ModifierLoop:init(parser: self, mods: modifiers));

		Conditional:branch(check: { self:atClassHeader() }, then: {
			local ClassInfo is nested: self:parseClass();
			local Member is m: Member:init(kind: MemberKind:CLASS);
			m:setLine(line: startLine);
			m:nestedClass: nested;
			return m;
		});

		Conditional:branch(check: { self:atEnumHeader() }, then: {
			local ClassInfo is edef: self:parseEnum();
			local Member is m: Member:init(kind: MemberKind:CLASS);
			m:setLine(line: startLine);
			m:nestedClass: edef;
			return m;
		});

		# Shorthand metadata property: `name: <expr>;` — the namespace/using
		# declaration form (an untyped field with an initializer).
		# The name may lex as a KEYWORD during transition generations (a
		# metadata name that shares an enum variant's tag); the ':' is what
		# actually discriminates the metadata form.
		Conditional:branch(check: { (self:peek():getTokenKind() == TokenKind:IDENTIFIER || self:peek():getTokenKind() == TokenKind:KEYWORD) && self:peekAhead(offset: 1):getTokenKind() == TokenKind:SYMBOL && self:peekAhead(offset: 1):getValue() == ':' }, then: {
			local Token is nameTok: self:advance();
			self:advance();
			local Expression is initExpr: self:parseExpression();
			Conditional:branch(check: { self:checkPunct(p: Punctuation:TERMINATOR) }, then: {
				self:advance();
			});
			local Member is m: Member:init(kind: MemberKind:FIELD);
			m:setLine(line: nameTok:getLine());
			m:modifiers: modifiers;
			m:memberType: Type:init(name: '');
			m:name: nameTok:getValue();
			m:initExpr: initExpr;
			m:hasInit: true;
			return m;
		});

		# Untyped (void) method: `name(params) { ... }`.
		Conditional:branch(check: { self:peek():getTokenKind() == TokenKind:IDENTIFIER && self:peekAhead(offset: 1):getValue() == Punctuation:GROUP_OPEN:value() }, then: {
			local Token is nameTok: self:advance();
			local String is name: nameTok:getValue();
			self:advance();

			local Array of Parameter is params: [];
			While:run(loop: ParamLoop:init(parser: self, params: params));
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
			local Array of Statement is body: self:parseMethodBody(params: params);

			local Member is m: Member:init(kind: MemberKind:METHOD);
			m:setLine(line: nameTok:getLine());
			m:modifiers: modifiers;
			m:memberType: Type:init(name: self:names:voidMemberType());
			m:name: name;
			m:params: params;
			m:body: body;
			return m;
		});

		local Type is mType: self:parseType();
		self:matchKeyword(kw: Keyword:IS);
		local Token is nameTok: self:advance();
		local String is name: nameTok:getValue();

		Conditional:branch(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
			self:advance();
			local Array of Parameter is params: [];
			While:run(loop: ParamLoop:init(parser: self, params: params));
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
			# Interface-style declaration: a `;`-terminated signature with no
			# body — the sysinternal floor-binding form.
			Conditional:branch(check: { self:checkPunct(p: Punctuation:TERMINATOR) }, then: {
				self:advance();
				local Member is m: Member:init(kind: MemberKind:METHOD);
				m:setLine(line: nameTok:getLine());
				m:modifiers: modifiers;
				m:memberType: mType;
				m:name: name;
				m:params: params;
				return m;
			});
			local Array of Statement is body: self:parseMethodBody(params: params);

			local Member is m: Member:init(kind: MemberKind:METHOD);
			m:setLine(line: nameTok:getLine());
			m:modifiers: modifiers;
			m:memberType: mType;
			m:name: name;
			m:params: params;
			m:body: body;
			return m;
		});

		# Field
		local Expression is initExpr;
		local Boolean is hasInit: false;
		Conditional:branch(check: { self:checkPunct(p: Punctuation:ASSIGN) }, then: {
			self:advance();
			initExpr: self:parseExpression();
			hasInit: true;
		});
		self:matchPunct(p: Punctuation:TERMINATOR);

		local Member is m: Member:init(kind: MemberKind:FIELD);
		m:setLine(line: nameTok:getLine());
		m:modifiers: modifiers;
		m:memberType: mType;
		m:name: name;
		m:initExpr: initExpr;
		m:hasInit: hasInit;
		return m;
	}

	## Parses a method body, seeding the receiver-field assignments that
	## `self: field` parameters imply.
	##
	## @param params: The method's parameters.
	## @return: The body statements.
	local Function of Array of Statement is parseMethodBody(Array of Parameter is params){
		self:matchPunct(p: Punctuation:BLOCK_OPEN);
		local Array of Statement is body: [];
		params:each(action: local Function(Parameter is p){
			Conditional:branch(check: { p:paramType:name == self:names:selfFieldMarker() }, then: {
				local Expression is lhs: Expression:init(kind: ExpressionKind:PATH);
				lhs:makePath(segments: [self:names:selfIdent(), p:name]);
				local Expression is rhs: Expression:init(kind: ExpressionKind:IDENT);
				rhs:makeIdent(name: p:name);
				local Statement is assignS: Statement:init(kind: StatementKind:ASSIGN);
				assignS:assign(target: lhs, value: rhs);
				body:add(item: assignS);
			});
		});
		While:run(loop: BlockStatementsLoop:init(parser: self, stmts: body));
		self:matchPunct(p: Punctuation:BLOCK_CLOSE);
		return body;
	}

	## Parses one type reference: a base name with optional `of`/`to`
	## generic arguments, or a bracketed list literal type.
	##
	## @return: The type descriptor.
	Function of Type is parseType(){
		Conditional:branch(check: { self:checkPunct(p: Punctuation:BRACKET_OPEN) }, then: {
			self:advance();
			local Type is elem: self:parseType();
			self:matchPunct(p: Punctuation:BRACKET_CLOSE);
			local Type is lnode: Type:init(name: self:names:listName());
			lnode:params: [elem];
			return lnode;
		});
		local Token is baseTok: self:advance();
		local String is typeName: baseTok:getValue();

		Conditional:branch(check: { self:checkKeyword(kw: Keyword:OF) }, then: {
			self:advance();
			local Array of Type is params: [];
			params:add(item: self:parseType());

			Conditional:branch(check: { self:checkKeyword(kw: Keyword:TO) }, then: {
				self:advance();
				params:add(item: self:parseType());
			});

			local Type is node: Type:init(name: typeName);
			node:params: params;
			return node;
		});

		return Type:init(name: typeName);
	}

	## Parses one statement.
	##
	## @return: The statement node.
	Function of Statement is parseStatement(){
		local Int is startLine: self:peek():getLine();

		# Merge-forward statement: `(arg, name: arg, ...)`.
		Conditional:branch(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
			return self:parseForwardStatement(startLine: startLine);
		});

		# Scoped callback statement: `as: call;` or `as (params): call;`.
		Conditional:branch(check: { self:checkKeyword(kw: Keyword:AS) }, then: {
			return self:parseAsStatement(startLine: startLine);
		});

		Conditional:branch(check: { self:atClassHeader() }, then: {
			local ClassInfo is cls: self:parseClass();
			local Statement is s: Statement:init(kind: StatementKind:CLASS);
			s:setLine(line: startLine);
			s:nestedClass: cls;
			return s;
		});

		Conditional:branch(check: { self:atEnumHeader() }, then: {
			local ClassInfo is edef: self:parseEnum();
			local Statement is s: Statement:init(kind: StatementKind:CLASS);
			s:setLine(line: startLine);
			s:nestedClass: edef;
			return s;
		});

		Conditional:branch(check: { self:checkKeyword(kw: Keyword:WHEN) }, then: {
			self:advance();
			self:matchPunct(p: Punctuation:GROUP_OPEN);
			local Expression is subject: self:parseExpression();
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
			local Array of WhenArm is arms: self:parseWhenArms();

			local Statement is s: Statement:init(kind: StatementKind:WHEN);
			s:setLine(line: startLine);
			s:whenStmt(subject: subject, arms: arms);
			return s;
		});

		Conditional:branch(check: { self:checkKeyword(kw: Keyword:IF) }, then: {
			self:advance();
			self:matchPunct(p: Punctuation:GROUP_OPEN);
			local Expression is cond: self:parseExpression();
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
			self:matchPunct(p: Punctuation:BLOCK_OPEN);

			local Array of Statement is thenBranch: [];
			While:run(loop: BlockStatementsLoop:init(parser: self, stmts: thenBranch));
			self:matchPunct(p: Punctuation:BLOCK_CLOSE);

			local Array of Statement is elseBranch: [];
			local Boolean is hasElse: false;
			Conditional:branch(check: { self:checkKeyword(kw: Keyword:ELSE) }, then: {
				self:advance();
				hasElse: true;
				Conditional:branch(check: { self:checkKeyword(kw: Keyword:IF) }, then: {
					elseBranch:add(item: self:parseStatement());
				}, otherwise: {
					self:matchPunct(p: Punctuation:BLOCK_OPEN);
					While:run(loop: BlockStatementsLoop:init(parser: self, stmts: elseBranch));
					self:matchPunct(p: Punctuation:BLOCK_CLOSE);
				});
			});

			local Statement is s: Statement:init(kind: StatementKind:IF);
			s:setLine(line: startLine);
			s:ifCondition: cond;
			s:thenBranch: thenBranch;
			s:elseBranch: elseBranch;
			s:hasElse: hasElse;
			return s;
		});

		Conditional:branch(check: { self:checkKeyword(kw: Keyword:RETURN) }, then: {
			self:advance();
			Conditional:branch(check: { self:checkKeyword(kw: Keyword:AS) }, then: {
				local Statement is asStmt: self:parseAsStatement(startLine: startLine);
				local Statement is s: Statement:init(kind: StatementKind:RETURN);
				s:setLine(line: startLine);
				s:returnExpr: asStmt:exprStmt;
				s:hasReturnExpr: true;
				return s;
			});
			local Expression is retExpr;
			local Boolean is hasExpr: false;
			Conditional:branch(check: { !self:checkPunct(p: Punctuation:TERMINATOR) }, then: {
				retExpr: self:parseExpression();
				hasExpr: true;
			});
			self:matchPunct(p: Punctuation:TERMINATOR);

			local Statement is s: Statement:init(kind: StatementKind:RETURN);
			s:setLine(line: startLine);
			s:returnExpr: retExpr;
			s:hasReturnExpr: hasExpr;
			return s;
		});

		Conditional:branch(check: { self:checkKeyword(kw: Keyword:LOCAL) }, then: {
			self:advance();
			local Type is vType: self:parseType();
			self:matchKeyword(kw: Keyword:IS);
			local Token is nameTok: self:advance();
			local String is name: nameTok:getValue();

			local Expression is initExpr;
			local Boolean is hasInit: false;
			Conditional:branch(check: { self:checkPunct(p: Punctuation:ASSIGN) }, then: {
				self:advance();
				initExpr: self:parseExpression();
				hasInit: true;
			});
			self:matchPunct(p: Punctuation:TERMINATOR);

			local Statement is s: Statement:init(kind: StatementKind:VAR_DECL);
			s:setLine(line: startLine);
			s:modifiers: ['local'];
			s:varType: vType;
			s:varName: name;
			s:initExpr: initExpr;
			s:hasInit: hasInit;
			return s;
		});

		# Expression or assignment: `target: value;` assigns, anything else
		# evaluates for effect.
		local Expression is expr: self:parseExpression();

		Conditional:branch(check: { self:checkPunct(p: Punctuation:ASSIGN) }, then: {
			self:advance();
			local Expression is val: self:parseExpression();
			self:matchPunct(p: Punctuation:TERMINATOR);

			local Statement is s: Statement:init(kind: StatementKind:ASSIGN);
			s:setLine(line: startLine);
			s:assignTarget: expr;
			s:assignValue: val;
			return s;
		});

		self:matchPunct(p: Punctuation:TERMINATOR);
		local Statement is s: Statement:init(kind: StatementKind:EXPR);
		s:setLine(line: startLine);
		s:exprStmt: expr;
		return s;
	}

	## Parses a merge-forward statement: `(arg, name: arg, ...)`.
	##
	## Valid only inside `merge` methods (enforced by the checker).
	##
	## @param startLine: Source line of the opening parenthesis.
	## @return: The FORWARD statement.
	local Function of Statement is parseForwardStatement(Int is startLine){
		self:advance();
		local Array of NamedArg is args: [];
		While:condition(
			evaluate: local Function of Boolean(){
				return !self:checkPunct(p: Punctuation:GROUP_CLOSE) && !self:check(kind: TokenKind:EOF, value: '');
			},
			iteration: local Function of Boolean(){
				local String is argName: '';
				local Token is tok0: self:peekAhead(offset: 0);
				Conditional:branch(check: { tok0:getTokenKind() == TokenKind:IDENTIFIER && self:peekAhead(offset: 1):getValue() == Punctuation:NAMED_ARG:value() }, then: {
					argName: tok0:getValue();
					self:advance();
					self:advance();
				});
				local Expression is val: self:parseExpression();
				args:add(item: NamedArg:init(name: argName, value: val));
				Conditional:branch(check: { self:checkPunct(p: Punctuation:SEPARATOR) }, then: {
					self:advance();
					return true;
				});
				return false;
			}
		);
		self:matchPunct(p: Punctuation:GROUP_CLOSE);
		Conditional:branch(check: { self:checkPunct(p: Punctuation:TERMINATOR) }, then: {
			self:advance();
		});
		local Statement is s: Statement:init(kind: StatementKind:FORWARD);
		s:setLine(line: startLine);
		s:forwardArgs: args;
		return s;
	}

	## Parses an `as` statement that desugars into a trailing callback:
	##   `as: callExpr;`
	##   `as (params): callExpr;`
	##   `as (params) of Type: callExpr;`
	##
	## The remainder of the enclosing block is collected into an anonymous
	## function and appended as a trailing positional argument to callExpr.
	##
	## @param startLine: Source line of the `as` keyword.
	## @return: The desugared EXPR statement holding the call.
	local Function of Statement is parseAsStatement(Int is startLine){
		self:advance();
		local Array of Parameter is params: [];
		local Boolean is hasParams: false;
		Conditional:branch(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
			self:advance();
			hasParams: true;
			While:run(loop: ParamLoop:init(parser: self, params: params));
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
		});
		local Type is returnType: Type:init(name: self:names:voidName());
		Conditional:branch(check: { self:checkKeyword(kw: Keyword:OF) }, then: {
			self:advance();
			returnType: self:parseType();
		});
		Conditional:branch(check: { self:checkPunct(p: Punctuation:ACCESSOR) }, then: {
			self:advance();
		}, otherwise: {
			Conditional:branch(check: { !hasParams }, then: {
				self:matchPunct(p: Punctuation:ACCESSOR);
			});
		});
		local Expression is callExpr: self:parseExpression();
		self:matchPunct(p: Punctuation:TERMINATOR);

		local Array of Statement is closureBody: [];
		While:run(loop: BlockStatementsLoop:init(parser: self, stmts: closureBody));

		local Expression is anonFn: Expression:init(kind: ExpressionKind:ANON_FN);
		anonFn:anonReturnType: returnType;
		anonFn:anonParams: params;
		anonFn:anonBody: closureBody;

		Conditional:branch(check: { callExpr:kind != ExpressionKind:CALL }, then: {
			local Expression is c: Expression:init(kind: ExpressionKind:CALL);
			Conditional:branch(check: { callExpr:kind == ExpressionKind:FIELD_ACCESS }, then: {
				c:methodTarget: callExpr:leftExpr;
				c:methodName: callExpr:stringValue;
			}, otherwise: {
				Conditional:branch(check: { callExpr:kind == ExpressionKind:IDENT }, then: {
					local Expression is selfTarget: Expression:init(kind: ExpressionKind:IDENT);
					selfTarget:stringValue: self:names:selfIdent();
					c:methodTarget: selfTarget;
					c:methodName: callExpr:stringValue;
				}, otherwise: {
					c:methodTarget: callExpr;
					c:methodName: '';
				});
			});
			c:methodArgs: [];
			callExpr: c;
		});

		callExpr:methodArgs:add(item: NamedArg:init(name: '', value: anonFn));
		# FUNCTIONS.md §as: the remainder is not an argument — it fills the
		# callable's declared-but-unbound last Function parameter. The
		# marker keeps it out of overload selection.
		callExpr:scopedRemainder: true;

		local Statement is s: Statement:init(kind: StatementKind:EXPR);
		s:setLine(line: startLine);
		s:exprStmt: callExpr;
		return s;
	}

	## Parses one full expression (entry at the loosest precedence).
	##
	## @return: The expression node.
	Function of Expression is parseExpression(){
		return self:parseLevel(level: PrecedenceLevel:LOGICAL_OR);
	}

	## Parses one binary precedence level via the parameterized fold loop.
	##
	## @param level: The level to fold.
	## @return: The folded expression.
	Function of Expression is parseLevel(PrecedenceLevel is level){
		when (level) {
			is PrecedenceLevel:MULTIPLICATIVE: { return self:foldBinary(ops: ['*', '/', '%'], next: PrecedenceLevel:NONE); }
			is PrecedenceLevel:ADDITIVE: { return self:foldBinary(ops: ['+', '-'], next: PrecedenceLevel:MULTIPLICATIVE); }
			is PrecedenceLevel:SHIFT: { return self:foldBinary(ops: ['<<', '>>'], next: PrecedenceLevel:ADDITIVE); }
			is PrecedenceLevel:CONCAT: { return self:foldBinary(ops: ['.'], next: PrecedenceLevel:SHIFT); }
			is PrecedenceLevel:RELATIONAL: { return self:foldBinary(ops: ['<', '<=', '>', '>='], next: PrecedenceLevel:CONCAT); }
			is PrecedenceLevel:EQUALITY: { return self:foldBinary(ops: ['==', '!=', 'is'], next: PrecedenceLevel:RELATIONAL); }
			is PrecedenceLevel:BIT_AND: { return self:foldBinary(ops: ['&'], next: PrecedenceLevel:EQUALITY); }
			is PrecedenceLevel:BIT_XOR: { return self:foldBinary(ops: ['^'], next: PrecedenceLevel:BIT_AND); }
			is PrecedenceLevel:BIT_OR: { return self:foldBinary(ops: ['|'], next: PrecedenceLevel:BIT_XOR); }
			is PrecedenceLevel:LOGICAL_AND: { return self:foldBinary(ops: ['&&'], next: PrecedenceLevel:BIT_OR); }
			is PrecedenceLevel:LOGICAL_OR: { return self:foldBinary(ops: ['||'], next: PrecedenceLevel:LOGICAL_AND); }
			else: { return self:parseUnary(); }
		}
	}

	## Folds one level: parse the next-lower level for the left operand,
	## then run [BinaryFoldLoop] over the operator set.
	##
	## @param ops: This level's operator lexemes.
	## @param next: The next-lower level (NONE descends to unary).
	## @return: The folded expression.
	Function of Expression is foldBinary(Array of String is ops, PrecedenceLevel is next){
		local Expression is left: Expression:init(kind: ExpressionKind:UNKNOWN);
		Conditional:branch(check: { next == PrecedenceLevel:NONE }, then: {
			left: self:parseUnary();
		}, otherwise: {
			left: self:parseLevel(level: next);
		});
		local BinaryFoldLoop is fold: BinaryFoldLoop:init(parser: self, expr: left, ops: ops, next: next);
		While:run(loop: fold);
		return fold:currentExpr;
	}

	## Parses unary operators (~, -, !) or descends to casts.
	##
	## @return: The expression node.
	Function of Expression is parseUnary(){
		local String is op: '';
		Conditional:branch(check: { self:checkSymbol(value: '++') }, then: {
			op: '++';
		}, otherwise: {
			Conditional:branch(check: { self:checkSymbol(value: '--') }, then: {
				op: '--';
			}, otherwise: {
				Conditional:branch(check: { self:checkSymbol(value: '~') }, then: {
					op: '~';
				}, otherwise: {
					Conditional:branch(check: { self:checkSymbol(value: '-') }, then: {
						op: '-';
					}, otherwise: {
						Conditional:branch(check: { self:checkSymbol(value: '!') }, then: {
							op: '!';
						}, otherwise: {
							return self:parseAs();
						});
					});
				});
			});
		});
		self:advance();
		local Expression is expr: self:parseUnary();
		local Expression is u: Expression:init(kind: ExpressionKind:UNARY);
		u:unaryOp: op;
		u:unaryExpr: expr;
		return u;
	}

	## Parses the instance-import form `as ClassName(args)` — a using-entry
	## terminator (INSTANCE.md §2.1). Arguments must be direct literal
	## values (INSTANCE.md E1); parentheses are required so the form can
	## never be confused with the postfix cast.
	##
	## @return: The USING_AS expression node.
	Function of Expression is parseUsingAs(){
		self:advance();
		local Token is clsTok: self:peek();
		Conditional:branch(check: { clsTok:getTokenKind() != TokenKind:IDENTIFIER }, then: {
			self:addError(tok: clsTok, message: "'as' in a using entry must be followed by a class name.");
			return Expression:init(kind: ExpressionKind:UNKNOWN);
		});
		self:advance();
		local Expression is e: Expression:init(kind: ExpressionKind:USING_AS);
		e:stringValue: clsTok:getValue();
		Conditional:branch(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
			self:advance();
			Conditional:branch(check: { !self:checkPunct(p: Punctuation:GROUP_CLOSE) }, then: {
				local Array of NamedArg is args: [];
				While:run(loop: ArgLoop:init(parser: self, args: args));
				e:methodArgs: args;
				args:each(action: local Function(NamedArg is arg){
					local ExpressionKind is ak: arg:value:kind;
					Conditional:branch(check: { ak != ExpressionKind:STRING && ak != ExpressionKind:NUMBER && ak != ExpressionKind:FLOAT && ak != ExpressionKind:BOOL }, then: {
						self:addError(tok: clsTok, message: 'Instance-import arguments must be direct literal values (INSTANCE.md E1).');
					});
				});
			});
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
		}, otherwise: {
			self:addError(tok: clsTok, message: "Instance import requires parentheses: 'as " . e:stringValue . "()'.");
		});
		return e;
	}

	## Parses a type cast: `value as Target` or `value as Target(width)`.
	## Binding is tighter than every binary operator; chaining
	## (`x as A as B`) is rejected.
	##
	## @return: The expression node.
	Function of Expression is parseAs(){
		local Expression is left: self:parsePostfix();
		Conditional:branch(check: { self:checkKeyword(kw: Keyword:AS) }, then: {
			self:advance();
			local Token is targetTok: self:advance();
			local Array of Expression is args: [];
			Conditional:branch(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
				self:advance();
				Conditional:branch(check: { !self:checkPunct(p: Punctuation:GROUP_CLOSE) }, then: {
					args:add(item: self:parseExpression());
				});
				self:matchPunct(p: Punctuation:GROUP_CLOSE);
			});
			Conditional:branch(check: { self:checkKeyword(kw: Keyword:AS) }, then: {
				self:addError(tok: self:peek(), message: "Chained 'as' casts are not supported; cast in separate steps.");
			});
			local Expression is c: Expression:init(kind: ExpressionKind:CAST);
			c:makeCast(inner: left, target: targetTok:getValue(), args: args);
			return c;
		});
		return left;
	}

	## Parses postfix trailers (calls, indexes, colon-paths) after a
	## primary expression.
	##
	## @return: The expression node.
	Function of Expression is parsePostfix(){
		local Expression is expr: self:parsePrimary();
		local PostfixLoop is postLoop: PostfixLoop:init(parser: self, expr: expr);
		While:run(loop: postLoop);
		return postLoop:currentExpr;
	}

	## Parses a primary expression: literals, identifiers, parenthesized
	## expressions, array/map literals, `when`, inline `if`, and anonymous
	## functions. Template strings desugar here.
	##
	## @return: The expression node.
	Function of Expression is parsePrimary(){
		# Anonymous function: `Function of T is (params) { ... }` or its
		# `local`-prefixed form.
		local Boolean is isAnonFn: false;
		Conditional:branch(check: { self:checkKeyword(kw: Keyword:LOCAL) && self:peekAhead(offset: 1):getValue() == self:names:fnName() }, then: {
			isAnonFn: true;
		});
		Conditional:branch(check: { self:peek():getValue() == self:names:fnName() && (self:peekAhead(offset: 1):getValue() == Punctuation:GROUP_OPEN:value() || self:peekAhead(offset: 1):getValue() == Keyword:OF:value()) }, then: {
			isAnonFn: true;
		});

		Conditional:branch(check: { isAnonFn }, then: {
			Conditional:branch(check: { self:checkKeyword(kw: Keyword:LOCAL) }, then: {
				self:advance();
			});
			self:advance();
			local Type is returnType: Type:init(name: self:names:voidName());
			Conditional:branch(check: { self:checkKeyword(kw: Keyword:OF) }, then: {
				self:advance();
				returnType: self:parseType();
			});
			self:matchPunct(p: Punctuation:GROUP_OPEN);
			local Array of Parameter is params: [];
			While:run(loop: ParamLoop:init(parser: self, params: params));
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
			local Array of Statement is body: self:parseMethodBody(params: params);

			local Expression is e: Expression:init(kind: ExpressionKind:ANON_FN);
			e:anonReturnType: returnType;
			e:anonParams: params;
			e:anonBody: body;
			return e;
		});

		Conditional:branch(check: { self:checkKeyword(kw: Keyword:WHEN) }, then: {
			self:advance();
			self:matchPunct(p: Punctuation:GROUP_OPEN);
			local Expression is subject: self:parseExpression();
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
			local Array of WhenArm is arms: self:parseWhenArms();

			local Expression is e: Expression:init(kind: ExpressionKind:WHEN);
			e:makeWhen(subject: subject, arms: arms);
			return e;
		});

		Conditional:branch(check: { self:checkKeyword(kw: Keyword:IF) }, then: {
			self:advance();
			self:matchPunct(p: Punctuation:GROUP_OPEN);
			local Expression is cond: self:parseExpression();
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
			local Expression is thenExpr: self:parseExpression();
			self:matchKeyword(kw: Keyword:ELSE);
			local Expression is elseExpr: self:parseExpression();
			local Expression is e: Expression:init(kind: ExpressionKind:IF_ELSE);
			e:condExpr: cond;
			e:thenExpr: thenExpr;
			e:elseExpr: elseExpr;
			return e;
		});

		local Token is tok: self:peek();

		when (tok:getTokenKind()) {
			is TokenKind:STRING: {
				self:advance();
				local Expression is e: Expression:init(kind: ExpressionKind:STRING);
				e:stringValue: tok:getValue();
				return e;
			}
			is TokenKind:RAWSTRING: {
				self:advance();
				local Expression is e: Expression:init(kind: ExpressionKind:STRING);
				e:stringValue: tok:getValue();
				return e;
			}
			is TokenKind:TEMPLATESTRING: {
				self:advance();
				return self:expandFancyString(raw: tok:getValue(), originTok: tok, depth: self:templateDepth);
			}
			is TokenKind:INT: {
				self:advance();
				local Expression is e: Expression:init(kind: ExpressionKind:NUMBER);
				e:stringValue: tok:getValue();
				return e;
			}
			is TokenKind:FLOAT: {
				self:advance();
				local Expression is e: Expression:init(kind: ExpressionKind:FLOAT);
				e:stringValue: tok:getValue();
				return e;
			}
			is TokenKind:BOOL: {
				self:advance();
				local Expression is e: Expression:init(kind: ExpressionKind:BOOL);
				e:boolValue: tok:getValue() == self:names:boolTrue();
				e:stringValue: tok:getValue();
				return e;
			}
			is TokenKind:IDENTIFIER: {
				self:advance();
				local Expression is e: Expression:init(kind: ExpressionKind:IDENT);
				e:stringValue: tok:getValue();
				return e;
			}
			is TokenKind:KEYWORD: {
				# Expression-initial `as` is the instance-import form
				# `as ClassName()` (INSTANCE.md §2.1); `as` never begins any
				# other expression (casts are postfix, scoped regions are
				# statement-initial).
				Conditional:branch(check: { self:checkKeyword(kw: Keyword:AS) }, then: {
					return self:parseUsingAs();
				});
				self:addError(tok: tok, message: "Unexpected token '{{tok:getValue()}}' in expression");
				self:advance();
				return Expression:init(kind: ExpressionKind:UNKNOWN);
			}
			else: {
				Conditional:branch(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
					self:advance();
					local Expression is inner: self:parseExpression();
					self:matchPunct(p: Punctuation:GROUP_CLOSE);
					return inner;
				});

				Conditional:branch(check: { self:checkPunct(p: Punctuation:BRACKET_OPEN) }, then: {
					return self:parseArrayOrMap();
				});

				Conditional:branch(check: { self:checkPunct(p: Punctuation:BLOCK_OPEN) }, then: {
					return self:parseFunctionBlock();
				});

				self:addError(tok: tok, message: "Unexpected token '{{tok:getValue()}}' in expression");
				self:advance();
				return Expression:init(kind: ExpressionKind:UNKNOWN);
			}
		}
	}

	## True when the current bracketed sequence begins a typed declaration
	## list `[Type is name: init, ...]` rather than a value array.
	##
	## @return: true when declaration list.
	Function of Boolean is isDeclListStart(){
		local Int is offset: 1;
		local Boolean is running: true;
		local Boolean is foundIs: false;
		While:condition(
			evaluate: local Function of Boolean(){
				return running;
			},
			iteration: local Function(){
				local Token is t: self:peekAhead(offset: offset);
				Conditional:branch(check: { t:getTokenKind() == TokenKind:EOF || t:getValue() == ']' || t:getValue() == ',' || t:getValue() == ';' }, then: {
					running: false;
				}, otherwise: {
					Conditional:branch(check: { t:getValue() == Keyword:IS:value() }, then: {
						foundIs: true;
						running: false;
					});
					offset: offset + 1;
				});
			}
		);
		return foundIs;
	}

	## Parses a scoped variable declaration list `[Type is name: init, ...]`.
	##
	## @return: ARRAY expression carrying parsed parameters in anonParams.
	Function of Expression is parseDeclList(){
		self:matchPunct(p: Punctuation:BRACKET_OPEN);
		local Array of Parameter is params: [];
		While:condition(
			evaluate: local Function of Boolean(){
				return !self:checkPunct(p: Punctuation:BRACKET_CLOSE) && !self:check(kind: TokenKind:EOF, value: '');
			},
			iteration: local Function(){
				local Type is pType: self:parseType();
				self:matchKeyword(kw: Keyword:IS);
				local Token is nameTok: self:advance();
				local Parameter is p: Parameter:init(name: nameTok:getValue(), paramType: pType);
				Conditional:branch(check: { self:checkPunct(p: Punctuation:ASSIGN) }, then: {
					self:advance();
					p:setDefault(expr: self:parseExpression());
				});
				params:add(item: p);
				Conditional:branch(check: { self:checkPunct(p: Punctuation:SEPARATOR) }, then: {
					self:advance();
				});
			}
		);
		self:matchPunct(p: Punctuation:BRACKET_CLOSE);
		local Expression is e: Expression:init(kind: ExpressionKind:ARRAY);
		e:anonParams: params;
		return e;
	}

	## Parses a function block shorthand `{ ... }` as an anonymous function.
	##
	## @return: The ANON_FN expression.
	Function of Expression is parseFunctionBlock(){
		self:matchPunct(p: Punctuation:BLOCK_OPEN);
		local Array of Statement is body: [];
		local Array of Parameter is params: [];
		local Type is returnType: Type:init(name: self:names:voidName());

		While:condition(
			evaluate: local Function of Boolean(){
				return !self:checkPunct(p: Punctuation:BLOCK_CLOSE) && !self:check(kind: TokenKind:EOF, value: '');
			},
			iteration: local Function(){
				Conditional:branch(check: { !self:checkKeyword(kw: Keyword:RETURN) && !self:checkKeyword(kw: Keyword:LOCAL) && !self:checkKeyword(kw: Keyword:IF) && !self:checkKeyword(kw: Keyword:WHEN) && !self:checkKeyword(kw: Keyword:AS) }, then: {
					local Expression is expr: self:parseExpression();
					Conditional:branch(check: { self:checkPunct(p: Punctuation:ASSIGN) }, then: {
						self:advance();
						local Expression is val: self:parseExpression();
						self:matchPunct(p: Punctuation:TERMINATOR);
						local Statement is s: Statement:init(kind: StatementKind:ASSIGN);
						s:assignTarget: expr;
						s:assignValue: val;
						body:add(item: s);
					}, otherwise: {
						Conditional:branch(check: { self:checkPunct(p: Punctuation:BLOCK_CLOSE) }, then: {
							local Statement is retS: Statement:init(kind: StatementKind:RETURN);
							retS:returnExpr: expr;
							retS:hasReturnExpr: true;
							body:add(item: retS);
						}, otherwise: {
							self:matchPunct(p: Punctuation:TERMINATOR);
							local Statement is exprS: Statement:init(kind: StatementKind:EXPR);
							exprS:exprStmt: expr;
							body:add(item: exprS);
						});
					});
				}, otherwise: {
					body:add(item: self:parseStatement());
				});
			}
		);
		self:matchPunct(p: Punctuation:BLOCK_CLOSE);

		local Expression is e: Expression:init(kind: ExpressionKind:ANON_FN);
		e:anonReturnType: returnType;
		e:anonParams: params;
		e:anonBody: body;
		return e;
	}

	## Parses a bracketed `[...]` literal: array, map, or their empty
	## forms (distinguished by `:]` for an empty map).
	##
	## @return: The ARRAY or MAP node.
	Function of Expression is parseArrayOrMap(){
		Conditional:branch(check: { self:isDeclListStart() }, then: {
			return self:parseDeclList();
		});
		self:advance();
		Conditional:branch(check: { self:checkPunct(p: Punctuation:BRACKET_CLOSE) }, then: {
			self:advance();
			local Expression is e: Expression:init(kind: ExpressionKind:ARRAY);
			e:arrayItems: [];
			return e;
		});
		Conditional:branch(check: { self:checkPunct(p: Punctuation:PAIR) }, then: {
			self:advance();
			self:matchPunct(p: Punctuation:BRACKET_CLOSE);
			local Expression is e: Expression:init(kind: ExpressionKind:MAP);
			e:makeMap(keys: [], values: []);
			return e;
		});
		local Expression is firstItem: self:parseExpression();
		Conditional:branch(check: { self:checkPunct(p: Punctuation:PAIR) }, then: {
			self:advance();
			local Expression is firstVal: self:parseExpression();
			local Array of Expression is mKeys: [firstItem];
			local Array of Expression is mVals: [firstVal];
			Conditional:branch(check: { self:checkPunct(p: Punctuation:SEPARATOR) }, then: {
				self:advance();
				While:run(loop: MapItemsLoop:init(parser: self, keys: mKeys, values: mVals));
			});
			self:matchPunct(p: Punctuation:BRACKET_CLOSE);
			local Expression is e: Expression:init(kind: ExpressionKind:MAP);
			e:makeMap(keys: mKeys, values: mVals);
			return e;
		});
		local Array of Expression is items: [firstItem];
		Conditional:branch(check: { self:checkPunct(p: Punctuation:SEPARATOR) }, then: {
			self:advance();
			While:run(loop: ArrayItemsLoop:init(parser: self, items: items));
		});
		self:matchPunct(p: Punctuation:BRACKET_CLOSE);
		local Expression is e: Expression:init(kind: ExpressionKind:ARRAY);
		e:arrayItems: items;
		return e;
	}

	## Desugars template-family string content ("..." and backtick
	## heredocs): splits literal chunks from {{expr}} holes, sub-parses each
	## hole, and folds everything into the same concat chain a programmer
	## would have written by hand. Hole-free content yields a single string
	## literal (zero runtime cost). At depth >= 1 — inside a hole — inner
	## strings stay plain: escapes only, no expansion.
	##
	## @param raw: The raw token content (escapes unparsed).
	## @param originTok: The originating token (for error provenance).
	## @param depth: Current template nesting depth.
	## @return: The desugared expression.
	Function of Expression is expandFancyString(String is raw, Token is originTok, Int is depth){
		local Expression is plainE: Expression:init(kind: ExpressionKind:STRING);
		Conditional:branch(check: { depth > 0 }, then: {
			local FancyEscapeLoop is dEsc: FancyEscapeLoop:init(src: raw);
			While:run(loop: dEsc);
			plainE:stringValue: dEsc:res;
			return plainE;
		});
		local TemplateSplitLoop is split: TemplateSplitLoop:init(raw: raw);
		While:run(loop: split);
		split:lits:add(item: split:lit);
		Conditional:branch(check: { split:inHole }, then: {
			self:addError(tok: originTok, message: 'Unterminated template hole (missing closing }})');
			plainE:stringValue: '';
			return plainE;
		});
		local Expression is acc: Expression:init(kind: ExpressionKind:STRING);
		acc:stringValue: split:lits:get(index: 0);
		Conditional:branch(check: { split:holes:length() == 0 }, then: {
			return acc;
		});
		local TemplateFoldLoop is fold: TemplateFoldLoop:init(parser: self, split: split, acc0: acc);
		While:run(loop: fold);
		return fold:acc;
	}

	## Parses one template hole's text as a full Spec expression using a
	## sub-lexer and sub-parser; the hole text must be exactly one
	## expression.
	##
	## @param text: The hole's raw text.
	## @return: The hole's expression.
	Function of Expression is parseTemplateExpression(String is text){
		local Expression is emptyE: Expression:init(kind: ExpressionKind:STRING);
		Conditional:branch(check: { text:trim():length() == 0 }, then: {
			self:addError(tok: self:peek(), message: 'Empty expression in string template');
			return emptyE;
		});
		local Lexer is subLexer: Lexer:init(source: text);
		local Array of Token is subTokens: subLexer:tokenize();
		Conditional:branch(check: { subLexer:hasErrors() }, then: {
			self:addError(tok: self:peek(), message: 'Invalid expression in string template');
			return emptyE;
		});
		local Parser is subParser: Parser:init(tokens: subTokens);
		subParser:setTemplateDepth(depth: 1);
		local Expression is e: subParser:parseExpression();
		Conditional:branch(check: { subParser:hasErrors() || subParser:peek():getTokenKind() != TokenKind:EOF }, then: {
			self:addError(tok: self:peek(), message: 'Invalid expression in string template');
			return emptyE;
		});
		return e;
	}
}
