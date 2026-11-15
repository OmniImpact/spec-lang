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
		['base', 'compiler', 'ast', CallData],
		['base', 'compiler', 'ast', Statement],
		['base', 'compiler', 'ast', Parameter],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', NamedArg],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', Error],
		['base', 'compiler', ErrorText],
		['base', 'sys', SourceLocation],
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
	local ErrorText is errText: ErrorText:init();

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
		local String is prefix: if({ self:sourceFile != '' }, { self:sourceFile . ':' }, { 'Line ' });
		local SourceLocation is loc: SourceLocation:init(file: self:sourceFile, line: tok:getLine(), col: tok:getCol(), length: tok:getValue():length());
		local Error is e: Error:init(message: "  [SyntaxError] [{{prefix}}{{tok:getLine()}}:{{tok:getCol()}}] {{message}}", location: loc);
		e:addTraceAt(className: Reflection:class(), methodName: Reflection:method(), line: tok:getLine(), col: tok:getCol());
		self:errors:add(item: e);
	}

	## Returns the current token without consuming it.
	##
	## @return: The current token; EOF past the end.
	Function of Token is peek(){
		if({ self:streaming }, {
			return self:peekAhead(offset: 0);
		});
		if({ self:pos < self:length }, {
			return self:tokens:get(index: self:pos);
		});
		return Token:init(kind: TokenKind:EOF, value: '', line: 0, col: 0);
	}

	## Returns the token [offset] positions ahead.
	##
	## @param offset: Lookahead distance.
	## @return: The token; EOF past the end.
	Function of Token is peekAhead(Int is offset){
		if({ self:streaming }, {
			local Boolean is pulling: true;
			while({ pulling && self:lookahead:length() <= offset }, {
				local Token is tok: self:lexer:nextToken();
				self:lookahead:add(item: tok);
				if({ tok:getTokenKind() == TokenKind:EOF }, {
					pulling: false;
				});
			});
			if({ offset < self:lookahead:length() }, {
				return self:lookahead:get(index: offset);
			});
			return Token:init(kind: TokenKind:EOF, value: '', line: 0, col: 0);
		});
		local Int is idx: self:pos + offset;
		if({ idx < self:length }, {
			return self:tokens:get(index: idx);
		});
		return Token:init(kind: TokenKind:EOF, value: '', line: 0, col: 0);
	}

	## Consumes and returns the current token.
	##
	## @return: The consumed token.
	Function of Token is advance(){
		if({ self:streaming }, {
			local Token is tok: self:peekAhead(offset: 0);
			self:lookahead:removeAt(index: 0, default: tok);
			return tok;
		});
		local Token is tok: self:peek();
		if({ self:pos < self:length }, {
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
		if({ nxt:getTokenKind() == TokenKind:EOF }, {
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
		if({ tok:getTokenKind() != kind }, {
			return false;
		});
		if({ value != '' && tok:getValue() != value }, {
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
		if({ self:check(kind: TokenKind:SYMBOL, value: value) }, {
			self:advance();
			return true;
		});
		local Token is tok: self:peek();
		self:addError(tok: tok, message: self:errText:errExpectedFound(expected: value, found: tok:getValue()));
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
		if({ self:check(kind: TokenKind:SYMBOL, value: p:value()) }, {
			self:advance();
			return true;
		});
		local Token is tok: self:peek();
		self:addError(tok: tok, message: self:errText:errExpectedFound(expected: p:value(), found: tok:getValue()));
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
		if({ self:check(kind: TokenKind:KEYWORD, value: kw:value()) }, {
			self:advance();
			return true;
		});
		local Token is tok: self:peek();
		self:addError(tok: tok, message: self:errText:errExpectedFound(expected: kw:value(), found: tok:getValue()));
		return false;
	}

	## Consumes call arguments: positional or `name: value` pairs.
	Function of Array of NamedArg is parseArgs(){
		local Array of NamedArg is args: [];
		local Boolean is keepGoing: true;
		while({ keepGoing && !self:checkPunct(p: Punctuation:GROUP_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
			local String is argName: '';
			local Token is tok0: self:peekAhead(offset: 0);
			if({ tok0:getTokenKind() == TokenKind:IDENTIFIER && self:peekAhead(offset: 1):getValue() == Punctuation:NAMED_ARG:value() }, {
				local String is nameVal: tok0:getValue();
				local Boolean is isUpper: self:chars:isUpper(ch: nameVal:charAt(index: 0, default: ''));
				if({ !isUpper }, {
					local Token is nextTok: self:peekAhead(offset: 2);
					local Boolean is isNamed: false;
					if({ nextTok:getTokenKind() != TokenKind:IDENTIFIER }, {
						isNamed: true;
					}, {
						isNamed: self:hasWhitespaceAfter(offset: 1);
					});
					if({ isNamed }, {
						local Token is aTok: self:advance();
						argName: aTok:getValue();
						self:advance();
					});
				});
			});
			local Expression is val: self:parseExpression();
			args:add(item: NamedArg:init(name: argName, value: val));
			if({ self:checkPunct(p: Punctuation:SEPARATOR) }, {
				self:advance();
			}, {
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
			if({ self:peek():getValue() == self:names:selfIdent() && self:peekAhead(offset: 1):getValue() == ':' }, {
				self:advance();
				self:advance();
				local Token is fTok: self:advance();
				local Parameter is param: Parameter:init(name: fTok:getValue(), paramType: Type:init(name: self:names:selfFieldMarker()));
				if({ self:checkPunct(p: Punctuation:DEFAULT) }, {
					self:advance();
					param:setDefault(expr: self:parseExpression());
				});
				params:add(item: param);
				if({ self:checkPunct(p: Punctuation:SEPARATOR) }, {
					self:advance();
				}, {
					keepGoing: false;
				});
			}, {
				# Shorthand: a bare identifier is an Any-typed parameter.
				if({ self:peekAhead(offset: 1):getValue() == Punctuation:SEPARATOR:value() || self:peekAhead(offset: 1):getValue() == Punctuation:GROUP_CLOSE:value() }, {
					local Token is pTok: self:advance();
					params:add(item: Parameter:init(name: pTok:getValue(), paramType: Type:init(name: self:names:anyName())));
					if({ self:checkPunct(p: Punctuation:SEPARATOR) }, {
						self:advance();
					}, {
						keepGoing: false;
					});
				}, {
					local Type is pType: self:parseType();
					self:matchKeyword(kw: Keyword:IS);
					local Token is pTok: self:advance();
					local Parameter is param: Parameter:init(name: pTok:getValue(), paramType: pType);
					if({ self:checkPunct(p: Punctuation:DEFAULT) }, {
						self:advance();
						param:setDefault(expr: self:parseExpression());
					});
					params:add(item: param);
					if({ self:checkPunct(p: Punctuation:SEPARATOR) }, {
						self:advance();
					}, {
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
			if({ self:atEnumHeader() }, {
				classes:add(item: self:parseEnum());
			}, {
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
			if({ c:outerName != '' }, {
				qualifiedOuter: c:outerName . ':' . c:name;
			});
			c:members:each(action: local Function(Member is m){
				if({ m:kind == MemberKind:CLASS }, {
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
		if({ self:peek():getValue() == self:names:legacyClassSpelling() }, {
			self:addError(tok: self:peek(), message: self:errText:errObsoleteClassKeyword());
		});
		self:advance();

		# Pre-binder `of`: parent classes.
		local Array of String is baseClasses: [];
		if({ self:checkKeyword(kw: Keyword:OF) }, {
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
				if({ self:checkPunct(p: Punctuation:SEPARATOR) }, {
					self:advance();
				}, {
					keepGoing: false;
				});
			});
		});

		self:matchKeyword(kw: Keyword:IS);
		local Token is nameTok: self:advance();
		local String is name: nameTok:getValue();

		# Post-name `of`: generic type parameters.
		local Array of String is typeParams: [];
		if({ self:checkKeyword(kw: Keyword:OF) }, {
			self:advance();
			local Token is tp1: self:advance();
			typeParams:add(item: tp1:getValue());
			if({ self:checkKeyword(kw: Keyword:TO) }, {
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

	## True when the cursor sits on a class-body member inside an enum
	## (field, method, nested class/enum, or shorthand metadata) rather than
	## an enum variant.
	##
	## @return: true when the next tokens begin an enum member declaration.
	Function of Boolean is atEnumMember(){
		local String is firstVal: self:peek():getValue();
		if({ firstVal == 'namespace' || firstVal == 'using' || firstVal == 'castable' }, {
			return false;
		});
		if({ self:checkKeyword(kw: Keyword:LOCAL) || self:checkKeyword(kw: Keyword:CONTAINED) || self:checkKeyword(kw: Keyword:REPLACE) || self:checkKeyword(kw: Keyword:MERGE) || self:checkKeyword(kw: Keyword:HELD) }, {
			return true;
		});
		if({ self:atClassHeader() || self:atEnumHeader() }, {
			return true;
		});
		if({ self:peek():getValue() == self:names:fnName() }, {
			return true;
		});
		if({ self:checkPunct(p: Punctuation:BRACKET_OPEN) }, {
			return true;
		});

		local Boolean is isMember: false;

		# If next token is followed by '(':
		# Could be untyped method name(...) { or variant Name(...).
		if({ self:peekAhead(offset: 1):getValue() == '(' }, {
			local Int is depth: 1;
			local Int is i: 2;
			local Boolean is searching: true;
			while({ searching }, {
				local Token is t: self:peekAhead(offset: i);
				local String is tv: t:getValue();
				if({ t:getTokenKind() == TokenKind:EOF || tv == '}' }, {
					searching: false;
				}, {
					if({ tv == '(' }, {
						depth: depth + 1;
					});
					if({ tv == ')' }, {
						depth: depth - 1;
						if({ depth == 0 }, {
							searching: false;
							local Token is after: self:peekAhead(offset: i + 1);
							if({ after:getValue() == '{' }, {
								isMember: true;
							});
						});
					});
				});
				i: i + 1;
			});
			return isMember;
		});

		# For other tokens, scan ahead up to the statement/variant boundary.
		# A typed field/method has 'is' before ';', '{', or ','.
		# Shorthand metadata or a statement has ';' before ','.
		local Int is j: 1;
		local Int is bDepth: 0;
		local Int is pDepth: 0;
		local Boolean is scanning: true;
		while({ scanning }, {
			local Token is tok: self:peekAhead(offset: j);
			local String is val: tok:getValue();
			if({ tok:getTokenKind() == TokenKind:EOF }, {
				scanning: false;
			}, {
				if({ bDepth == 0 && pDepth == 0 && val == '}' }, {
					scanning: false;
				}, {
					if({ val == '[' }, {
						bDepth: bDepth + 1;
					});
					if({ val == ']' && bDepth > 0 }, {
						bDepth: bDepth - 1;
					});
					if({ val == '(' }, {
						pDepth: pDepth + 1;
					});
					if({ val == ')' && pDepth > 0 }, {
						pDepth: pDepth - 1;
					});
					if({ bDepth == 0 && pDepth == 0 }, {
						if({ tok:getTokenKind() == TokenKind:KEYWORD && val == 'is' }, {
							isMember: true;
							scanning: false;
						});
						if({ !isMember && tok:getTokenKind() == TokenKind:SYMBOL && val == ';' }, {
							isMember: true;
							scanning: false;
						});
						if({ !isMember && tok:getTokenKind() == TokenKind:SYMBOL && (val == ',' || val == '{') }, {
							scanning: false;
						});
					});
				});
			});
			j: j + 1;
		});

		return isMember;
	}

	## Parses one enum declaration: `Enum of Backing is Name` with tagged or
	## ordinal variants.
	##
	## @return: The enum descriptor (base class Enum).
	Function of ClassInfo is parseEnum(){
		self:advance();
		local String is backingType: self:names:intName();
		if({ self:checkKeyword(kw: Keyword:OF) }, {
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
		while({ !self:checkPunct(p: Punctuation:BLOCK_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
			if({ self:atEnumMember() }, {
				members:add(item: self:parseMember());
			}, {
				local Token is vTok: self:advance();
				local String is vName: vTok:getValue();
				local Array of Parameter is vParams: [];
				if({ self:checkPunct(p: Punctuation:GROUP_OPEN) }, {
					self:advance();
					vParams: self:parseParams();
					self:matchPunct(p: Punctuation:GROUP_CLOSE);
				});
				local Expression is valExpr: Expression:Unknown;
				local Boolean is hasInit: false;
				if({ self:checkPunct(p: Punctuation:TAG) }, {
					self:advance();
					valExpr: self:parseExpression();
					hasInit: true;
				}, {
					valExpr: Expression:NumberLit(value: count, text: '' . count);
					hasInit: true;
				});
				count: count + 1;

				local Member is m: Member:init(kind: MemberKind:FIELD);
				m:setLine(line: vTok:getLine());
				m:modifiers: ['static', 'local'];
				m:memberType: Type:init(name: backingType);
				m:name: vName;
				m:params: vParams;
				m:initExpr: valExpr;
				m:hasInit: hasInit;
				members:add(item: m);

				if({ self:checkPunct(p: Punctuation:SEPARATOR) }, {
					self:advance();
				});
			});
		});
		self:matchPunct(p: Punctuation:BLOCK_CLOSE);
		if({ self:checkPunct(p: Punctuation:TERMINATOR) }, {
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

	if({ self:atClassHeader() }, {
		local ClassInfo is nested: self:parseClass();
		local Member is m: Member:init(kind: MemberKind:CLASS);
		m:setLine(line: startLine);
		# the member identifies its class — the unnamed member
		# matched other unnamed members in the override and registry walks.
		m:name: nested:name;
		m:nestedClass: nested;
		return m;
	});

	if({ self:atEnumHeader() }, {
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
		if({ (self:peek():getTokenKind() == TokenKind:IDENTIFIER || self:peek():getTokenKind() == TokenKind:KEYWORD) && self:peekAhead(offset: 1):getTokenKind() == TokenKind:SYMBOL && self:peekAhead(offset: 1):getValue() == ':' }, {
			local Token is nameTok: self:advance();
			self:advance();
			local Expression is initExpr: self:parseExpression();
			if({ self:checkPunct(p: Punctuation:TERMINATOR) }, {
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
		if({ self:peek():getTokenKind() == TokenKind:IDENTIFIER && self:peekAhead(offset: 1):getValue() == Punctuation:GROUP_OPEN:value() }, {
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

		if({ self:checkPunct(p: Punctuation:GROUP_OPEN) }, {
			self:advance();
			local Array of Parameter is params: self:parseParams();
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
			# Interface-style declaration: a `;`-terminated signature with no
			# body — the sysinternal floor-binding form.
			if({ self:checkPunct(p: Punctuation:TERMINATOR) }, {
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
		if({ self:checkPunct(p: Punctuation:ASSIGN) }, {
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
			if({ p:paramType:name == self:names:selfFieldMarker() }, {
				local Expression is lhs: Expression:Path(segments: [self:names:selfIdent(), p:name]);
				local Expression is rhs: Expression:Ident(name: p:name);
				local Statement is assignS: Statement:Assign(assignTarget: lhs, assignValue: rhs);
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
		if({ self:checkPunct(p: Punctuation:BRACKET_OPEN) }, {
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

		if({ self:checkKeyword(kw: Keyword:OF) }, {
			self:advance();
			local Array of Type is params: [];
			params:add(item: self:parseType());

			if({ self:checkKeyword(kw: Keyword:TO) }, {
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
		if({ self:checkPunct(p: Punctuation:GROUP_OPEN) }, {
			return self:parseForwardStatement(startLine: startLine);
		});

		# Scoped callback statement: `as: call;` or `as (params): call;`.
		if({ self:checkKeyword(kw: Keyword:AS) }, {
			return self:parseAsStatement(startLine: startLine);
		});

		if({ self:atClassHeader() }, {
			local ClassInfo is cls: self:parseClass();
			local Statement is s: Statement:ClassDecl(nestedClass: cls);
			s:setLine(line: startLine);
			return s;
		});

		if({ self:atEnumHeader() }, {
			local ClassInfo is edef: self:parseEnum();
			local Statement is s: Statement:ClassDecl(nestedClass: edef);
			s:setLine(line: startLine);
			return s;
		});


		if({ self:checkKeyword(kw: Keyword:RETURN) }, {
			self:advance();
			if({ self:checkKeyword(kw: Keyword:AS) }, {
				local Statement is asStmt: self:parseAsStatement(startLine: startLine);
				local Expression is asExpr: match(on: asStmt, when: [
					Statement:Expr: local Function of Expression(Expression is exprStmt){
						return exprStmt;
					},
					else: { return Expression:Unknown; }
				]);
				local Statement is s: Statement:Return(returnExpr: asExpr, hasReturnExpr: true);
				s:setLine(line: startLine);
				return s;
			});
			local Expression is retExpr: Expression:Unknown;
			local Boolean is hasExpr: false;
			if({ !self:checkPunct(p: Punctuation:TERMINATOR) }, {
				retExpr: self:parseExpression();
				hasExpr: true;
			});
			self:matchPunct(p: Punctuation:TERMINATOR);

			local Statement is s: Statement:Return(returnExpr: retExpr, hasReturnExpr: hasExpr);
			s:setLine(line: startLine);
			return s;
		});

		if({ self:checkKeyword(kw: Keyword:LOCAL) }, {
			self:advance();
			local Type is vType: self:parseType();
			self:matchKeyword(kw: Keyword:IS);
			local Token is nameTok: self:advance();
			local String is name: nameTok:getValue();

			local Expression is initExpr: Expression:Unknown;
			local Boolean is hasInit: false;
			if({ self:checkPunct(p: Punctuation:ASSIGN) }, {
				self:advance();
				initExpr: self:parseExpression();
				hasInit: true;
			});
			self:matchPunct(p: Punctuation:TERMINATOR);

			local Statement is s: Statement:VarDecl(modifiers: ['local'], varType: vType, varName: name, initExpr: initExpr, hasInit: hasInit);
			s:setLine(line: startLine);
			return s;
		});

		# Expression or assignment: `target: value;` assigns, anything else
		# evaluates for effect.
		local Expression is expr: self:parseExpression();

		if({ self:checkPunct(p: Punctuation:ASSIGN) }, {
			self:advance();
			local Expression is val: self:parseExpression();
			self:matchPunct(p: Punctuation:TERMINATOR);

			local Statement is s: Statement:Assign(assignTarget: expr, assignValue: val);
			s:setLine(line: startLine);
			return s;
		});

		self:matchPunct(p: Punctuation:TERMINATOR);
		local Statement is s: Statement:Expr(exprStmt: expr);
		s:setLine(line: startLine);
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
		if({ self:checkPunct(p: Punctuation:TERMINATOR) }, {
			self:advance();
		});
		local Statement is s: Statement:Forward(forwardArgs: args);
		s:setLine(line: startLine);
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
		if({ self:checkPunct(p: Punctuation:GROUP_OPEN) }, {
			self:advance();
			hasParams: true;
			params: self:parseParams();
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
		});
		local Type is returnType: Type:init(name: self:names:voidName());
		if({ self:checkKeyword(kw: Keyword:OF) }, {
			self:advance();
			returnType: self:parseType();
		});
		if({ self:checkPunct(p: Punctuation:ACCESSOR) }, {
			self:advance();
		}, {
			if({ !hasParams }, {
				self:matchPunct(p: Punctuation:ACCESSOR);
			});
		});
		local Expression is callExpr: self:parseExpression();
		self:matchPunct(p: Punctuation:TERMINATOR);

		local Array of Statement is closureBody: [];
		while({ !self:checkPunct(p: Punctuation:BLOCK_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
			closureBody:add(item: self:parseStatement());
		});

		local Expression is anonFn: Expression:AnonFn(returnType: returnType, params: params, body: closureBody);

		local CallData is cd: match(on: callExpr, when: [
			Expression:Call: local Function of CallData(CallData is call){ return call; },
			else: {
				local CallData is created: match(on: callExpr, when: [
					Expression:FieldAccess: local Function of CallData(Expression is target, String is fieldName){
						return CallData:init(target: target, name: fieldName, args: []);
					},
					Expression:Ident: local Function of CallData(String is name){
						return CallData:init(target: Expression:Ident(name: self:names:selfIdent()), name: name, args: []);
					},
					else: {
						CallData:init(target: callExpr, name: '', args: [])
					}
				]);
				callExpr: Expression:Call(call: created);
				created
			}
		]);

		cd:args:add(item: NamedArg:init(name: '', value: anonFn));
		# §as: the remainder is not an argument — it fills the
		# callable's declared-but-unbound last Function parameter. The
		# marker keeps it out of overload selection.
		cd:scopedRemainder: true;

		local Statement is s: Statement:Expr(exprStmt: callExpr);
		s:setLine(line: startLine);
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
		return match(on: level, when: [
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
		local Expression is left: Expression:Unknown;
		if({ next == PrecedenceLevel:NONE }, {
			left: self:parseUnary();
		}, {
			left: self:parseLevel(level: next);
		});
		while({ ops:indexOf(search: self:peek():getValue(), default: -1) >= 0 }, {
			local Token is opTok: self:advance();
			local String is op: opTok:getValue();
			if({ op == Keyword:IS:value() }, {
				op: '==';
			});
			local Expression is right: Expression:Unknown;
			if({ next == PrecedenceLevel:NONE }, {
				right: self:parseUnary();
			}, {
				right: self:parseLevel(level: next);
			});
			left: Expression:Binary(op: op, left: left, right: right);
		});
		return left;
	}

	## Parses unary operators (~, -, !) or descends to casts.
	##
	## @return: The expression node.
	Function of Expression is parseUnary(){
		local String is op: '';
		if({ self:checkSymbol(value: '++') }, {
			op: '++';
		}, {
			if({ self:checkSymbol(value: '--') }, {
				op: '--';
			}, {
				if({ self:checkSymbol(value: '~') }, {
					op: '~';
				}, {
					if({ self:checkSymbol(value: '-') }, {
						op: '-';
					}, {
						if({ self:checkSymbol(value: '!') }, {
							op: '!';
						}, {
							return self:parseAs();
						});
					});
				});
			});
		});
		self:advance();
		local Expression is expr: self:parseUnary();
		return Expression:Unary(op: op, operand: expr);
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
		if({ clsTok:getTokenKind() != TokenKind:IDENTIFIER }, {
			self:addError(tok: clsTok, message: self:errText:errUsingAsRequiresClass());
			return Expression:Unknown;
		});
		self:advance();
		local String is clsName: clsTok:getValue();
		local Array of NamedArg is args: [];
		if({ self:checkPunct(p: Punctuation:GROUP_OPEN) }, {
			self:advance();
			if({ !self:checkPunct(p: Punctuation:GROUP_CLOSE) }, {
				args: self:parseArgs();
				args:each(action: local Function(NamedArg is arg){
					local Boolean is isLiteral: match(on: arg:value, when: [
						Expression:StringLit: local Function of Boolean(String is value){ return true; },
						Expression:NumberLit: local Function of Boolean(Int is value, String is text){ return true; },
						Expression:FloatLit: local Function of Boolean(String is text){ return true; },
						Expression:BoolLit: local Function of Boolean(Boolean is value){ return true; },
						else: { false }
					]);
					if({ !isLiteral }, {
						self:addError(tok: clsTok, message: self:errText:errInstanceImportLiteralArgs());
					});
				});
			});
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
		}, {
			self:addError(tok: clsTok, message: self:errText:errInstanceImportParens(target: clsName));
		});
		return Expression:UsingAs(className: clsName, args: args);
	}

	## Parses a type cast: `value as Target` or `value as Target(width)`.
	## Binding is tighter than every binary operator; chaining
	## (`x as A as B`) is rejected.
	##
	## @return: The expression node.
	Function of Expression is parseAs(){
		local Expression is left: self:parsePostfix();
		if({ self:checkKeyword(kw: Keyword:AS) }, {
			self:advance();
			local Token is targetTok: self:advance();
			local Array of Expression is args: [];
			if({ self:checkPunct(p: Punctuation:GROUP_OPEN) }, {
				self:advance();
				if({ !self:checkPunct(p: Punctuation:GROUP_CLOSE) }, {
					args:add(item: self:parseExpression());
				});
				self:matchPunct(p: Punctuation:GROUP_CLOSE);
			});
			if({ self:checkKeyword(kw: Keyword:AS) }, {
				self:addError(tok: self:peek(), message: self:errText:errChainedAsUnsupported());
			});
			return Expression:Cast(inner: left, target: targetTok:getValue(), args: args);
		});
		return left;
	}

	## Returns whether the next token starts a postfix operator or access.
	Function of Boolean is atPostfix(){
		if({ self:checkPunct(p: Punctuation:GROUP_OPEN) || self:checkPunct(p: Punctuation:BRACKET_OPEN) || self:checkSymbol(value: '++') || self:checkSymbol(value: '--') }, {
			return true;
		});
		if({ self:checkPunct(p: Punctuation:ACCESSOR) }, {
			# Whitespace before ':' means assignment context, not a path.
			if({ self:hasWhitespaceAfter(offset: 0) }, {
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
			if({ self:checkPunct(p: Punctuation:GROUP_OPEN) }, {
				self:advance();
				local Array of NamedArg is args: self:parseArgs();
				self:matchPunct(p: Punctuation:GROUP_CLOSE);

				local CallData is cd: match(on: currentExpr, when: [
					Expression:Ident: local Function of CallData(String is name){
						return if({ name == 'Loops' }, {
							CallData:init(target: currentExpr, name: 'loop', args: args)
						}, {
							CallData:init(target: Expression:Ident(name: self:names:selfIdent()), name: name, args: args)
						});
					},
					else: {
						CallData:init(target: currentExpr, name: '', args: args)
					}
				]);
				currentExpr: Expression:Call(call: cd);
			}, {
				if({ self:checkPunct(p: Punctuation:BRACKET_OPEN) }, {
					self:advance();
					local Expression is idxExpr: self:parseExpression();
					self:matchPunct(p: Punctuation:BRACKET_CLOSE);

					currentExpr: Expression:Index(target: currentExpr, index: idxExpr);
				}, {
					if({ self:checkSymbol(value: '++') }, {
						self:advance();
						currentExpr: Expression:Unary(op: 'post++', operand: currentExpr);
					}, {
						if({ self:checkSymbol(value: '--') }, {
							self:advance();
							currentExpr: Expression:Unary(op: 'post--', operand: currentExpr);
						}, {
							if({ self:checkPunct(p: Punctuation:ACCESSOR) }, {
								self:advance();
								local Token is mTok: self:advance();
								local String is method: mTok:getValue();

								if({ self:checkPunct(p: Punctuation:GROUP_OPEN) }, {
									self:advance();
									local Array of NamedArg is args: self:parseArgs();
									self:matchPunct(p: Punctuation:GROUP_CLOSE);

									currentExpr: Expression:Call(call: CallData:init(target: currentExpr, name: method, args: args));
								}, {
									local Boolean is isPathOrIdent: match(on: currentExpr, when: [
										Expression:Path: local Function of Boolean(Array of String is segments){ return true; },
										Expression:Ident: local Function of Boolean(String is name){ return true; },
										else: { false }
									]);
									if({ !isPathOrIdent }, {
										currentExpr: Expression:FieldAccess(target: currentExpr, fieldName: method);
									}, {
										local Array of String is segs: [];
										match(on: currentExpr, when: [
											Expression:Path: local Function(Array of String is segments){
												segments:each(action: local Function(String is s){
													segs:add(item: s);
												});
											},
											Expression:Ident: local Function(String is name){
												segs:add(item: name);
											}
										]);
										segs:add(item: method);
										currentExpr: Expression:Path(segments: segs);
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
		if({ self:checkKeyword(kw: Keyword:LOCAL) && self:peekAhead(offset: 1):getValue() == self:names:fnName() }, {
			isAnonFn: true;
		});
		if({ self:peek():getValue() == self:names:fnName() && (self:peekAhead(offset: 1):getValue() == Punctuation:GROUP_OPEN:value() || self:peekAhead(offset: 1):getValue() == Keyword:OF:value()) }, {
			isAnonFn: true;
		});

		if({ isAnonFn }, {
			if({ self:checkKeyword(kw: Keyword:LOCAL) }, {
				self:advance();
			});
			self:advance();
			local Type is returnType: Type:init(name: self:names:voidName());
			if({ self:checkKeyword(kw: Keyword:OF) }, {
				self:advance();
				returnType: self:parseType();
			});
			self:matchPunct(p: Punctuation:GROUP_OPEN);
			local Array of Parameter is params: self:parseParams();
			self:matchPunct(p: Punctuation:GROUP_CLOSE);
			local Array of Statement is body: self:parseMethodBody(params: params);

			return Expression:AnonFn(returnType: returnType, params: params, body: body);
		});


		local Token is tok: self:peek();

		return match(on: tok:getTokenKind(), when: [
			TokenKind:STRING: {
				self:advance();
				Expression:StringLit(value: tok:getValue()) as Expression
			},
			TokenKind:RAWSTRING: {
				self:advance();
				Expression:StringLit(value: tok:getValue()) as Expression
			},
			TokenKind:TEMPLATESTRING: {
				self:advance();
				self:expandFancyString(raw: tok:getValue(), originTok: tok, depth: self:templateDepth)
			},
			TokenKind:INT: {
				self:advance();
				Expression:NumberLit(value: 0, text: tok:getValue()) as Expression
			},
			TokenKind:FLOAT: {
				self:advance();
				Expression:FloatLit(text: tok:getValue()) as Expression
			},
			TokenKind:BOOL: {
				self:advance();
				Expression:BoolLit(value: tok:getValue() == self:names:boolTrue()) as Expression
			},
			TokenKind:IDENTIFIER: {
				self:advance();
				Expression:Ident(name: tok:getValue()) as Expression
			},
			TokenKind:KEYWORD: {
				# Expression-initial `as` is the instance-import form
				# `as ClassName()` (§2.1); `as` never begins any
				# other expression (casts are postfix, scoped regions are
				# statement-initial).
				if({ self:checkKeyword(kw: Keyword:AS) }, {
					return self:parseUsingAs();
				});
				self:addError(tok: tok, message: self:errText:errUnexpectedTokenInExpression(token: tok:getValue()));
				self:advance();
				Expression:Unknown
			},
			else: {
				if({ self:checkPunct(p: Punctuation:GROUP_OPEN) }, {
					self:advance();
					local Expression is inner: self:parseExpression();
					self:matchPunct(p: Punctuation:GROUP_CLOSE);
					return inner;
				});

				if({ self:checkPunct(p: Punctuation:BRACKET_OPEN) }, {
					return self:parseArrayOrMap();
				});

				if({ self:checkPunct(p: Punctuation:BLOCK_OPEN) }, {
					return self:parseFunctionBlock();
				});

				self:addError(tok: tok, message: self:errText:errUnexpectedTokenInExpression(token: tok:getValue()));
				self:advance();
				Expression:Unknown
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
			if({ t:getTokenKind() == TokenKind:EOF }, {
				running: false;
			}, {
				if({ depth == 0 && (v == ']' || v == ',' || v == ';') }, {
					running: false;
				}, {
					if({ v == '(' || v == '[' || v == '{' }, {
						depth: depth + 1;
					}, {
						if({ v == ')' || v == ']' || v == '}' }, {
							depth: depth - 1;
						}, {
							if({ depth == 0 && t:getTokenKind() == TokenKind:KEYWORD && v == Keyword:IS:value() }, {
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
			if({ self:checkPunct(p: Punctuation:ASSIGN) }, {
				self:advance();
				p:setDefault(expr: self:parseExpression());
			});
			params:add(item: p);
			if({ self:checkPunct(p: Punctuation:SEPARATOR) }, {
				self:advance();
			}, {
				keepGoing: false;
			});
		});
		self:matchPunct(p: Punctuation:BRACKET_CLOSE);
		return Expression:AnonFn(returnType: Type:init(name: ''), params: params, body: []);
	}

	## Parses a function block shorthand `{ ... }` as an anonymous function.
	## Statements built here carry their source line: the shorthand bodies
	## are where user code actually lives (loop/branch arms), and both the
	## checker's diagnostics and the debug emission's #line directives
	## read Statement:line.
	##
	## @return: The ANON_FN expression.
	Function of Expression is parseFunctionBlock(){
		self:matchPunct(p: Punctuation:BLOCK_OPEN);
		local Array of Statement is body: [];
		local Array of Parameter is params: [];
		local Type is returnType: Type:init(name: self:names:voidName());

		while({ !self:checkPunct(p: Punctuation:BLOCK_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
			local Int is stmtLine: self:peek():getLine();
			if({ !self:checkKeyword(kw: Keyword:RETURN) && !self:checkKeyword(kw: Keyword:LOCAL) && !self:checkKeyword(kw: Keyword:AS) }, {
				local Expression is expr: self:parseExpression();
				if({ self:checkPunct(p: Punctuation:ASSIGN) }, {
					self:advance();
					local Expression is val: self:parseExpression();
					self:matchPunct(p: Punctuation:TERMINATOR);
					local Statement is s: Statement:Assign(assignTarget: expr, assignValue: val);
					s:setLine(line: stmtLine);
					body:add(item: s);
				}, {
					if({ self:checkPunct(p: Punctuation:BLOCK_CLOSE) }, {
						local Statement is retS: Statement:Return(returnExpr: expr, hasReturnExpr: true);
						retS:setLine(line: stmtLine);
						body:add(item: retS);
					}, {
						self:matchPunct(p: Punctuation:TERMINATOR);
						local Statement is exprS: Statement:Expr(exprStmt: expr);
						exprS:setLine(line: stmtLine);
						body:add(item: exprS);
					});
				});
			}, {
				body:add(item: self:parseStatement());
			});
		});
		self:matchPunct(p: Punctuation:BLOCK_CLOSE);

		return Expression:AnonFn(returnType: returnType, params: params, body: body);
	}

	## Parses a bracketed `[...]` literal: array, map, or their empty
	## forms (distinguished by `:]` for an empty map).
	##
	## @return: The ARRAY or MAP node.
	Function of Expression is parseArrayOrMap(){
		if({ self:isDeclListStart() }, {
			return self:parseDeclList();
		});
		self:advance();
		if({ self:checkPunct(p: Punctuation:BRACKET_CLOSE) }, {
			self:advance();
			return Expression:ArrayLit(items: []);
		});
		if({ self:checkPunct(p: Punctuation:PAIR) }, {
			self:advance();
			self:matchPunct(p: Punctuation:BRACKET_CLOSE);
			return Expression:MapLit(keys: [], values: []);
		});
		local Expression is firstItem: self:parseExpression();
		if({ self:checkPunct(p: Punctuation:PAIR) }, {
			self:advance();
			local Expression is firstVal: self:parseExpression();
			local Array of Expression is mKeys: [firstItem];
			local Array of Expression is mVals: [firstVal];
			if({ self:checkPunct(p: Punctuation:SEPARATOR) }, {
				self:advance();
				local Boolean is keepGoing: true;
				while({ keepGoing && !self:checkPunct(p: Punctuation:BRACKET_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
					local Expression is k: self:parseExpression();
					self:matchPunct(p: Punctuation:PAIR);
					local Expression is v: self:parseExpression();
					mKeys:add(item: k);
					mVals:add(item: v);
					if({ self:checkPunct(p: Punctuation:SEPARATOR) }, {
						self:advance();
					}, {
						keepGoing: false;
					});
				});
			});
			self:matchPunct(p: Punctuation:BRACKET_CLOSE);
			return Expression:MapLit(keys: mKeys, values: mVals);
		});
		local Array of Expression is items: [firstItem];
		if({ self:checkPunct(p: Punctuation:SEPARATOR) }, {
			self:advance();
			local Boolean is keepGoing: true;
			while({ keepGoing && !self:checkPunct(p: Punctuation:BRACKET_CLOSE) && !self:check(kind: TokenKind:EOF, value: '') }, {
				items:add(item: self:parseExpression());
				if({ self:checkPunct(p: Punctuation:SEPARATOR) }, {
					self:advance();
				}, {
					keepGoing: false;
				});
			});
		});
		self:matchPunct(p: Punctuation:BRACKET_CLOSE);
		return Expression:ArrayLit(items: items);
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
		if({ depth > 0 }, {
			local String is dRes: '';
			local Int is dPos: 0;
			local TemplateEscapes is esc: TemplateEscapes:init();
			while({ dPos < raw:length() }, {
				local String is ch: raw:charAt(index: dPos, default: '');
				dPos: dPos + 1;
				if({ ch == "\\" }, {
					if({ dPos < raw:length() }, {
						local String is nextCh: raw:charAt(index: dPos, default: '');
						dPos: dPos + 1;
						dRes: dRes . esc:expand(escaped: nextCh);
					}, {
						dRes: dRes . "\\";
					});
				}, {
					dRes: dRes . ch;
				});
			});
			return Expression:StringLit(value: dRes);
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
			if({ !inHole }, {
				if({ ch == "{" && sPos + 1 < raw:length() && raw:charAt(index: sPos + 1, default: '') == "{" }, {
					lits:add(item: lit);
					lit: '';
					inHole: true;
					hole: '';
					quoteCh: '';
					braceDepth: 0;
					sPos: sPos + 2;
				}, {
					if({ ch == "\\" }, {
						if({ sPos + 1 < raw:length() }, {
							local String is nextCh: raw:charAt(index: sPos + 1, default: '');
							lit: lit . esc:expand(escaped: nextCh);
							sPos: sPos + 2;
						}, {
							lit: lit . "\\";
							sPos: sPos + 1;
						});
					}, {
						lit: lit . ch;
						sPos: sPos + 1;
					});
				});
			}, {
				if({ quoteCh != '' }, {
					if({ ch == "\\" }, {
						hole: hole . ch;
						sPos: sPos + 1;
						if({ sPos < raw:length() }, {
							hole: hole . raw:charAt(index: sPos, default: '');
							sPos: sPos + 1;
						});
					}, {
						if({ ch == quoteCh }, {
							quoteCh: '';
						});
						hole: hole . ch;
						sPos: sPos + 1;
					});
				}, {
					if({ ch == '\'' || ch == '"' }, {
						quoteCh: ch;
						hole: hole . ch;
						sPos: sPos + 1;
					}, {
						if({ ch == "{" }, {
							braceDepth: braceDepth + 1;
							hole: hole . ch;
							sPos: sPos + 1;
						}, {
							if({ ch == "}" }, {
								if({ braceDepth > 0 }, {
									braceDepth: braceDepth - 1;
									hole: hole . ch;
									sPos: sPos + 1;
								}, {
									if({ sPos + 1 < raw:length() && raw:charAt(index: sPos + 1, default: '') == "}" }, {
										holes:add(item: hole);
										hole: '';
										inHole: false;
										sPos: sPos + 2;
									}, {
										hole: hole . ch;
										sPos: sPos + 1;
									});
								});
							}, {
								hole: hole . ch;
								sPos: sPos + 1;
							});
						});
					});
				});
			});
		});

		lits:add(item: lit);
		if({ inHole }, {
			self:addError(tok: originTok, message: self:errText:errUnterminatedTemplateHole());
			return Expression:StringLit(value: '');
		});
		local Expression is acc: Expression:StringLit(value: lits:get(index: 0));
		if({ holes:length() == 0 }, {
			return acc;
		});

		local Int is k: 0;
		repeat(count: holes:length(), worker: {
			local Expression is holeE: self:parseTemplateExpression(text: holes:get(index: k));
			local Expression is withHole: Expression:Binary(op: '.', left: acc, right: holeE);
			local Expression is litE: Expression:StringLit(value: lits:get(index: k + 1));
			acc: Expression:Binary(op: '.', left: withHole, right: litE);
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
		local Expression is emptyE: Expression:StringLit(value: '');
		if({ text:trim():length() == 0 }, {
			self:addError(tok: self:peek(), message: self:errText:errEmptyTemplateExpression());
			return emptyE;
		});
		local Lexer is subLexer: Lexer:init(source: text);
		local Array of Token is subTokens: subLexer:tokenize();
		if({ subLexer:hasErrors() }, {
			self:addError(tok: self:peek(), message: self:errText:errInvalidTemplateExpression());
			return emptyE;
		});
		local Parser is subParser: Parser:init(tokens: subTokens);
		subParser:setTemplateDepth(depth: 1);
		local Expression is e: subParser:parseExpression();
		if({ subParser:hasErrors() || subParser:peek():getTokenKind() != TokenKind:EOF }, {
			self:addError(tok: self:peek(), message: self:errText:errInvalidTemplateExpression());
			return emptyE;
		});
		return e;
	}
}
