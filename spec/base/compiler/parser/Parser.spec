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
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', Error],
		['base', 'sys', as Reflection()],
		['base', 'compiler', WellKnown],
		['base', 'compiler', 'parser', PrecedenceLevel],
		['base', 'compiler', 'parser', TemplateEscapes],
		['base', 'compiler', 'parser', EnumDesugar],
		['base', 'compiler', 'utils', Chars],
		['base', 'iterator'],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],

	];

	local Array of Token is tokens: [];
	local Int is pos: 0;
	local Int is length: 0;
	local String is sourceFile: '';
	local Array of Error is errors: [];

	local Lexer is lexer;
	local Array of Token is lookahead: [];
	local Boolean is streaming: false;

	# Nesting depth of template desugaring: 0 at statement level, >= 1
	# inside a template hole (inner strings stay plain — no nested
	# template expansion).
	local Int is templateDepth: 0;

	## Well-known names (builtin types, sentinels).
	local WellKnown is names: WellKnown:init();

	## Character classifier (for named-argument uppercase heuristic).
	local Chars is chars: Chars:init();

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
		self:streaming: false;
		self:lookahead: [];
	}

	## Configures the parser to stream tokens on-demand from a lexer.
	##
	## @param lexer: The active lexer instance.
	Function is setLexer(Lexer is lexer){
		self:lexer: lexer;
		self:streaming: true;
		self:lookahead: [];
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
		local String is prefix: Conditional:if(check: { self:sourceFile != '' }, then: { self:sourceFile . ':' }, else: { 'Line ' });
		local Error is e: Error:init(message: "  [SyntaxError] [{{prefix}}{{tok:getLine()}}:{{tok:getCol()}}] {{message}}");
		e:addTraceAt(className: Reflection:class(), methodName: Reflection:method(), line: tok:getLine(), col: tok:getCol());
		self:errors:add(item: e);
	}

	## Returns the current token without consuming it.
	##
	## @return: The current token; EOF past the end.
	Function of Token is peek(){
		Conditional:if(check: { self:streaming }, then: {
			return self:peekAhead(offset: 0);
		});
		Conditional:if(check: { self:pos < self:length }, then: {
			return self:tokens:get(index: self:pos);
		});
		return Token:init(kind: TokenKind:EOF, value: '', line: 0, col: 0);
	}

	## Returns the token [offset] positions ahead.
	##
	## @param offset: Lookahead distance.
	## @return: The token; EOF past the end.
	Function of Token is peekAhead(Int is offset){
		Conditional:if(check: { self:streaming }, then: {
			local Boolean is pulling: true;
			while({ pulling && self:lookahead:length() <= offset }, {
				local Token is tok: self:lexer:nextToken();
				self:lookahead:add(item: tok);
				Conditional:if(check: { tok:getTokenKind() == TokenKind:EOF }, then: {
					pulling: false;
				});
			});
			Conditional:if(check: { offset < self:lookahead:length() }, then: {
				return self:lookahead:get(index: offset);
			});
			return Token:init(kind: TokenKind:EOF, value: '', line: 0, col: 0);
		});
		local Int is idx: self:pos + offset;
		Conditional:if(check: { idx < self:length }, then: {
			return self:tokens:get(index: idx);
		});
		return Token:init(kind: TokenKind:EOF, value: '', line: 0, col: 0);
	}

	## Consumes and returns the current token.
	##
	## @return: The consumed token.
	Function of Token is advance(){
		Conditional:if(check: { self:streaming }, then: {
			local Token is tok: self:peekAhead(offset: 0);
			self:lookahead:removeAt(index: 0, default: tok);
			return tok;
		});
		local Token is tok: self:peek();
		Conditional:if(check: { self:pos < self:length }, then: {
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
		Conditional:if(check: { nxt:getTokenKind() == TokenKind:EOF }, then: {
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
		Conditional:if(check: { tok:getTokenKind() != kind }, then: {
			return false;
		});
		Conditional:if(check: { value != '' && tok:getValue() != value }, then: {
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
		Conditional:if(check: { self:check(kind: TokenKind:SYMBOL, value: value) }, then: {
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
		Conditional:if(check: { self:check(kind: TokenKind:SYMBOL, value: p:value()) }, then: {
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
		Conditional:if(check: { self:check(kind: TokenKind:KEYWORD, value: kw:value()) }, then: {
			self:advance();
			return true;
		});
		local Token is tok: self:peek();
		self:addError(tok: tok, message: "Expected '{{kw:value()}}', found '{{tok:getValue()}}'");
		return false;
	}

	## Consumes call arguments: positional or `name: value` pairs.
	Function of Array of NamedArg is parseArgs(){
		local Array of NamedArg is args: [];
		local Boolean is keepGoing: true;
		while({ keepGoing && !self:checkPunct(p: Punctuation:GROUP_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
			local String is argName: '';
			local Token is tok0: self:peekAhead(offset: 0);
			Conditional:if(check: { tok0:getTokenKind() == TokenKind:IDENTIFIER && self:peekAhead(offset: 1):getValue() == Punctuation:NAMED_ARG:value() }, then: {
				local String is nameVal: tok0:getValue();
				local Boolean is isUpper: self:chars:isUpper(ch: nameVal:charAt(index: 0, default: ''));
				Conditional:if(check: { !isUpper }, then: {
					local Token is nextTok: self:peekAhead(offset: 2);
					local Boolean is isNamed: false;
					Conditional:if(check: { nextTok:getTokenKind() != TokenKind:IDENTIFIER }, then: {
						isNamed: true;
					}, else: {
						isNamed: self:hasWhitespaceAfter(offset: 1);
					});
					Conditional:if(check: { isNamed }, then: {
						local Token is aTok: self:advance();
						argName: aTok:getValue();
						self:advance();
					});
				});
			});
			local Expression is val: self:parseExpression();
			args:add(item: NamedArg:init(name: argName, value: val));
			Conditional:if(check: { self:checkPunct(p: Punctuation:SEPARATOR) }, then: {
				self:advance();
			}, else: {
				keepGoing: false;
			});
		});
		return args;
	}

	## Consumes formal parameter lists: `Type is name`, shorthand `name`
	## (Any-typed), and `self: field` receiver fields.
	Function of Array of Parameter is parseParams(){
		local Array of Parameter is params: [];
		local Boolean is keepGoing: true;
		while({ keepGoing && !self:checkPunct(p: Punctuation:GROUP_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
			# `self: field` declares a receiver field parameter.
			Conditional:if(check: { self:peek():getValue() == self:names:selfIdent() && self:peekAhead(offset: 1):getValue() == ':' }, then: {
				self:advance();
				self:advance();
				local Token is fTok: self:advance();
				local Parameter is param: Parameter:init(name: fTok:getValue(), paramType: Type:init(name: self:names:selfFieldMarker()));
				Conditional:if(check: { self:checkPunct(p: Punctuation:DEFAULT) }, then: {
					self:advance();
					param:setDefault(expr: self:parseExpression());
				});
				params:add(item: param);
				Conditional:if(check: { self:checkPunct(p: Punctuation:SEPARATOR) }, then: {
					self:advance();
				}, else: {
					keepGoing: false;
				});
			}, else: {
				# Shorthand: a bare identifier is an Any-typed parameter.
				Conditional:if(check: { self:peekAhead(offset: 1):getValue() == Punctuation:SEPARATOR:value() || self:peekAhead(offset: 1):getValue() == Punctuation:GROUP_CLOSE:value() }, then: {
					local Token is pTok: self:advance();
					params:add(item: Parameter:init(name: pTok:getValue(), paramType: Type:init(name: self:names:anyName())));
					Conditional:if(check: { self:checkPunct(p: Punctuation:SEPARATOR) }, then: {
						self:advance();
					}, else: {
						keepGoing: false;
					});
				}, else: {
					local Type is pType: self:parseType();
					self:matchKeyword(kw: Keyword:IS);
					local Token is pTok: self:advance();
					local Parameter is param: Parameter:init(name: pTok:getValue(), paramType: pType);
					Conditional:if(check: { self:checkPunct(p: Punctuation:DEFAULT) }, then: {
						self:advance();
						param:setDefault(expr: self:parseExpression());
					});
					params:add(item: param);
					Conditional:if(check: { self:checkPunct(p: Punctuation:SEPARATOR) }, then: {
						self:advance();
					}, else: {
						keepGoing: false;
					});
				});
			});
		});
		return params;
	}

	## Parses the token stream into a root [ProgramNode].
	##
	## @return: All top-level class definitions.
	Function of ProgramNode is parseProgram(){
		local Array of ClassInfo is classes: [];
		while({ !self:check(kind: TokenKind:EOF, value: '') }, {
			Conditional:if(check: { self:atEnumHeader() }, then: {
				classes:add(item: self:parseEnum());
			}, else: {
				classes:add(item: self:parseClass());
			});
		});
		self:linkNestedClasses(classes: classes);
		return ProgramNode:init(classes: classes);
	}

	## links nested classes to their enclosing
	## class — the qualified outer chain (outerName) and the parent link
	## (the outer appended to baseClasses), so the standard lattice walks
	## serve inner classes. Recurses through the nesting.
	##
	## @param classes: The classes at this nesting level.
	Function is linkNestedClasses(Array of ClassInfo is classes){
		classes:each(action: local Function(ClassInfo is c){
			local String is qualifiedOuter: c:name;
			Conditional:if(check: { c:outerName != '' }, then: {
				qualifiedOuter: c:outerName . ':' . c:name;
			});
			c:members:each(action: local Function(Member is m){
				Conditional:if(check: { m:kind == MemberKind:CLASS }, then: {
					m:nestedClass:setOuter(name: qualifiedOuter);
					m:nestedClass:baseClasses:add(item: c:name);
					self:linkNestedClasses(classes: [m:nestedClass]);
				});
			});
		});
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
	## Parses one class declaration: `Class of Parent is Name` with optional
	## post-name generic parameters.
	##
	## @return: The class descriptor.
	Function of ClassInfo is parseClass(){
		Conditional:if(check: { self:peek():getValue() == self:names:legacyClassSpelling() }, then: {
			self:addError(tok: self:peek(), message: "The 'class' keyword is no longer valid; declare classes as 'Class of Parent is Name'.");
		});
		self:advance();

		# Pre-binder `of`: parent classes.
		local Array of String is baseClasses: [];
		Conditional:if(check: { self:checkKeyword(kw: Keyword:OF) }, then: {
			self:advance();
			local Boolean is keepGoing: true;
			while({ keepGoing && !self:checkPunct(p: Punctuation:BLOCK_OPEN) && !self:check(kind: TokenKind:EOF, value: '') }, {
				local Token is tok: self:advance();
				local String is base: tok:getValue();
				while({ self:checkPunct(p: Punctuation:DEFAULT) }, {
					self:advance();
					base: base . ':' . self:advance():getValue();
				});
				baseClasses:add(item: base);
				Conditional:if(check: { self:checkPunct(p: Punctuation:SEPARATOR) }, then: {
					self:advance();
				}, else: {
					keepGoing: false;
				});
			});
		});

		self:matchKeyword(kw: Keyword:IS);
		local Token is nameTok: self:advance();
		local String is name: nameTok:getValue();

		# Post-name `of`: generic type parameters.
		local Array of String is typeParams: [];
		Conditional:if(check: { self:checkKeyword(kw: Keyword:OF) }, then: {
			self:advance();
			local Token is tp1: self:advance();
			typeParams:add(item: tp1:getValue());
			Conditional:if(check: { self:checkKeyword(kw: Keyword:TO) }, then: {
				self:advance();
				local Token is tp2: self:advance();
				typeParams:add(item: tp2:getValue());
			});
		});

		self:matchPunct(p: Punctuation:BLOCK_OPEN);
		local Array of Member is members: [];
		while({ !self:checkPunct(p: Punctuation:BLOCK_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
			members:add(item: self:parseMember());
		});
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
		Conditional:if(check: { self:checkKeyword(kw: Keyword:OF) }, then: {
			self:advance();
			local Type is bt: self:parseType();
			backingType: bt:name;
		});
		self:matchKeyword(kw: Keyword:IS);
		local Token is nameTok: self:advance();
		local String is name: nameTok:getValue();
		self:matchPunct(p: Punctuation:BLOCK_OPEN);

		local Array of Member is members: [];
		local Int is count: 0;
		local Boolean is keepGoing: true;
		while({ keepGoing && !self:checkPunct(p: Punctuation:BLOCK_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
			local Token is vTok: self:advance();
			local String is vName: vTok:getValue();
			local Array of Parameter is vParams: [];
			Conditional:if(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
				self:advance();
				vParams: self:parseParams();
				self:matchPunct(p: Punctuation:GROUP_CLOSE);
			});
			local Expression is valExpr: Expression:init(kind: ExpressionKind:NUMBER);
			local Boolean is hasInit: false;
			Conditional:if(check: { self:checkPunct(p: Punctuation:TAG) }, then: {
				self:advance();
				valExpr: self:parseExpression();
				hasInit: true;
			}, else: {
				valExpr:str: '' . count;
				valExpr:num: count;
				hasInit: true;
			});
			count: count + 1;

			local Member is m: Member:init(kind: MemberKind:FIELD);
			m:modifiers: ['static', 'local'];
			m:memberType: Type:init(name: backingType);
			m:name: vName;
			m:params: vParams;
			m:initExpr: valExpr;
			m:hasInit: hasInit;
			members:add(item: m);

			Conditional:if(check: { self:checkPunct(p: Punctuation:SEPARATOR) }, then: {
				self:advance();
			}, else: {
				keepGoing: false;
			});
		});
		self:matchPunct(p: Punctuation:BLOCK_CLOSE);
		Conditional:if(check: { self:checkPunct(p: Punctuation:TERMINATOR) }, then: {
			self:advance();
		});

		# every enum desugars to the class model —
		# value enums to held variants + the synthesized contract methods;
		# tagged enums to nested subclasses with real payload fields (the
		# desugar branches on the variant shapes).
		local EnumDesugar is ds: EnumDesugar:init();
		local ClassInfo is dc: ClassInfo:init(name: name, baseClass: self:names:enumHeader(), members: members);
		local ClassInfo is desugared: ds:desugar(c: dc, backingType: backingType);
		members: desugared:members;

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
		while({ self:checkKeyword(kw: Keyword:LOCAL) || self:checkKeyword(kw: Keyword:CONTAINED) || self:checkKeyword(kw: Keyword:REPLACE) || self:checkKeyword(kw: Keyword:MERGE) || self:checkKeyword(kw: Keyword:HELD) }, {
			local Token is tok: self:advance();
			modifiers:add(item: tok:getValue());
		});

	Conditional:if(check: { self:atClassHeader() }, then: {
		local ClassInfo is nested: self:parseClass();
		local Member is m: Member:init(kind: MemberKind:CLASS);
		m:setLine(line: startLine);
		# the member identifies its class — the unnamed member
		# matched other unnamed members in the override and registry walks.
		m:name: nested:name;
		m:nestedClass: nested;
		return m;
	});

	Conditional:if(check: { self:atEnumHeader() }, then: {
		local ClassInfo is edef: self:parseEnum();
		local Member is m: Member:init(kind: MemberKind:CLASS);
		m:setLine(line: startLine);
		m:name: edef:name;
		m:nestedClass: edef;
		return m;
	});

		# Shorthand metadata property: `name: <expr>;` — the namespace/using
		# declaration form (an untyped field with an initializer).
		# The name may lex as a KEYWORD during transition generations (a
		# metadata name that shares an enum variant's tag); the ':' is what
		# actually discriminates the metadata form.
		Conditional:if(check: { (self:peek():getTokenKind() == TokenKind:IDENTIFIER || self:peek():getTokenKind() == TokenKind:KEYWORD) && self:peekAhead(offset: 1):getTokenKind() == TokenKind:SYMBOL && self:peekAhead(offset: 1):getValue() == ':' }, then: {
			local Token is nameTok: self:advance();
			self:advance();
			local Expression is initExpr: self:parseExpression();
			Conditional:if(check: { self:checkPunct(p: Punctuation:TERMINATOR) }, then: {
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
		Conditional:if(check: { self:peek():getTokenKind() == TokenKind:IDENTIFIER && self:peekAhead(offset: 1):getValue() == Punctuation:GROUP_OPEN:value() }, then: {
			local Token is nameTok: self:advance();
			local String is name: nameTok:getValue();
			self:advance();

			local Array of Parameter is params: self:parseParams();
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

		Conditional:if(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
			self:advance();
			local Array of Parameter is params: self:parseParams();
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
			# Interface-style declaration: a `;`-terminated signature with no
			# body — the sysinternal floor-binding form.
			Conditional:if(check: { self:checkPunct(p: Punctuation:TERMINATOR) }, then: {
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
		Conditional:if(check: { self:checkPunct(p: Punctuation:ASSIGN) }, then: {
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
			Conditional:if(check: { p:paramType:name == self:names:selfFieldMarker() }, then: {
				local Expression is lhs: Expression:init(kind: ExpressionKind:PATH);
				lhs:makePath(segments: [self:names:selfIdent(), p:name]);
				local Expression is rhs: Expression:init(kind: ExpressionKind:IDENT);
				rhs:makeIdent(name: p:name);
				local Statement is assignS: Statement:init(kind: StatementKind:ASSIGN);
				assignS:assign(target: lhs, value: rhs);
				body:add(item: assignS);
			});
		});
		while({ !self:checkPunct(p: Punctuation:BLOCK_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
			body:add(item: self:parseStatement());
		});
		self:matchPunct(p: Punctuation:BLOCK_CLOSE);
		return body;
	}

	## Parses one type reference: a base name with optional `of`/`to`
	## generic arguments, or a bracketed list literal type.
	##
	## @return: The type descriptor.
	Function of Type is parseType(){
		Conditional:if(check: { self:checkPunct(p: Punctuation:BRACKET_OPEN) }, then: {
			self:advance();
			local Type is elem: self:parseType();
			self:matchPunct(p: Punctuation:BRACKET_CLOSE);
			local Type is lnode: Type:init(name: self:names:listName());
			lnode:params: [elem];
			return lnode;
		});
		local Token is baseTok: self:advance();
		local String is typeName: baseTok:getValue();

		# the qualified nested-class reference —
		# `Outer:Inner` chains consume the glued colon segments into the
		# type name, so declaration positions can spell the full path.
		while({ self:checkPunct(p: Punctuation:ACCESSOR) && self:hasWhitespaceAfter(offset: 0) == false && self:peekAhead(offset: 1):getTokenKind() == TokenKind:IDENTIFIER }, {
			self:advance();
			local Token is segTok: self:advance();
			typeName: typeName . ':' . segTok:getValue();
		});

		Conditional:if(check: { self:checkKeyword(kw: Keyword:OF) }, then: {
			self:advance();
			local Array of Type is params: [];
			params:add(item: self:parseType());

			Conditional:if(check: { self:checkKeyword(kw: Keyword:TO) }, then: {
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
		Conditional:if(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
			return self:parseForwardStatement(startLine: startLine);
		});

		# Scoped callback statement: `as: call;` or `as (params): call;`.
		Conditional:if(check: { self:checkKeyword(kw: Keyword:AS) }, then: {
			return self:parseAsStatement(startLine: startLine);
		});

		Conditional:if(check: { self:atClassHeader() }, then: {
			local ClassInfo is cls: self:parseClass();
			local Statement is s: Statement:init(kind: StatementKind:CLASS);
			s:setLine(line: startLine);
			s:nestedClass: cls;
			return s;
		});

		Conditional:if(check: { self:atEnumHeader() }, then: {
			local ClassInfo is edef: self:parseEnum();
			local Statement is s: Statement:init(kind: StatementKind:CLASS);
			s:setLine(line: startLine);
			s:nestedClass: edef;
			return s;
		});

		Conditional:if(check: { self:atEnumHeader() }, then: {
			local ClassInfo is edef: self:parseEnum();
			local Statement is s: Statement:init(kind: StatementKind:CLASS);
			s:setLine(line: startLine);
			s:nestedClass: edef;
			return s;
		});


		Conditional:if(check: { self:checkKeyword(kw: Keyword:RETURN) }, then: {
			self:advance();
			Conditional:if(check: { self:checkKeyword(kw: Keyword:AS) }, then: {
				local Statement is asStmt: self:parseAsStatement(startLine: startLine);
				local Statement is s: Statement:init(kind: StatementKind:RETURN);
				s:setLine(line: startLine);
				s:returnExpr: asStmt:exprStmt;
				s:hasReturnExpr: true;
				return s;
			});
			local Expression is retExpr;
			local Boolean is hasExpr: false;
			Conditional:if(check: { !self:checkPunct(p: Punctuation:TERMINATOR) }, then: {
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

		Conditional:if(check: { self:checkKeyword(kw: Keyword:LOCAL) }, then: {
			self:advance();
			local Type is vType: self:parseType();
			self:matchKeyword(kw: Keyword:IS);
			local Token is nameTok: self:advance();
			local String is name: nameTok:getValue();

			local Expression is initExpr;
			local Boolean is hasInit: false;
			Conditional:if(check: { self:checkPunct(p: Punctuation:ASSIGN) }, then: {
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

		Conditional:if(check: { self:checkPunct(p: Punctuation:ASSIGN) }, then: {
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
		local Array of NamedArg is args: self:parseArgs();
		self:matchPunct(p: Punctuation:GROUP_CLOSE);
		Conditional:if(check: { self:checkPunct(p: Punctuation:TERMINATOR) }, then: {
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
		Conditional:if(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
			self:advance();
			hasParams: true;
			params: self:parseParams();
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
		});
		local Type is returnType: Type:init(name: self:names:voidName());
		Conditional:if(check: { self:checkKeyword(kw: Keyword:OF) }, then: {
			self:advance();
			returnType: self:parseType();
		});
		Conditional:if(check: { self:checkPunct(p: Punctuation:ACCESSOR) }, then: {
			self:advance();
		}, else: {
			Conditional:if(check: { !hasParams }, then: {
				self:matchPunct(p: Punctuation:ACCESSOR);
			});
		});
		local Expression is callExpr: self:parseExpression();
		self:matchPunct(p: Punctuation:TERMINATOR);

		local Array of Statement is closureBody: [];
		while({ !self:checkPunct(p: Punctuation:BLOCK_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
			closureBody:add(item: self:parseStatement());
		});

		local Expression is anonFn: Expression:init(kind: ExpressionKind:ANON_FN);
		anonFn:anonReturnType: returnType;
		anonFn:anonParams: params;
		anonFn:anonBody: closureBody;

		Conditional:if(check: { callExpr:kind != ExpressionKind:CALL }, then: {
			local Expression is c: Expression:init(kind: ExpressionKind:CALL);
			Conditional:if(check: { callExpr:kind == ExpressionKind:FIELD_ACCESS }, then: {
				c:methodTarget: callExpr:leftExpr;
				c:methodName: callExpr:str;
			}, else: {
				Conditional:if(check: { callExpr:kind == ExpressionKind:IDENT }, then: {
					local Expression is selfTarget: Expression:init(kind: ExpressionKind:IDENT);
					selfTarget:str: self:names:selfIdent();
					c:methodTarget: selfTarget;
					c:methodName: callExpr:str;
				}, else: {
					c:methodTarget: callExpr;
					c:methodName: '';
				});
			});
			c:methodArgs: [];
			callExpr: c;
		});

		callExpr:methodArgs:add(item: NamedArg:init(name: '', value: anonFn));
		# §as: the remainder is not an argument — it fills the
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
		return Conditional:match(on: level, when: [
			PrecedenceLevel:MULTIPLICATIVE: { self:foldBinary(ops: ['*', '/', '%'], next: PrecedenceLevel:NONE) },
			PrecedenceLevel:ADDITIVE: { self:foldBinary(ops: ['+', '-'], next: PrecedenceLevel:MULTIPLICATIVE) },
			PrecedenceLevel:SHIFT: { self:foldBinary(ops: ['<<', '>>'], next: PrecedenceLevel:ADDITIVE) },
			PrecedenceLevel:CONCAT: { self:foldBinary(ops: ['.'], next: PrecedenceLevel:SHIFT) },
			PrecedenceLevel:RELATIONAL: { self:foldBinary(ops: ['<', '<=', '>', '>='], next: PrecedenceLevel:CONCAT) },
			PrecedenceLevel:EQUALITY: { self:foldBinary(ops: ['==', '!=', 'is'], next: PrecedenceLevel:RELATIONAL) },
			PrecedenceLevel:BIT_AND: { self:foldBinary(ops: ['&'], next: PrecedenceLevel:EQUALITY) },
			PrecedenceLevel:BIT_XOR: { self:foldBinary(ops: ['^'], next: PrecedenceLevel:BIT_AND) },
			PrecedenceLevel:BIT_OR: { self:foldBinary(ops: ['|'], next: PrecedenceLevel:BIT_XOR) },
			PrecedenceLevel:LOGICAL_AND: { self:foldBinary(ops: ['&&'], next: PrecedenceLevel:BIT_OR) },
			PrecedenceLevel:LOGICAL_OR: { self:foldBinary(ops: ['||'], next: PrecedenceLevel:LOGICAL_AND) },
			else: { self:parseUnary() }
		]);
	}

	## Folds one level: parse the next-lower level for the left operand,
	## then run [BinaryFoldLoop] over the operator set.
	##
	## @param ops: This level's operator lexemes.
	## @param next: The next-lower level (NONE descends to unary).
	## @return: The folded expression.
	Function of Expression is foldBinary(Array of String is ops, PrecedenceLevel is next){
		local Expression is left: Expression:init(kind: ExpressionKind:UNKNOWN);
		Conditional:if(check: { next == PrecedenceLevel:NONE }, then: {
			left: self:parseUnary();
		}, else: {
			left: self:parseLevel(level: next);
		});
		while({ ops:indexOf(search: self:peek():getValue(), default: -1) >= 0 }, {
			local Token is opTok: self:advance();
			local String is op: opTok:getValue();
			Conditional:if(check: { op == Keyword:IS:value() }, then: {
				op: '==';
			});
			local Expression is right: Expression:init(kind: ExpressionKind:UNKNOWN);
			Conditional:if(check: { next == PrecedenceLevel:NONE }, then: {
				right: self:parseUnary();
			}, else: {
				right: self:parseLevel(level: next);
			});
			local Expression is binExpr: Expression:init(kind: ExpressionKind:BINARY);
			binExpr:str: op;
			binExpr:leftExpr: left;
			binExpr:rightExpr: right;
			left: binExpr;
		});
		return left;
	}

	## Parses unary operators (~, -, !) or descends to casts.
	##
	## @return: The expression node.
	Function of Expression is parseUnary(){
		local String is op: '';
		Conditional:if(check: { self:checkSymbol(value: '++') }, then: {
			op: '++';
		}, else: {
			Conditional:if(check: { self:checkSymbol(value: '--') }, then: {
				op: '--';
			}, else: {
				Conditional:if(check: { self:checkSymbol(value: '~') }, then: {
					op: '~';
				}, else: {
					Conditional:if(check: { self:checkSymbol(value: '-') }, then: {
						op: '-';
					}, else: {
						Conditional:if(check: { self:checkSymbol(value: '!') }, then: {
							op: '!';
						}, else: {
							return self:parseAs();
						});
					});
				});
			});
		});
		self:advance();
		local Expression is expr: self:parseUnary();
		local Expression is u: Expression:init(kind: ExpressionKind:UNARY);
		u:str: op;
		u:unaryExpr: expr;
		return u;
	}

	## Parses the instance-import form `as ClassName(args)` — a using-entry
	## terminator (§2.1). Arguments must be direct literal
	## values (E1); parentheses are required so the form can
	## never be confused with the postfix cast.
	##
	## @return: The USING_AS expression node.
	Function of Expression is parseUsingAs(){
		self:advance();
		local Token is clsTok: self:peek();
		Conditional:if(check: { clsTok:getTokenKind() != TokenKind:IDENTIFIER }, then: {
			self:addError(tok: clsTok, message: "'as' in a using entry must be followed by a class name.");
			return Expression:init(kind: ExpressionKind:UNKNOWN);
		});
		self:advance();
		local Expression is e: Expression:init(kind: ExpressionKind:USING_AS);
		e:str: clsTok:getValue();
		Conditional:if(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
			self:advance();
			Conditional:if(check: { !self:checkPunct(p: Punctuation:GROUP_CLOSE) }, then: {
				local Array of NamedArg is args: self:parseArgs();
				e:methodArgs: args;
				args:each(action: local Function(NamedArg is arg){
					local ExpressionKind is ak: arg:value:kind;
					Conditional:if(check: { ak != ExpressionKind:STRING && ak != ExpressionKind:NUMBER && ak != ExpressionKind:FLOAT && ak != ExpressionKind:BOOL }, then: {
						self:addError(tok: clsTok, message: 'Instance-import arguments must be direct literal values (E1).');
					});
				});
			});
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
		}, else: {
			self:addError(tok: clsTok, message: "Instance import requires parentheses: 'as " . e:str . "()'.");
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
		Conditional:if(check: { self:checkKeyword(kw: Keyword:AS) }, then: {
			self:advance();
			local Token is targetTok: self:advance();
			local Array of Expression is args: [];
			Conditional:if(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
				self:advance();
				Conditional:if(check: { !self:checkPunct(p: Punctuation:GROUP_CLOSE) }, then: {
					args:add(item: self:parseExpression());
				});
				self:matchPunct(p: Punctuation:GROUP_CLOSE);
			});
			Conditional:if(check: { self:checkKeyword(kw: Keyword:AS) }, then: {
				self:addError(tok: self:peek(), message: "Chained 'as' casts are not supported; cast in separate steps.");
			});
			local Expression is c: Expression:init(kind: ExpressionKind:CAST);
			c:makeCast(inner: left, target: targetTok:getValue(), args: args);
			return c;
		});
		return left;
	}

	## Returns whether the next token starts a postfix operator or access.
	Function of Boolean is atPostfix(){
		Conditional:if(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) || self:checkPunct(p: Punctuation:BRACKET_OPEN) || self:checkSymbol(value: '++') || self:checkSymbol(value: '--') }, then: {
			return true;
		});
		Conditional:if(check: { self:checkPunct(p: Punctuation:ACCESSOR) }, then: {
			# Whitespace before ':' means assignment context, not a path.
			Conditional:if(check: { self:hasWhitespaceAfter(offset: 0) }, then: {
				return false;
			});
			local Token is nextTok: self:peekAhead(offset: 1);
			return nextTok:getTokenKind() == TokenKind:IDENTIFIER || nextTok:getTokenKind() == TokenKind:KEYWORD || nextTok:getValue() == self:names:wildcard();
		});
		return false;
	}

	## Parses postfix trailers (calls, indexes, colon-paths) after a
	## primary expression.
	##
	## @return: The expression node.
	Function of Expression is parsePostfix(){
		local Expression is currentExpr: self:parsePrimary();
		while({ self:atPostfix() }, {
			Conditional:if(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
				self:advance();
				local Array of NamedArg is args: self:parseArgs();
				self:matchPunct(p: Punctuation:GROUP_CLOSE);

				local Expression is callExpr: Expression:init(kind: ExpressionKind:CALL);
				Conditional:if(check: { currentExpr:kind == ExpressionKind:IDENT }, then: {
					Conditional:if(check: { currentExpr:str == 'Loops' }, then: {
						callExpr:methodTarget: currentExpr;
						callExpr:methodName: 'loop';
					}, else: {
						local Expression is selfTarget: Expression:init(kind: ExpressionKind:IDENT);
						selfTarget:str: self:names:selfIdent();
						callExpr:methodTarget: selfTarget;
						callExpr:methodName: currentExpr:str;
					});
				}, else: {
					callExpr:methodTarget: currentExpr;
					callExpr:methodName: '';
				});
				callExpr:methodArgs: args;
				currentExpr: callExpr;
			}, else: {
				Conditional:if(check: { self:checkPunct(p: Punctuation:BRACKET_OPEN) }, then: {
					self:advance();
					local Expression is idxExpr: self:parseExpression();
					self:matchPunct(p: Punctuation:BRACKET_CLOSE);

					local Expression is indexNode: Expression:init(kind: ExpressionKind:INDEX);
					indexNode:leftExpr: currentExpr;
					indexNode:rightExpr: idxExpr;
					currentExpr: indexNode;
				}, else: {
					Conditional:if(check: { self:checkSymbol(value: '++') }, then: {
						self:advance();
						local Expression is u: Expression:init(kind: ExpressionKind:UNARY);
						u:str: 'post++';
						u:unaryExpr: currentExpr;
						currentExpr: u;
					}, else: {
						Conditional:if(check: { self:checkSymbol(value: '--') }, then: {
							self:advance();
							local Expression is u: Expression:init(kind: ExpressionKind:UNARY);
							u:str: 'post--';
							u:unaryExpr: currentExpr;
							currentExpr: u;
						}, else: {
							Conditional:if(check: { self:checkPunct(p: Punctuation:ACCESSOR) }, then: {
								self:advance();
								local Token is mTok: self:advance();
								local String is method: mTok:getValue();

								Conditional:if(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
									self:advance();
									local Array of NamedArg is args: self:parseArgs();
									self:matchPunct(p: Punctuation:GROUP_CLOSE);

									local Expression is callExpr: Expression:init(kind: ExpressionKind:CALL);
									callExpr:methodTarget: currentExpr;
									callExpr:methodName: method;
									callExpr:methodArgs: args;
									currentExpr: callExpr;
								}, else: {
									Conditional:if(check: { currentExpr:kind != ExpressionKind:PATH && currentExpr:kind != ExpressionKind:IDENT }, then: {
										local Expression is fa: Expression:init(kind: ExpressionKind:FIELD_ACCESS);
										fa:leftExpr: currentExpr;
										fa:str: method;
										currentExpr: fa;
									}, else: {
										local Array of String is segs: [];
										Conditional:if(check: { currentExpr:kind == ExpressionKind:PATH }, then: {
											currentExpr:pathSegments:each(action: local Function(String is s){
												segs:add(item: s);
											});
										}, else: {
											Conditional:if(check: { currentExpr:kind == ExpressionKind:IDENT }, then: {
												segs:add(item: currentExpr:str);
											});
										});
										segs:add(item: method);
										local Expression is pathExpr: Expression:init(kind: ExpressionKind:PATH);
										pathExpr:pathSegments: segs;
										pathExpr:str: currentExpr:str . ':' . method;
										currentExpr: pathExpr;
									});
								});
							});
						});
					});
				});
			});
		});
		return currentExpr;
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
		Conditional:if(check: { self:checkKeyword(kw: Keyword:LOCAL) && self:peekAhead(offset: 1):getValue() == self:names:fnName() }, then: {
			isAnonFn: true;
		});
		Conditional:if(check: { self:peek():getValue() == self:names:fnName() && (self:peekAhead(offset: 1):getValue() == Punctuation:GROUP_OPEN:value() || self:peekAhead(offset: 1):getValue() == Keyword:OF:value()) }, then: {
			isAnonFn: true;
		});

		Conditional:if(check: { isAnonFn }, then: {
			Conditional:if(check: { self:checkKeyword(kw: Keyword:LOCAL) }, then: {
				self:advance();
			});
			self:advance();
			local Type is returnType: Type:init(name: self:names:voidName());
			Conditional:if(check: { self:checkKeyword(kw: Keyword:OF) }, then: {
				self:advance();
				returnType: self:parseType();
			});
			self:matchPunct(p: Punctuation:GROUP_OPEN);
			local Array of Parameter is params: self:parseParams();
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
			local Array of Statement is body: self:parseMethodBody(params: params);

			local Expression is e: Expression:init(kind: ExpressionKind:ANON_FN);
			e:anonReturnType: returnType;
			e:anonParams: params;
			e:anonBody: body;
			return e;
		});


		local Token is tok: self:peek();

		return Conditional:match(on: tok:getTokenKind(), when: [
			TokenKind:STRING: {
				self:advance();
				local Expression is e: Expression:init(kind: ExpressionKind:STRING);
				e:str: tok:getValue();
				e
			},
			TokenKind:RAWSTRING: {
				self:advance();
				local Expression is e: Expression:init(kind: ExpressionKind:STRING);
				e:str: tok:getValue();
				e
			},
			TokenKind:TEMPLATESTRING: {
				self:advance();
				self:expandFancyString(raw: tok:getValue(), originTok: tok, depth: self:templateDepth)
			},
			TokenKind:INT: {
				self:advance();
				local Expression is e: Expression:init(kind: ExpressionKind:NUMBER);
				e:str: tok:getValue();
				e
			},
			TokenKind:FLOAT: {
				self:advance();
				local Expression is e: Expression:init(kind: ExpressionKind:FLOAT);
				e:str: tok:getValue();
				e
			},
			TokenKind:BOOL: {
				self:advance();
				local Expression is e: Expression:init(kind: ExpressionKind:BOOL);
				e:num: Conditional:if(check: { tok:getValue() == self:names:boolTrue() }, then: { 1 }, else: { 0 });
				e:str: tok:getValue();
				e
			},
			TokenKind:IDENTIFIER: {
				self:advance();
				local Expression is e: Expression:init(kind: ExpressionKind:IDENT);
				e:str: tok:getValue();
				e
			},
			TokenKind:KEYWORD: {
				# Expression-initial `as` is the instance-import form
				# `as ClassName()` (§2.1); `as` never begins any
				# other expression (casts are postfix, scoped regions are
				# statement-initial).
				Conditional:if(check: { self:checkKeyword(kw: Keyword:AS) }, then: {
					return self:parseUsingAs();
				});
				self:addError(tok: tok, message: "Unexpected token '{{tok:getValue()}}' in expression");
				self:advance();
				Expression:init(kind: ExpressionKind:UNKNOWN)
			},
			else: {
				Conditional:if(check: { self:checkPunct(p: Punctuation:GROUP_OPEN) }, then: {
					self:advance();
					local Expression is inner: self:parseExpression();
					self:matchPunct(p: Punctuation:GROUP_CLOSE);
					return inner;
				});

				Conditional:if(check: { self:checkPunct(p: Punctuation:BRACKET_OPEN) }, then: {
					return self:parseArrayOrMap();
				});

				Conditional:if(check: { self:checkPunct(p: Punctuation:BLOCK_OPEN) }, then: {
					return self:parseFunctionBlock();
				});

				self:addError(tok: tok, message: "Unexpected token '{{tok:getValue()}}' in expression");
				self:advance();
				Expression:init(kind: ExpressionKind:UNKNOWN)
			}
		]);
	}

	## True when the current bracketed sequence begins a typed declaration
	## list `[Type is name: init, ...]` rather than a value array.
	## The scan is depth-aware: tokens inside balanced `(`/`[`/`{` groups
	## are skipped, so the `is` of a nested closure body
	## (`[key: { local X is v: ...; v }]`) never misfires the detector —
	## only a depth-0 `is` (the decl-list form) or a depth-0 terminator
	## (`]`, `,`, `;`) decides.
	##
	## @return: true when declaration list.
	Function of Boolean is isDeclListStart(){
		local Int is offset: 1;
		local Int is depth: 0;
		local Boolean is running: true;
		local Boolean is foundIs: false;
		while({ running }, {
			local Token is t: self:peekAhead(offset: offset);
			local String is v: t:getValue();
			Conditional:if(check: { t:getTokenKind() == TokenKind:EOF }, then: {
				running: false;
			}, else: {
				Conditional:if(check: { depth == 0 && (v == ']' || v == ',' || v == ';') }, then: {
					running: false;
				}, else: {
					Conditional:if(check: { v == '(' || v == '[' || v == '{' }, then: {
						depth: depth + 1;
					}, else: {
						Conditional:if(check: { v == ')' || v == ']' || v == '}' }, then: {
							depth: depth - 1;
						}, else: {
							Conditional:if(check: { depth == 0 && t:getTokenKind() == TokenKind:KEYWORD && v == Keyword:IS:value() }, then: {
								foundIs: true;
								running: false;
							});
						});
					});
					offset: offset + 1;
				});
			});
		});
		return foundIs;
	}

	## Parses a scoped variable declaration list `[Type is name: init, ...]`.
	##
	## @return: ARRAY expression carrying parsed parameters in anonParams.
	Function of Expression is parseDeclList(){
		self:matchPunct(p: Punctuation:BRACKET_OPEN);
		local Array of Parameter is params: [];
		local Boolean is keepGoing: true;
		while({ keepGoing && !self:checkPunct(p: Punctuation:BRACKET_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
			local Type is pType: self:parseType();
			self:matchKeyword(kw: Keyword:IS);
			local Token is nameTok: self:advance();
			local Parameter is p: Parameter:init(name: nameTok:getValue(), paramType: pType);
			Conditional:if(check: { self:checkPunct(p: Punctuation:ASSIGN) }, then: {
				self:advance();
				p:setDefault(expr: self:parseExpression());
			});
			params:add(item: p);
			Conditional:if(check: { self:checkPunct(p: Punctuation:SEPARATOR) }, then: {
				self:advance();
			}, else: {
				keepGoing: false;
			});
		});
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

		while({ !self:checkPunct(p: Punctuation:BLOCK_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
			Conditional:if(check: { !self:checkKeyword(kw: Keyword:RETURN) && !self:checkKeyword(kw: Keyword:LOCAL) && !self:checkKeyword(kw: Keyword:AS) }, then: {
				local Expression is expr: self:parseExpression();
				Conditional:if(check: { self:checkPunct(p: Punctuation:ASSIGN) }, then: {
					self:advance();
					local Expression is val: self:parseExpression();
					self:matchPunct(p: Punctuation:TERMINATOR);
					local Statement is s: Statement:init(kind: StatementKind:ASSIGN);
					s:assignTarget: expr;
					s:assignValue: val;
					body:add(item: s);
				}, else: {
					Conditional:if(check: { self:checkPunct(p: Punctuation:BLOCK_CLOSE) }, then: {
						local Statement is retS: Statement:init(kind: StatementKind:RETURN);
						retS:returnExpr: expr;
						retS:hasReturnExpr: true;
						body:add(item: retS);
					}, else: {
						self:matchPunct(p: Punctuation:TERMINATOR);
						local Statement is exprS: Statement:init(kind: StatementKind:EXPR);
						exprS:exprStmt: expr;
						body:add(item: exprS);
					});
				});
			}, else: {
				body:add(item: self:parseStatement());
			});
		});
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
		Conditional:if(check: { self:isDeclListStart() }, then: {
			return self:parseDeclList();
		});
		self:advance();
		Conditional:if(check: { self:checkPunct(p: Punctuation:BRACKET_CLOSE) }, then: {
			self:advance();
			local Expression is e: Expression:init(kind: ExpressionKind:ARRAY);
			e:arrayItems: [];
			return e;
		});
		Conditional:if(check: { self:checkPunct(p: Punctuation:PAIR) }, then: {
			self:advance();
			self:matchPunct(p: Punctuation:BRACKET_CLOSE);
			local Expression is e: Expression:init(kind: ExpressionKind:MAP);
			e:makeMap(keys: [], values: []);
			return e;
		});
		local Expression is firstItem: self:parseExpression();
		Conditional:if(check: { self:checkPunct(p: Punctuation:PAIR) }, then: {
			self:advance();
			local Expression is firstVal: self:parseExpression();
			local Array of Expression is mKeys: [firstItem];
			local Array of Expression is mVals: [firstVal];
			Conditional:if(check: { self:checkPunct(p: Punctuation:SEPARATOR) }, then: {
				self:advance();
				local Boolean is keepGoing: true;
				while({ keepGoing && !self:checkPunct(p: Punctuation:BRACKET_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
					local Expression is k: self:parseExpression();
					self:matchPunct(p: Punctuation:PAIR);
					local Expression is v: self:parseExpression();
					mKeys:add(item: k);
					mVals:add(item: v);
					Conditional:if(check: { self:checkPunct(p: Punctuation:SEPARATOR) }, then: {
						self:advance();
					}, else: {
						keepGoing: false;
					});
				});
			});
			self:matchPunct(p: Punctuation:BRACKET_CLOSE);
			local Expression is e: Expression:init(kind: ExpressionKind:MAP);
			e:makeMap(keys: mKeys, values: mVals);
			return e;
		});
		local Array of Expression is items: [firstItem];
		Conditional:if(check: { self:checkPunct(p: Punctuation:SEPARATOR) }, then: {
			self:advance();
			local Boolean is keepGoing: true;
			while({ keepGoing && !self:checkPunct(p: Punctuation:BRACKET_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
				items:add(item: self:parseExpression());
				Conditional:if(check: { self:checkPunct(p: Punctuation:SEPARATOR) }, then: {
					self:advance();
				}, else: {
					keepGoing: false;
				});
			});
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
		Conditional:if(check: { depth > 0 }, then: {
			local String is dRes: '';
			local Int is dPos: 0;
			local TemplateEscapes is esc: TemplateEscapes:init();
			while({ dPos < raw:length() }, {
				local String is ch: raw:charAt(index: dPos, default: '');
				dPos: dPos + 1;
				Conditional:if(check: { ch == "\\" }, then: {
					Conditional:if(check: { dPos < raw:length() }, then: {
						local String is nextCh: raw:charAt(index: dPos, default: '');
						dPos: dPos + 1;
						dRes: dRes . esc:expand(escaped: nextCh);
					}, else: {
						dRes: dRes . "\\";
					});
				}, else: {
					dRes: dRes . ch;
				});
			});
			plainE:str: dRes;
			return plainE;
		});

		local Int is sPos: 0;
		local Boolean is inHole: false;
		local String is lit: '';
		local Array of String is lits: [];
		local String is hole: '';
		local Array of String is holes: [];
		local String is quoteCh: '';
		local Int is braceDepth: 0;
		local TemplateEscapes is esc: TemplateEscapes:init();

		while({ sPos < raw:length() }, {
			local String is ch: raw:charAt(index: sPos, default: '');
			Conditional:if(check: { !inHole }, then: {
				Conditional:if(check: { ch == "{" && sPos + 1 < raw:length() && raw:charAt(index: sPos + 1, default: '') == "{" }, then: {
					lits:add(item: lit);
					lit: '';
					inHole: true;
					hole: '';
					quoteCh: '';
					braceDepth: 0;
					sPos: sPos + 2;
				}, else: {
					Conditional:if(check: { ch == "\\" }, then: {
						Conditional:if(check: { sPos + 1 < raw:length() }, then: {
							local String is nextCh: raw:charAt(index: sPos + 1, default: '');
							lit: lit . esc:expand(escaped: nextCh);
							sPos: sPos + 2;
						}, else: {
							lit: lit . "\\";
							sPos: sPos + 1;
						});
					}, else: {
						lit: lit . ch;
						sPos: sPos + 1;
					});
				});
			}, else: {
				Conditional:if(check: { quoteCh != '' }, then: {
					Conditional:if(check: { ch == "\\" }, then: {
						hole: hole . ch;
						sPos: sPos + 1;
						Conditional:if(check: { sPos < raw:length() }, then: {
							hole: hole . raw:charAt(index: sPos, default: '');
							sPos: sPos + 1;
						});
					}, else: {
						Conditional:if(check: { ch == quoteCh }, then: {
							quoteCh: '';
						});
						hole: hole . ch;
						sPos: sPos + 1;
					});
				}, else: {
					Conditional:if(check: { ch == '\'' || ch == '"' }, then: {
						quoteCh: ch;
						hole: hole . ch;
						sPos: sPos + 1;
					}, else: {
						Conditional:if(check: { ch == "{" }, then: {
							braceDepth: braceDepth + 1;
							hole: hole . ch;
							sPos: sPos + 1;
						}, else: {
							Conditional:if(check: { ch == "}" }, then: {
								Conditional:if(check: { braceDepth > 0 }, then: {
									braceDepth: braceDepth - 1;
									hole: hole . ch;
									sPos: sPos + 1;
								}, else: {
									Conditional:if(check: { sPos + 1 < raw:length() && raw:charAt(index: sPos + 1, default: '') == "}" }, then: {
										holes:add(item: hole);
										hole: '';
										inHole: false;
										sPos: sPos + 2;
									}, else: {
										hole: hole . ch;
										sPos: sPos + 1;
									});
								});
							}, else: {
								hole: hole . ch;
								sPos: sPos + 1;
							});
						});
					});
				});
			});
		});

		lits:add(item: lit);
		Conditional:if(check: { inHole }, then: {
			self:addError(tok: originTok, message: 'Unterminated template hole (missing closing }})');
			plainE:str: '';
			return plainE;
		});
		local Expression is acc: Expression:init(kind: ExpressionKind:STRING);
		acc:str: lits:get(index: 0);
		Conditional:if(check: { holes:length() == 0 }, then: {
			return acc;
		});

		local Int is k: 0;
		while({ k < holes:length() }, {
			local Expression is holeE: self:parseTemplateExpression(text: holes:get(index: k));
			local Expression is withHole: Expression:init(kind: ExpressionKind:BINARY);
			withHole:str: '.';
			withHole:leftExpr: acc;
			withHole:rightExpr: holeE;
			local Expression is litE: Expression:init(kind: ExpressionKind:STRING);
			litE:str: lits:get(index: k + 1);
			local Expression is withLit: Expression:init(kind: ExpressionKind:BINARY);
			withLit:str: '.';
			withLit:leftExpr: withHole;
			withLit:rightExpr: litE;
			acc: withLit;
			k: k + 1;
		});
		return acc;
	}

	## Parses one template hole's text as a full Spec expression using a
	## sub-lexer and sub-parser; the hole text must be exactly one
	## expression.
	##
	## @param text: The hole's raw text.
	## @return: The hole's expression.
	Function of Expression is parseTemplateExpression(String is text){
		local Expression is emptyE: Expression:init(kind: ExpressionKind:STRING);
		Conditional:if(check: { text:trim():length() == 0 }, then: {
			self:addError(tok: self:peek(), message: 'Empty expression in string template');
			return emptyE;
		});
		local Lexer is subLexer: Lexer:init(source: text);
		local Array of Token is subTokens: subLexer:tokenize();
		Conditional:if(check: { subLexer:hasErrors() }, then: {
			self:addError(tok: self:peek(), message: 'Invalid expression in string template');
			return emptyE;
		});
		local Parser is subParser: Parser:init(tokens: subTokens);
		subParser:setTemplateDepth(depth: 1);
		local Expression is e: subParser:parseExpression();
		Conditional:if(check: { subParser:hasErrors() || subParser:peek():getTokenKind() != TokenKind:EOF }, then: {
			self:addError(tok: self:peek(), message: 'Invalid expression in string template');
			return emptyE;
		});
		return e;
	}
}
