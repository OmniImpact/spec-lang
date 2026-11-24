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
	replace [String] is namespace: ['base', 'compiler', 'parser'];

	replace [[String]] is using: [
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
		['base', 'sys', as Conditional()]
	];

	local [Token] is tokens: [];
	local Int is pos: 0;
	local Int is length: 0;
	local String is sourceFile: '';
	local [Error] is errors: [];
	local ErrorText is errText: ErrorText:init();

	local Lexer is lexer: Lexer:init(source: '');
	local [Token] is lookahead: [];
	local Int is lookaheadHead: 0;
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
	replace Function is init([Token] is tokens){
		:tokens: tokens;
		:length: tokens:length();
		:pos: 0;
		:sourceFile: '';
		:errors: [];
		:templateDepth: 0;
		:streaming: false;
		:lookahead: [];
		:lookaheadHead: 0;
	}

	## Configures the parser to stream tokens on-demand from a lexer.
	##
	## @param lexer: The active lexer instance.
	Function is setLexer(Lexer is lexer){
		:lexer: lexer;
		:streaming: true;
		:lookahead: [];
		:lookaheadHead: 0;
	}

	## Attaches the declaring file for provenance.
	##
	## @param file: Source file path.
	Function is setSourceFile(String is file){
		:sourceFile: file;
	}

	## Sets the template nesting depth (sub-parsers inside holes run at 1).
	##
	## @param depth: The depth to run at.
	Function is setTemplateDepth(Int is depth){
		:templateDepth: depth;
	}

	## Returns whether any parse errors were recorded.
	##
	## @return: true when [errors] is non-empty.
	Function of Boolean is hasErrors(){
		return :errors:length() > 0;
	}

	## Returns all recorded parse errors.
	##
	## @return: [Error] values, in discovery order.
	Function of [Error] is getErrors(){
		return :errors;
	}

	## Records a parse error at the given token's coordinates.
	##
	## @param tok: The offending token.
	## @param message: What went wrong.
	Function is addError(Token is tok, String is message){
		local String is prefix: if({ :sourceFile != '' }, { :sourceFile . ':' }, { 'Line ' });
		local SourceLocation is loc: SourceLocation(file: :sourceFile, line: tok:getLine(), col: tok:getCol(), length: tok:getValue():length());
		local Error is e: Error(message: "  [SyntaxError] [{{prefix}}{{tok:getLine()}}:{{tok:getCol()}}] {{message}}", location: loc);
		e:addTraceAt(className: Reflection:class(), methodName: Reflection:method(), line: tok:getLine(), col: tok:getCol());
		:errors:push(item: e);
	}

	## Returns the current token without consuming it.
	##
	## @return: The current token; EOF past the end.
	Function of Token is peek(){
		if({ :streaming }, {
			return :peekAhead(offset: 0);
		});
		if({ :pos < :length }, {
			return :tokens:get(index: :pos);
		});
		return Token:init(kind: TokenKind:EOF, value: '', line: 0, col: 0);
	}

	## Returns the token [offset] positions ahead.
	##
	## @param offset: Lookahead distance.
	## @return: The token; EOF past the end.
	Function of Token is peekAhead(Int is offset){
		if({ :streaming }, {
			local Boolean is pulling: true;
			while({ pulling && (:lookahead:length() - :lookaheadHead) <= offset }, {
				local Token is tok: :lexer:nextToken();
				:lookahead:push(item: tok);
				if({ tok:getTokenKind() == TokenKind:EOF }, {
					pulling: false;
				});
			});
			if({ (:lookaheadHead + offset) < :lookahead:length() }, {
				return :lookahead:get(index: :lookaheadHead + offset);
			});
			return Token:init(kind: TokenKind:EOF, value: '', line: 0, col: 0);
		});
		local Int is idx: :pos + offset;
		if({ idx < :length }, {
			return :tokens:get(index: idx);
		});
		return Token:init(kind: TokenKind:EOF, value: '', line: 0, col: 0);
	}

	## Consumes and returns the current token.
	##
	## @return: The consumed token.
	Function of Token is advance(){
		if({ :streaming }, {
			local Token is tok: :peekAhead(offset: 0);
			if({ :lookaheadHead < :lookahead:length() }, {
				:lookaheadHead: :lookaheadHead + 1;
				if({ :lookaheadHead >= :lookahead:length() }, {
					:lookahead: [];
					:lookaheadHead: 0;
				});
			});
			return tok;
		});
		local Token is tok: :peek();
		if({ :pos < :length }, {
			:pos: :pos + 1;
		});
		return tok;
	}

	## True when the token [offset] ahead starts on a new line or column
	## position that implies whitespace separation.
	##
	## @param offset: Lookahead distance.
	## @return: true when whitespace separates the tokens.
	Function of Boolean is hasWhitespaceAfter(Int is offset){
		local Token is cur: :peekAhead(offset: offset);
		local Token is nxt: :peekAhead(offset: offset + 1);
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
		local Token is tok: :peek();
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
		if({ :check(kind: TokenKind:SYMBOL, value: value) }, {
			:advance();
			return true;
		});
		local Token is tok: :peek();
		:addError(tok: tok, message: :errText:errExpectedFound(expected: value, found: tok:getValue()));
		return false;
	}

	## Non-consuming symbol test.
	##
	## @param value: Expected symbol lexeme.
	## @return: true on match.
	Function of Boolean is checkSymbol(String is value){
		return :check(kind: TokenKind:SYMBOL, value: value);
	}

	## Consumes the current punctuation token when it matches; records an
	## error when it does not.
	##
	## @param p: Expected punctuation.
	## @return: true on match.
	Function of Boolean is matchPunct(Punctuation is p){
		if({ :check(kind: TokenKind:SYMBOL, value: p:value()) }, {
			:advance();
			return true;
		});
		local Token is tok: :peek();
		:addError(tok: tok, message: :errText:errExpectedFound(expected: p:value(), found: tok:getValue()));
		return false;
	}

	## Non-consuming punctuation test.
	##
	## @param p: Expected punctuation.
	## @return: true on match.
	Function of Boolean is checkPunct(Punctuation is p){
		return :check(kind: TokenKind:SYMBOL, value: p:value());
	}

	## Non-consuming reserved-word test.
	##
	## @param kw: Expected keyword.
	## @return: true on match.
	Function of Boolean is checkKeyword(Keyword is kw){
		return :check(kind: TokenKind:KEYWORD, value: kw:value());
	}

	## Consumes the current reserved word when it matches; records an error
	## when it does not.
	##
	## @param kw: Expected keyword.
	## @return: true on match.
	Function of Boolean is matchKeyword(Keyword is kw){
		if({ :check(kind: TokenKind:KEYWORD, value: kw:value()) }, {
			:advance();
			return true;
		});
		local Token is tok: :peek();
		:addError(tok: tok, message: :errText:errExpectedFound(expected: kw:value(), found: tok:getValue()));
		return false;
	}

	## Consumes call arguments: positional or `name: value` pairs.
	Function of [NamedArg] is parseArgs(){
		local [NamedArg] is args: [];
		local Boolean is keepGoing: true;
		while({ keepGoing && !:checkPunct(p: Punctuation:GROUP_CLOSE) && !:check(kind: TokenKind:EOF, value: '') }, {
			local String is argName: '';
			local Token is tok0: :peekAhead(offset: 0);
			if({ tok0:getTokenKind() == TokenKind:IDENTIFIER && :peekAhead(offset: 1):getValue() == Punctuation:NAMED_ARG:value() }, {
				local String is nameVal: tok0:getValue();
				local Boolean is isUpper: :chars:isUpper(ch: nameVal:charAt(index: 0, default: ''));
				if({ !isUpper }, {
					local Token is nextTok: :peekAhead(offset: 2);
					local Boolean is isNamed: false;
					if({ nextTok:getTokenKind() != TokenKind:IDENTIFIER }, {
						isNamed: true;
					}, {
						isNamed: :hasWhitespaceAfter(offset: 1);
					});
					if({ isNamed }, {
						local Token is aTok: :advance();
						argName: aTok:getValue();
						:advance();
					});
				});
			});
			local Expression is val: :parseExpression();
			args:push(item: NamedArg(name: argName, value: val));
			if({ :checkPunct(p: Punctuation:SEPARATOR) }, {
				:advance();
			}, {
				keepGoing: false;
			});
		});
		return args;
	}

	## Consumes formal parameter lists: `Type is name`, shorthand `name`
	## (Any-typed), and `self: field` receiver fields.
	Function of [Parameter] is parseParams(){
		local [Parameter] is params: [];
		local Boolean is keepGoing: true;
		while({ keepGoing && !:checkPunct(p: Punctuation:GROUP_CLOSE) && !:check(kind: TokenKind:EOF, value: '') }, {
			# `:field` / `: field` declares a receiver field parameter.
			if({ :peek():getValue() == ':' && :peekAhead(offset: 1):getTokenKind() == TokenKind:IDENTIFIER }, {
				:advance();
				local Token is fTok: :advance();
				local Parameter is param: Parameter(name: fTok:getValue(), paramType: Type(name: :names:selfFieldMarker()));
				if({ :checkPunct(p: Punctuation:DEFAULT) }, {
					:advance();
					param:setDefault(expr: :parseExpression());
				});
				params:push(item: param);
				if({ :checkPunct(p: Punctuation:SEPARATOR) }, {
					:advance();
				}, {
					keepGoing: false;
				});
			}, {
				# Shorthand: a bare identifier is an Any-typed parameter.
				if({ :peekAhead(offset: 1):getValue() == Punctuation:SEPARATOR:value() || :peekAhead(offset: 1):getValue() == Punctuation:GROUP_CLOSE:value() }, {
					local Token is pTok: :advance();
					params:push(item: Parameter(name: pTok:getValue(), paramType: Type(name: :names:anyName())));
					if({ :checkPunct(p: Punctuation:SEPARATOR) }, {
						:advance();
					}, {
						keepGoing: false;
					});
				}, {
					local Type is pType: :parseType();
					:matchKeyword(kw: Keyword:IS);
					local Boolean is isVar: false;
					if({ :peek():getValue() == '*' }, {
						:advance();
						isVar: true;
					});
					local Token is pTok: :advance();
					local Parameter is param: Parameter(name: pTok:getValue(), paramType: pType);
					param:isVariadic: isVar;
					if({ :checkPunct(p: Punctuation:DEFAULT) }, {
						:advance();
						param:setDefault(expr: :parseExpression());
					});
					params:push(item: param);
					if({ :checkPunct(p: Punctuation:SEPARATOR) }, {
						:advance();
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
		local [ClassInfo] is classes: [];
		while({ !:check(kind: TokenKind:EOF, value: '') }, {
			if({ :atEnumHeader() }, {
				classes:push(item: :parseEnum());
			}, {
				classes:push(item: :parseClass());
			});
		});
		:linkNestedClasses(classes: classes);
		return ProgramNode(classes: classes);
	}

	## links nested classes to their enclosing
	## class — the qualified outer chain (outerName) and the parent link
	## (the outer appended to baseClasses), so the standard lattice walks
	## serve inner classes. Recurses through the nesting.
	##
	## @param classes: The classes at this nesting level.
	Function is linkNestedClasses([ClassInfo] is classes){
		local Int is ci: 0;
		while({ ci < classes:length() }, {
			local ClassInfo is c: classes:get(index: ci);
			local String is qualifiedOuter: c:name;
			if({ c:outerName != '' }, {
				qualifiedOuter: c:outerName . ':' . c:name;
			});
			while([Int is mi: 0], { mi < c:members:length() }, {
				local Member is m: c:members:get(index: mi);
				if({ m:kind == MemberKind:CLASS }, {
					m:nestedClass:setOuter(name: qualifiedOuter);
					m:nestedClass:baseClasses:push(item: c:name);
					:linkNestedClasses(classes: [m:nestedClass]);
				});
				mi++;
			});
			ci++;
		});
	}

	## True when the cursor sits on a class declaration header. `Class` is
	## not a keyword: it is the root class every declaration derives from,
	## so the header is recognized by its canonical class name.
	##
	## @return: true when the next tokens begin a class declaration.
	Function of Boolean is atClassHeader(){
		return :check(kind: TokenKind:IDENTIFIER, value: :names:classHeader());
	}

	## True when the cursor sits on an enum declaration header — same rule
	## as [atClassHeader]: `Enum` is the root class, recognized by name.
	##
	## @return: true when the next tokens begin an enum declaration.
	Function of Boolean is atEnumHeader(){
		return :check(kind: TokenKind:IDENTIFIER, value: :names:enumHeader());
	}

	## Parses the shared `when` arm block (between the braces). Used by both
	## Parses one class declaration: `Class of Parent is Name` with optional
	## post-name generic parameters.
	##
	## @return: The class descriptor.
	Function of ClassInfo is parseClass(){
		if({ :peek():getValue() == :names:legacyClassSpelling() }, {
			:addError(tok: :peek(), message: :errText:errObsoleteClassKeyword());
		});
		:advance();

		# Pre-binder `of`: parent classes.
		local [String] is baseClasses: [];
		if({ :checkKeyword(kw: Keyword:OF) }, {
			:advance();
			local Boolean is keepGoing: true;
			while({ keepGoing && !:checkPunct(p: Punctuation:BLOCK_OPEN) && !:check(kind: TokenKind:EOF, value: '') }, {
				local Token is tok: :advance();
				local String is base: tok:getValue();
				while({ :checkPunct(p: Punctuation:DEFAULT) }, {
					:advance();
					base: base . ':' . :advance():getValue();
				});
				baseClasses:push(item: base);
				if({ :checkPunct(p: Punctuation:SEPARATOR) }, {
					:advance();
				}, {
					keepGoing: false;
				});
			});
		});

		:matchKeyword(kw: Keyword:IS);
		local Token is nameTok: :advance();
		local String is name: nameTok:getValue();

		# Post-name `of`: generic type parameters.
		local [String] is typeParams: [];
		if({ :checkKeyword(kw: Keyword:OF) }, {
			:advance();
			local Token is tp1: :advance();
			typeParams:push(item: tp1:getValue());
			if({ :checkKeyword(kw: Keyword:TO) }, {
				:advance();
				local Token is tp2: :advance();
				typeParams:push(item: tp2:getValue());
			});
		});

		:matchPunct(p: Punctuation:BLOCK_OPEN);
		local [Member] is members: [];
		while({ !:checkPunct(p: Punctuation:BLOCK_CLOSE) && !:check(kind: TokenKind:EOF, value: '') }, {
			members:push(item: :parseMember());
		});
		:matchPunct(p: Punctuation:BLOCK_CLOSE);

		local ClassInfo is c: ClassInfo:init(name: name, baseClass: '', members: members);
		c:setLine(line: nameTok:getLine());
		c:setSourceFile(file: :sourceFile);
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
		if({ :checkKeyword(kw: Keyword:LOCAL) || :checkKeyword(kw: Keyword:CONTAINED) || :checkKeyword(kw: Keyword:REPLACE) || :checkKeyword(kw: Keyword:MERGE) || :checkKeyword(kw: Keyword:HELD) }, {
			return true;
		});
		if({ :atClassHeader() || :atEnumHeader() }, {
			return true;
		});
		if({ :peek():getValue() == :names:fnName() }, {
			return true;
		});
		if({ :checkPunct(p: Punctuation:BRACKET_OPEN) }, {
			return true;
		});

		local Boolean is isMember: false;

		# If next token is followed by '(':
		# Could be untyped method name(...) { or variant Name(...).
		if({ :peekAhead(offset: 1):getValue() == '(' }, {
			local Int is depth: 1;
			local Int is i: 2;
			local Boolean is searching: true;
			while({ searching }, {
				local Token is t: :peekAhead(offset: i);
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
							local Token is after: :peekAhead(offset: i + 1);
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
			local Token is tok: :peekAhead(offset: j);
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
		:advance();
		local String is backingType: :names:intName();
		if({ :checkKeyword(kw: Keyword:OF) }, {
			:advance();
			local Type is bt: :parseType();
			backingType: bt:name;
		});
		:matchKeyword(kw: Keyword:IS);
		local Token is nameTok: :advance();
		local String is name: nameTok:getValue();

		# Post-name `of`: generic type parameters over the tagged shape —
		# the same grammar as `Class is Box of T`. The pre-name `of` keeps
		# its meaning: the value-enum backing type.
		local [String] is enumTypeParams: [];
		if({ :checkKeyword(kw: Keyword:OF) }, {
			:advance();
			local Token is ep1: :advance();
			enumTypeParams:push(item: ep1:getValue());
			if({ :checkKeyword(kw: Keyword:TO) }, {
				:advance();
				local Token is ep2: :advance();
				enumTypeParams:push(item: ep2:getValue());
			});
		});

		:matchPunct(p: Punctuation:BLOCK_OPEN);

		local [Member] is members: [];
		local Int is count: 0;
		while({ !:checkPunct(p: Punctuation:BLOCK_CLOSE) && !:check(kind: TokenKind:EOF, value: '') }, {
			# Stray terminator between body members: shorthand metadata
			# (`namespace: [...]`) may end with ';' while the variant branch
			# consumes only separators — skip it rather than reading it as
			# a variant.
			if({ :checkPunct(p: Punctuation:TERMINATOR) }, {
				:advance();
			});
			if({ :atEnumMember() }, {
				members:push(item: :parseMember());
			}, {
				local Token is vTok: :advance();
				local String is vName: vTok:getValue();
				local [Parameter] is vParams: [];
				if({ :checkPunct(p: Punctuation:GROUP_OPEN) }, {
					:advance();
					vParams: :parseParams();
					:matchPunct(p: Punctuation:GROUP_CLOSE);
				});
				local Expression is valExpr: Expression:Unknown;
				local Boolean is hasInit: false;
				if({ :checkPunct(p: Punctuation:TAG) }, {
					:advance();
					valExpr: :parseExpression();
					hasInit: true;
				}, {
					valExpr: Expression:NumberLit(value: count, text: '' . count);
					hasInit: true;
				});
				count: count + 1;

				local Member is m: Member(kind: MemberKind:FIELD);
				m:setLine(line: vTok:getLine());
				m:modifiers: ['static', 'local'];
				m:memberType: Type(name: backingType);
				m:name: vName;
				m:params: vParams;
				m:initExpr: valExpr;
				m:hasInit: hasInit;
				members:push(item: m);

				if({ :checkPunct(p: Punctuation:SEPARATOR) }, {
					:advance();
				});
			});
		});
		:matchPunct(p: Punctuation:BLOCK_CLOSE);
		if({ :checkPunct(p: Punctuation:TERMINATOR) }, {
			:advance();
		});

		# every enum desugars to the class model —
		# value enums to held variants + the synthesized contract methods;
		# tagged enums to nested subclasses with real payload fields (the
		# desugar branches on the variant shapes).
		local EnumDesugar is ds: EnumDesugar:init();
		local ClassInfo is dc: ClassInfo:init(name: name, baseClass: :names:enumHeader(), members: members);
		dc:setTypeParams(params: enumTypeParams);
		local ClassInfo is desugared: ds:desugar(c: dc, backingType: backingType);
		members: desugared:members;

		local ClassInfo is c: ClassInfo:init(name: name, baseClass: :names:enumHeader(), members: members);
		c:setLine(line: nameTok:getLine());
		c:setSourceFile(file: :sourceFile);
		c:setTypeParams(params: enumTypeParams);
		c:withBaseClasses(name: name, baseClasses: [:names:enumHeader()], members: members);
		return c;
	}

	## Parses one class-body member: method, field, nested class, or
	## shorthand metadata property.
	##
	## @return: The member descriptor.
	Function of Member is parseMember(){
		local Int is startLine: :peek():getLine();
		local [String] is modifiers: [];
		while({ :checkKeyword(kw: Keyword:LOCAL) || :checkKeyword(kw: Keyword:CONTAINED) || :checkKeyword(kw: Keyword:REPLACE) || :checkKeyword(kw: Keyword:MERGE) || :checkKeyword(kw: Keyword:HELD) }, {
			local Token is tok: :advance();
			modifiers:push(item: tok:getValue());
		});

	if({ :atClassHeader() }, {
		local ClassInfo is nested: :parseClass();
		local Member is m: Member:init(kind: MemberKind:CLASS);
		m:setLine(line: startLine);
		# the member identifies its class — the unnamed member
		# matched other unnamed members in the override and registry walks.
		m:name: nested:name;
		m:nestedClass: nested;
		return m;
	});

	if({ :atEnumHeader() }, {
		local ClassInfo is edef: :parseEnum();
		local Member is m: Member:init(kind: MemberKind:CLASS);
		m:setLine(line: startLine);
		m:name: edef:name;
		m:nestedClass: edef;
		return m;
	});

		# Untyped (void) method: `name(params) { ... }`.
		if({ :peek():getTokenKind() == TokenKind:IDENTIFIER && :peekAhead(offset: 1):getValue() == Punctuation:GROUP_OPEN:value() }, {
			local Token is nameTok: :advance();
			local String is name: nameTok:getValue();
			:advance();

			local [Parameter] is params: :parseParams();
			:matchPunct(p: Punctuation:GROUP_CLOSE);
			local [Statement] is body: :parseMethodBody(params: params);

			local Member is m: Member:init(kind: MemberKind:METHOD);
			m:setLine(line: nameTok:getLine());
			m:modifiers: modifiers;
			m:memberType: Type:init(name: :names:voidMemberType());
			m:name: name;
			m:params: params;
			m:body: body;
			return m;
		});

		local Type is mType: :parseType();
		:matchKeyword(kw: Keyword:IS);
		local Token is nameTok: :advance();
		local String is name: nameTok:getValue();

		if({ :checkPunct(p: Punctuation:GROUP_OPEN) }, {
			:advance();
			local [Parameter] is params: :parseParams();
			:matchPunct(p: Punctuation:GROUP_CLOSE);
			# Interface-style declaration: a `;`-terminated signature with no
			# body — the sysinternal floor-binding form.
			if({ :checkPunct(p: Punctuation:TERMINATOR) }, {
				:advance();
				local Member is m: Member:init(kind: MemberKind:METHOD);
				m:setLine(line: nameTok:getLine());
				m:modifiers: modifiers;
				m:memberType: mType;
				m:name: name;
				m:params: params;
				return m;
			});
			local [Statement] is body: :parseMethodBody(params: params);

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
		local Expression is initExpr: Expression:Unknown;
		local Boolean is hasInit: false;
		if({ :checkPunct(p: Punctuation:ASSIGN) }, {
			:advance();
			initExpr: :parseExpression();
			hasInit: true;
		});
		:matchPunct(p: Punctuation:TERMINATOR);

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
	local Function of [Statement] is parseMethodBody([Parameter] is params){
		:matchPunct(p: Punctuation:BLOCK_OPEN);
		local [Statement] is body: [];
		local Int is pi: 0;
		while({ pi < params:length() }, {
			local Parameter is p: params:get(index: pi);
			if({ p:paramType:name == :names:selfFieldMarker() }, {
				local Expression is lhs: Expression:Path(segments: [:names:selfIdent(), p:name]);
				local Expression is rhs: Expression:Ident(name: p:name);
				local Statement is assignS: Statement:Assign(assignTarget: lhs, assignValue: rhs);
				body:push(item: assignS);
			});
			pi++;
		});
		while({ !:checkPunct(p: Punctuation:BLOCK_CLOSE) && !:check(kind: TokenKind:EOF, value: '') }, {
			body:push(item: :parseStatement());
		});
		:matchPunct(p: Punctuation:BLOCK_CLOSE);
		return body;
	}

	## Parses one type reference: a base name with optional `of`/`to`
	## generic arguments, or a bracketed list literal type.
	##
	## @return: The type descriptor.
	Function of Type is parseType(){
		if({ :checkPunct(p: Punctuation:BRACKET_OPEN) }, {
			:advance();
			local Type is elem: :parseType();
			:matchPunct(p: Punctuation:BRACKET_CLOSE);
			local Type is lnode: Type(name: :names:listName());
			lnode:params: [elem];
			return lnode;
		});
		local Token is baseTok: :advance();
		local String is typeName: baseTok:getValue();

		# the qualified nested-class reference —
		# `Outer:Inner` chains consume the glued colon segments into the
		# type name, so declaration positions can spell the full path.
		while({ :checkPunct(p: Punctuation:ACCESSOR) && :hasWhitespaceAfter(offset: 0) == false && :peekAhead(offset: 1):getTokenKind() == TokenKind:IDENTIFIER }, {
			:advance();
			local Token is segTok: :advance();
			typeName: typeName . ':' . segTok:getValue();
		});

		if({ :checkKeyword(kw: Keyword:OF) }, {
			:advance();
			local [Type] is params: [];
			params:push(item: :parseType());

			if({ :checkKeyword(kw: Keyword:TO) }, {
				:advance();
				params:push(item: :parseType());
			});

			local Type is node: Type(name: typeName);
			node:params: params;
			return node;
		});

		return Type:init(name: typeName);
	}

	## Parses one statement.
	##
	local Function of Boolean is isForwardStatementStart(){
		if({ !:checkPunct(p: Punctuation:GROUP_OPEN) }, {
			return false;
		});
		local Int is depth: 0;
		local Int is off: 0;
		while({ true }, {
			local Token is tok: :peekAhead(offset: off);
			local String is val: tok:getValue();
			if({ tok:getTokenKind() == TokenKind:EOF }, {
				return false;
			});
			if({ val == Punctuation:GROUP_OPEN:value() }, {
				depth++;
			}, {
				if({ val == Punctuation:GROUP_CLOSE:value() }, {
					depth--;
					if({ depth == 0 }, {
						local Token is afterTok: :peekAhead(offset: off + 1);
						local String is afterVal: afterTok:getValue();
						return afterVal == Punctuation:TERMINATOR:value() || afterVal == Punctuation:BLOCK_CLOSE:value();
					});
				});
			});
			off++;
		});
		return false;
	}

	## @return: The statement node.
	Function of Statement is parseStatement(){
		local Int is startLine: :peek():getLine();

		# Merge-forward statement: `(arg, name: arg, ...)`.
		if({ :isForwardStatementStart() }, {
			return :parseForwardStatement(startLine: startLine);
		});

		# Scoped callback statement: `as: call;` or `as (params): call;`.
		if({ :checkKeyword(kw: Keyword:AS) }, {
			return :parseAsStatement(startLine: startLine);
		});

		if({ :atClassHeader() }, {
			local ClassInfo is cls: :parseClass();
			local Statement is s: Statement:ClassDecl(nestedClass: cls);
			s:setLine(line: startLine);
			return s;
		});

		if({ :atEnumHeader() }, {
			local ClassInfo is edef: :parseEnum();
			local Statement is s: Statement:ClassDecl(nestedClass: edef);
			s:setLine(line: startLine);
			return s;
		});


		if({ :checkKeyword(kw: Keyword:RETURN) }, {
			:advance();
			if({ :checkKeyword(kw: Keyword:AS) }, {
				local Statement is asStmt: :parseAsStatement(startLine: startLine);
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
			if({ !:checkPunct(p: Punctuation:TERMINATOR) }, {
				retExpr: :parseExpression();
				hasExpr: true;
			});
			:matchPunct(p: Punctuation:TERMINATOR);

			local Statement is s: Statement:Return(returnExpr: retExpr, hasReturnExpr: hasExpr);
			s:setLine(line: startLine);
			return s;
		});

		if({ :checkKeyword(kw: Keyword:LOCAL) }, {
			:advance();
			local Type is vType: :parseType();
			:matchKeyword(kw: Keyword:IS);
			local Token is nameTok: :advance();
			local String is name: nameTok:getValue();

			local Expression is initExpr: Expression:Unknown;
			local Boolean is hasInit: false;
			if({ :checkPunct(p: Punctuation:ASSIGN) }, {
				:advance();
				initExpr: :parseExpression();
				hasInit: true;
			});
			:matchPunct(p: Punctuation:TERMINATOR);

			local Statement is s: Statement:VarDecl(modifiers: ['local'], varType: vType, varName: name, initExpr: initExpr, hasInit: hasInit);
			s:setLine(line: startLine);
			return s;
		});

		# Expression or assignment: `target: value;` assigns, anything else
		# evaluates for effect.
		local Expression is expr: :parseExpression();

		if({ :checkPunct(p: Punctuation:ASSIGN) }, {
			:advance();
			local Expression is val: :parseExpression();
			:matchPunct(p: Punctuation:TERMINATOR);

			local Statement is s: Statement:Assign(assignTarget: expr, assignValue: val);
			s:setLine(line: startLine);
			return s;
		});

		if({ !:checkPunct(p: Punctuation:BLOCK_CLOSE) }, {
			:matchPunct(p: Punctuation:TERMINATOR);
		});
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
		:advance();
		local [NamedArg] is args: :parseArgs();
		:matchPunct(p: Punctuation:GROUP_CLOSE);
		if({ :checkPunct(p: Punctuation:TERMINATOR) }, {
			:advance();
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
		:advance();
		local [Parameter] is params: [];
		local Boolean is hasParams: false;
		if({ :checkPunct(p: Punctuation:GROUP_OPEN) }, {
			:advance();
			hasParams: true;
			params: :parseParams();
			:matchPunct(p: Punctuation:GROUP_CLOSE);
		});
		local Type is returnType: Type:init(name: :names:voidName());
		if({ :checkKeyword(kw: Keyword:OF) }, {
			:advance();
			returnType: :parseType();
		});
		if({ :checkPunct(p: Punctuation:ACCESSOR) }, {
			:advance();
		}, {
			if({ !hasParams }, {
				:matchPunct(p: Punctuation:ACCESSOR);
			});
		});
		local Expression is callExpr: :parseExpression();
		:matchPunct(p: Punctuation:TERMINATOR);

		local [Statement] is closureBody: [];
		while({ !:checkPunct(p: Punctuation:BLOCK_CLOSE) && !:check(kind: TokenKind:EOF, value: '') }, {
			closureBody:push(item: :parseStatement());
		});

		local Expression is anonFn: Expression:AnonFn(returnType: returnType, params: params, body: closureBody);

		local CallData is cd: match(on: callExpr, when: [
			Expression:Call: local Function of CallData(CallData is call){ return call; },
			else: {
				local [NamedArg] is emptyArgs: [];
				local CallData is created: match(on: callExpr, when: [
					Expression:FieldAccess: local Function of CallData(Expression is target, String is fieldName){
						return CallData(target: target, name: fieldName, args: emptyArgs);
					},
					Expression:Ident: local Function of CallData(String is name){
						local CallData is bareCd: CallData(target: Expression:Ident(name: :names:selfIdent()), name: name, args: emptyArgs);
						bareCd:isBareCall: true;
						return bareCd;
					},
					else: {
						CallData(target: callExpr, name: '', args: emptyArgs)
					}
				]);
				callExpr: Expression:Call(call: created);
				created
			}
		]);

		cd:args:push(item: NamedArg(name: '', value: anonFn));
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
		return :parseLevel(level: PrecedenceLevel:LOGICAL_OR);
	}

	## Parses one binary precedence level via the parameterized fold loop.
	##
	## @param level: The level to fold.
	## @return: The folded expression.
	Function of Expression is parseLevel(PrecedenceLevel is level){
		return match(on: level, when: [
			PrecedenceLevel:MULTIPLICATIVE: { :foldBinary(ops: Array(['*', '/', '%']), next: PrecedenceLevel:NONE) },
			PrecedenceLevel:ADDITIVE: { :foldBinary(ops: Array(['+', '-']), next: PrecedenceLevel:MULTIPLICATIVE) },
			PrecedenceLevel:SHIFT: { :foldBinary(ops: Array(['<<', '>>']), next: PrecedenceLevel:ADDITIVE) },
			PrecedenceLevel:CONCAT: { :foldBinary(ops: Array(['.']), next: PrecedenceLevel:SHIFT) },
			PrecedenceLevel:RELATIONAL: { :foldBinary(ops: Array(['<', '<=', '>', '>=']), next: PrecedenceLevel:CONCAT) },
			PrecedenceLevel:EQUALITY: { :foldBinary(ops: Array(['==', '!=', 'is']), next: PrecedenceLevel:RELATIONAL) },
			PrecedenceLevel:BIT_AND: { :foldBinary(ops: Array(['&']), next: PrecedenceLevel:EQUALITY) },
			PrecedenceLevel:BIT_XOR: { :foldBinary(ops: Array(['^']), next: PrecedenceLevel:BIT_AND) },
			PrecedenceLevel:BIT_OR: { :foldBinary(ops: Array(['|']), next: PrecedenceLevel:BIT_XOR) },
			PrecedenceLevel:LOGICAL_AND: { :foldBinary(ops: Array(['&&']), next: PrecedenceLevel:BIT_OR) },
			PrecedenceLevel:LOGICAL_OR: { :foldBinary(ops: Array(['||']), next: PrecedenceLevel:LOGICAL_AND) },
			PrecedenceLevel:NONE: { :parseUnary() }
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
			left: :parseUnary();
		}, {
			left: :parseLevel(level: next);
		});
		while({ ops:indexOf(search: :peek():getValue(), default: -1) >= 0 }, {
			local Token is opTok: :advance();
			local String is op: opTok:getValue();
			if({ op == Keyword:IS:value() }, {
				op: '==';
			});
			local Expression is right: Expression:Unknown;
			if({ next == PrecedenceLevel:NONE }, {
				right: :parseUnary();
			}, {
				right: :parseLevel(level: next);
			});
			# Real-syntax binaries carry the operator token's line —
			# lint rules key source lines off it. The template-string
			# desugar's synthetic concat chains stay line-0 (exempt).
			local Expression is bin: Expression:Binary(op: op, left: left, right: right);
			bin:setLine(line: opTok:getLine());
			left: bin;
		});
		return left;
	}

	## Parses unary operators (~, -, !) or descends to casts.
	##
	## @return: The expression node.
	Function of Expression is parseUnary(){
		local String is op: match(when: [
			{ :checkSymbol(value: '++') }: { '++' },
			{ :checkSymbol(value: '--') }: { '--' },
			{ :checkSymbol(value: '~') }: { '~' },
			{ :checkSymbol(value: '-') }: { '-' },
			{ :checkSymbol(value: '!') }: { '!' },
			else: { '' }
		]);
		if({ op == '' }, {
			return :parseAs();
		});
		:advance();
		local Expression is expr: :parseUnary();
		return Expression:Unary(op: op, operand: expr);
	}

	## Parses the instance-import form `as ClassName(args)` — a using-entry
	## terminator (§2.1). Arguments must be direct literal
	## values (E1); parentheses are required so the form can
	## never be confused with the postfix cast.
	##
	## @return: The USING_AS expression node.
	Function of Expression is parseUsingAs(){
		:advance();
		local Token is clsTok: :peek();
		if({ clsTok:getTokenKind() != TokenKind:IDENTIFIER }, {
			:addError(tok: clsTok, message: :errText:errUsingAsRequiresClass());
			return Expression:Unknown;
		});
		:advance();
		local String is clsName: clsTok:getValue();
		local [NamedArg] is args: [];
		if({ :checkPunct(p: Punctuation:GROUP_OPEN) }, {
			:advance();
			if({ !:checkPunct(p: Punctuation:GROUP_CLOSE) }, {
				args: :parseArgs();
				local Int is ai: 0;
				while({ ai < args:length() }, {
					local NamedArg is arg: args:get(index: ai);
					local Boolean is isLiteral: match(on: arg:value, when: [
						Expression:StringLit: local Function of Boolean(String is value){ return true; },
						Expression:NumberLit: local Function of Boolean(Int is value, String is text){ return true; },
						Expression:FloatLit: local Function of Boolean(String is text){ return true; },
						Expression:BoolLit: local Function of Boolean(Boolean is value){ return true; },
						else: { false }
					]);
					if({ !isLiteral }, {
						:addError(tok: clsTok, message: :errText:errInstanceImportLiteralArgs());
					});
					ai++;
				});
			});
			:matchPunct(p: Punctuation:GROUP_CLOSE);
		}, {
			:addError(tok: clsTok, message: :errText:errInstanceImportParens(target: clsName));
		});
		local String is alias: '';
		if({ :checkKeyword(kw: Keyword:IS) }, {
			:advance();
			local Token is aliasTok: :peek();
			if({ aliasTok:getTokenKind() != TokenKind:IDENTIFIER }, {
				:addError(tok: aliasTok, message: 'Instance-import alias after \'is\' must be an identifier.');
				return Expression:Unknown;
			});
			:advance();
			alias: aliasTok:getValue();
		});
		local Expression is node: Expression:UsingAs(className: clsName, args: args);
		node:usingAsAlias: alias;
		return node;
	}

	## Parses a type cast: `value as Target` or `value as Target(width)`.
	## Binding is tighter than every binary operator; chaining
	## (`x as A as B`) is rejected.
	##
	## @return: The expression node.
	Function of Expression is parseAs(){
		local Expression is left: :parsePostfix();
		if({ :checkKeyword(kw: Keyword:AS) }, {
			:advance();
			local Token is targetTok: :advance();
			local [Expression] is args: [];
			if({ :checkPunct(p: Punctuation:GROUP_OPEN) }, {
				:advance();
				if({ !:checkPunct(p: Punctuation:GROUP_CLOSE) }, {
					args:push(item: :parseExpression());
				});
				:matchPunct(p: Punctuation:GROUP_CLOSE);
			});
			if({ :checkKeyword(kw: Keyword:AS) }, {
				:addError(tok: :peek(), message: :errText:errChainedAsUnsupported());
			});
			return Expression:Cast(inner: left, target: targetTok:getValue(), args: args);
		});
		return left;
	}

	## Returns whether the next token starts a postfix operator or access.
	Function of Boolean is atPostfix(){
		if({ :checkPunct(p: Punctuation:GROUP_OPEN) || :checkPunct(p: Punctuation:BRACKET_OPEN) || :checkSymbol(value: '++') || :checkSymbol(value: '--') }, {
			return true;
		});
		if({ :checkPunct(p: Punctuation:ACCESSOR) }, {
			# Whitespace before ':' means assignment context, not a path.
			if({ :hasWhitespaceAfter(offset: 0) }, {
				return false;
			});
			local Token is nextTok: :peekAhead(offset: 1);
			return nextTok:getTokenKind() == TokenKind:IDENTIFIER || nextTok:getTokenKind() == TokenKind:KEYWORD || nextTok:getValue() == :names:wildcard();
		});
		return false;
	}

	## Parses postfix trailers (calls, indexes, colon-paths) after a
	## primary expression.
	##
	## @return: The expression node.
	Function of Expression is parsePostfix(){
		local Expression is currentExpr: :parsePrimary();
		while({ :atPostfix() }, {
			match(when: [
				{ :checkPunct(p: Punctuation:GROUP_OPEN) }: {
					:advance();
					local [NamedArg] is args: :parseArgs();
					:matchPunct(p: Punctuation:GROUP_CLOSE);

					local CallData is cd: match(on: currentExpr, when: [
						Expression:Ident: local Function of CallData(String is name){
							if({ name == 'Loops' }, {
								return CallData:init(target: currentExpr, name: 'loop', args: args);
							});
							local CallData is bareCd: CallData:init(target: Expression:Ident(name: :names:selfIdent()), name: name, args: args);
							bareCd:isBareCall: true;
							return bareCd;
						},
						else: {
							CallData:init(target: currentExpr, name: '', args: args)
						}
					]);
					currentExpr: Expression:Call(call: cd);
				},
				{ :checkPunct(p: Punctuation:BRACKET_OPEN) }: {
					:advance();
					local Expression is idxExpr: :parseExpression();
					:matchPunct(p: Punctuation:BRACKET_CLOSE);

					currentExpr: Expression:Index(target: currentExpr, index: idxExpr);
				},
				{ :checkSymbol(value: '++') }: {
					:advance();
					currentExpr: Expression:Unary(op: 'post++', operand: currentExpr);
				},
				{ :checkSymbol(value: '--') }: {
					:advance();
					currentExpr: Expression:Unary(op: 'post--', operand: currentExpr);
				},
				{ :checkPunct(p: Punctuation:ACCESSOR) }: {
					:advance();
					local Token is mTok: :advance();
					local String is method: mTok:getValue();

					if({ :checkPunct(p: Punctuation:GROUP_OPEN) }, {
						:advance();
						local [NamedArg] is args: :parseArgs();
						:matchPunct(p: Punctuation:GROUP_CLOSE);

						currentExpr: Expression:Call(call: CallData:init(target: currentExpr, name: method, args: args));
					}, {
						local Boolean is isPathOrIdent: match(on: currentExpr, when: [
							Expression:Path: local Function of Boolean([String] is segments){ return true; },
							Expression:Ident: local Function of Boolean(String is name){ return true; },
							else: { false }
						]);
						if({ !isPathOrIdent }, {
							currentExpr: Expression:FieldAccess(target: currentExpr, fieldName: method);
						}, {
							local [String] is segs: [];
							match(on: currentExpr, when: [
								Expression:Path: local Function([String] is segments){
									each(list: segments, action: local Function(String is s){
										segs:push(item: s);
									});
								},
								Expression:Ident: local Function(String is name){
									segs:push(item: name);
								},
								else: {}
							]);
							segs:push(item: method);
							currentExpr: Expression:Path(segments: segs);
						});
					});
				},
				else: {}
			]);
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
		if({ :checkKeyword(kw: Keyword:LOCAL) && :peekAhead(offset: 1):getValue() == :names:fnName() }, {
			isAnonFn: true;
		});
		if({ :peek():getValue() == :names:fnName() && (:peekAhead(offset: 1):getValue() == Punctuation:GROUP_OPEN:value() || :peekAhead(offset: 1):getValue() == Keyword:OF:value()) }, {
			isAnonFn: true;
		});

		if({ isAnonFn }, {
			if({ :checkKeyword(kw: Keyword:LOCAL) }, {
				:advance();
			});
			:advance();
			local Type is returnType: Type:init(name: :names:voidName());
			if({ :checkKeyword(kw: Keyword:OF) }, {
				:advance();
				returnType: :parseType();
			});
			:matchPunct(p: Punctuation:GROUP_OPEN);
			local [Parameter] is params: :parseParams();
			:matchPunct(p: Punctuation:GROUP_CLOSE);
			local [Statement] is body: :parseMethodBody(params: params);

			return Expression:AnonFn(returnType: returnType, params: params, body: body);
		});


		local Token is tok: :peek();

		return match(on: tok:getTokenKind(), when: [
			TokenKind:STRING: {
				:advance();
				Expression:StringLit(value: tok:getValue()) as Expression
			},
			TokenKind:RAWSTRING: {
				:advance();
				Expression:StringLit(value: tok:getValue()) as Expression
			},
			TokenKind:TEMPLATESTRING: {
				:advance();
				:expandFancyString(raw: tok:getValue(), originTok: tok, depth: :templateDepth)
			},
			TokenKind:INT: {
				:advance();
				Expression:NumberLit(value: 0, text: tok:getValue()) as Expression
			},
			TokenKind:FLOAT: {
				:advance();
				Expression:FloatLit(text: tok:getValue()) as Expression
			},
			TokenKind:BOOL: {
				:advance();
				Expression:BoolLit(value: tok:getValue() == :names:boolTrue()) as Expression
			},
			TokenKind:IDENTIFIER: {
				:advance();
				Expression:Ident(name: tok:getValue()) as Expression
			},
			TokenKind:KEYWORD: {
				# Expression-initial `as` is the instance-import form
				# `as ClassName()` (§2.1); `as` never begins any
				# other expression (casts are postfix, scoped regions are
				# statement-initial).
				if({ :checkKeyword(kw: Keyword:AS) }, {
					return :parseUsingAs();
				});
				:addError(tok: tok, message: :errText:errUnexpectedTokenInExpression(token: tok:getValue()));
				:advance();
				Expression:Unknown
			},
			else: {
				if({ :checkPunct(p: Punctuation:GROUP_OPEN) }, {
					:advance();
					local Expression is inner: :parseExpression();
					:matchPunct(p: Punctuation:GROUP_CLOSE);
					return inner;
				});

				if({ :checkPunct(p: Punctuation:BRACKET_OPEN) }, {
					return :parseArrayOrMap();
				});

				if({ :checkPunct(p: Punctuation:BLOCK_OPEN) }, {
					return :parseFunctionBlock();
				});

				if({ :checkPunct(p: Punctuation:ACCESSOR) }, {
					local Token is nextTok: :peekAhead(offset: 1);
					local Boolean is isMemberStart: !:hasWhitespaceAfter(offset: 0) && (nextTok:getTokenKind() == TokenKind:IDENTIFIER || nextTok:getTokenKind() == TokenKind:KEYWORD || nextTok:getValue() == :names:wildcard());
					if({ !isMemberStart }, {
						:advance();
					});
					return Expression:Ident(name: :names:selfIdent());
				});

				:addError(tok: tok, message: :errText:errUnexpectedTokenInExpression(token: tok:getValue()));
				:advance();
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
		local Token is firstTok: :peekAhead(offset: 1);
		if({ firstTok:getTokenKind() == TokenKind:KEYWORD && firstTok:getValue() == Keyword:AS:value() }, {
			return false;
		});
		local Int is offset: 1;
		local Int is depth: 0;
		local Boolean is running: true;
		local Boolean is foundIs: false;
		while({ running }, {
			local Token is t: :peekAhead(offset: offset);
			local TokenKind is tk: t:getTokenKind();
			local String is v: t:getValue();
			if({ tk == TokenKind:EOF }, {
				running: false;
			}, {
				if({ tk != TokenKind:STRING }, {
					if({ depth == 0 && (v == ']' || v == ',' || v == ';') }, {
						running: false;
					}, {
						if({ v == '(' || v == '[' || v == '{' }, {
							depth: depth + 1;
						}, {
							if({ v == ')' || v == ']' || v == '}' }, {
								depth: depth - 1;
							}, {
								if({ depth == 0 && tk == TokenKind:KEYWORD && v == Keyword:IS:value() }, {
									foundIs: true;
									running: false;
								});
							});
						});
					});
				});
				if({ running }, {
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
		:matchPunct(p: Punctuation:BRACKET_OPEN);
		local [Parameter] is params: [];
		local Boolean is keepGoing: true;
		while({ keepGoing && !:checkPunct(p: Punctuation:BRACKET_CLOSE) && !:check(kind: TokenKind:EOF, value: '') }, {
			local Type is pType: :parseType();
			:matchKeyword(kw: Keyword:IS);
			local Token is nameTok: :advance();
			local Parameter is p: Parameter(name: nameTok:getValue(), paramType: pType);
			if({ :checkPunct(p: Punctuation:ASSIGN) }, {
				:advance();
				p:setDefault(expr: :parseExpression());
			});
			params:push(item: p);
			if({ :checkPunct(p: Punctuation:SEPARATOR) }, {
				:advance();
			}, {
				keepGoing: false;
			});
		});
		:matchPunct(p: Punctuation:BRACKET_CLOSE);
		local [Statement] is emptyBody: [];
		return Expression:AnonFn(returnType: Type(name: ''), params: params, body: emptyBody);
	}

	## Parses a function block shorthand `{ ... }` as an anonymous function.
	## Statements built here carry their source line: the shorthand bodies
	## are where user code actually lives (loop/branch arms), and both the
	## checker's diagnostics and the debug emission's #line directives
	## read Statement:line.
	##
	## @return: The ANON_FN expression.
	Function of Expression is parseFunctionBlock(){
		:matchPunct(p: Punctuation:BLOCK_OPEN);
		local [Statement] is body: [];
		local [Parameter] is params: [];
		local Type is returnType: Type(name: :names:voidName());

		while({ !:checkPunct(p: Punctuation:BLOCK_CLOSE) && !:check(kind: TokenKind:EOF, value: '') }, {
			local Int is stmtLine: :peek():getLine();
			if({ !:checkKeyword(kw: Keyword:RETURN) && !:checkKeyword(kw: Keyword:LOCAL) && !:checkKeyword(kw: Keyword:AS) }, {
				local Expression is expr: :parseExpression();
				if({ :checkPunct(p: Punctuation:ASSIGN) }, {
					:advance();
					local Expression is val: :parseExpression();
					:matchPunct(p: Punctuation:TERMINATOR);
					local Statement is s: Statement:Assign(assignTarget: expr, assignValue: val);
					s:setLine(line: stmtLine);
					body:push(item: s);
				}, {
					if({ :checkPunct(p: Punctuation:BLOCK_CLOSE) }, {
						local Statement is retS: Statement:Return(returnExpr: expr, hasReturnExpr: true);
						retS:setLine(line: stmtLine);
						body:push(item: retS);
					}, {
						:matchPunct(p: Punctuation:TERMINATOR);
						local Statement is exprS: Statement:Expr(exprStmt: expr);
						exprS:setLine(line: stmtLine);
						body:push(item: exprS);
					});
				});
			}, {
				body:push(item: :parseStatement());
			});
		});
		:matchPunct(p: Punctuation:BLOCK_CLOSE);

		return Expression:AnonFn(returnType: returnType, params: params, body: body);
	}

	## Parses a bracketed `[...]` literal: array, map, or their empty
	## forms (distinguished by `:]` for an empty map).
	##
	## @return: The ARRAY or MAP node.
	Function of Expression is parseArrayOrMap(){
		if({ :isDeclListStart() }, {
			return :parseDeclList();
		});
		:advance();
		if({ :checkPunct(p: Punctuation:BRACKET_CLOSE) }, {
			:advance();
			local [Expression] is emptyItems: [];
			return Expression:ArrayLit(items: emptyItems);
		});
		if({ :checkPunct(p: Punctuation:PAIR) && :peekAhead(offset: 1):getValue() == Punctuation:BRACKET_CLOSE:value() }, {
			:advance();
			:matchPunct(p: Punctuation:BRACKET_CLOSE);
			local [Expression] is emptyKeys: [];
			local [Expression] is emptyVals: [];
			return Expression:MapLit(keys: emptyKeys, values: emptyVals);
		});
		local Expression is firstItem: :parseExpression();
		if({ :checkPunct(p: Punctuation:PAIR) }, {
			:advance();
			local Expression is firstVal: :parseExpression();
			local [Expression] is mKeys: [firstItem];
			local [Expression] is mVals: [firstVal];
			if({ :checkPunct(p: Punctuation:SEPARATOR) }, {
				:advance();
				local Boolean is keepGoing: true;
				while({ keepGoing && !:checkPunct(p: Punctuation:BRACKET_CLOSE) && !:check(kind: TokenKind:EOF, value: '') }, {
					local Expression is k: :parseExpression();
					:matchPunct(p: Punctuation:PAIR);
					local Expression is v: :parseExpression();
					mKeys:push(item: k);
					mVals:push(item: v);
					if({ :checkPunct(p: Punctuation:SEPARATOR) }, {
						:advance();
					}, {
						keepGoing: false;
					});
				});
			});
			:matchPunct(p: Punctuation:BRACKET_CLOSE);
			return Expression:MapLit(keys: mKeys, values: mVals);
		});
		local [Expression] is items: [firstItem];
		if({ :checkPunct(p: Punctuation:SEPARATOR) }, {
			:advance();
			local Boolean is keepGoing: true;
			while({ keepGoing && !:checkPunct(p: Punctuation:BRACKET_CLOSE) && !:check(kind: TokenKind:EOF, value: '') }, {
				items:push(item: :parseExpression());
				if({ :checkPunct(p: Punctuation:SEPARATOR) }, {
					:advance();
				}, {
					keepGoing: false;
				});
			});
		});
		:matchPunct(p: Punctuation:BRACKET_CLOSE);
		return Expression:ArrayLit(items: items);
	}

	## Next byte position in `raw` after `expandUnicodeEscape` completes.
	local Int is unicodeEscEndPos: 0;

	## Maps a hex character to 0..15, or -1 if not hex.
	local Function of Int is hexDigitVal(String is ch){
		if({ ch:length() == 0 }, { return -1; });
		local Int is b: ch:charCodeAt(index: 0, default: -1);
		if({ b >= 48 && b <= 57 }, { return b - 48; });
		if({ b >= 97 && b <= 102 }, { return b - 97 + 10; });
		if({ b >= 65 && b <= 70 }, { return b - 65 + 10; });
		return -1;
	}

	## Parses and expands a `\uXXXX` or `\u{...}` escape starting immediately
	## after `\u` at [uPos] in [raw], setting `:unicodeEscEndPos` to the new
	## position in [raw] and reporting a parser error on [originTok] if invalid.
	local Function of String is expandUnicodeEscape(String is raw, Int is uPos, Token is originTok){
		local Int is rlen: raw:length();
		if({ uPos >= rlen }, {
			:unicodeEscEndPos: uPos;
			:addError(tok: originTok, message: "Invalid Unicode escape: expected 4 hex digits (\\uXXXX) or braced hex (\\u{...}).");
			return '';
		});
		local String is first: raw:charAt(index: uPos, default: '');
		if({ first == '{' }, {
			local Int is p: uPos + 1;
			local Int is digits: 0;
			local Int is val: 0;
			local Boolean is closed: false;
			local Boolean is badChar: false;
			while({ p < rlen && !closed && !badChar }, {
				local String is ch: raw:charAt(index: p, default: '');
				if({ ch == '}' }, {
					closed: true;
					p: p + 1;
				}, {
					local Int is d: :hexDigitVal(ch: ch);
					if({ d < 0 }, {
						badChar: true;
					}, {
						digits: digits + 1;
						if({ digits <= 6 }, {
							val: (val * 16) + d;
						});
						p: p + 1;
					});
				});
			});
			:unicodeEscEndPos: p;
			if({ !closed || badChar || digits == 0 || digits > 6 }, {
				:addError(tok: originTok, message: "Invalid Unicode escape: \\u{...} requires 1 to 6 hexadecimal digits.");
				return '';
			});
			if({ val > 1114111 }, {
				:addError(tok: originTok, message: "Invalid Unicode escape: code point exceeds maximum U+10FFFF.");
				return '';
			});
			if({ val >= 55296 && val <= 57343 }, {
				:addError(tok: originTok, message: "Invalid Unicode escape: lone surrogate code points (U+D800..U+DFFF) are not valid Unicode scalar values.");
				return '';
			});
			return String:fromCodePoint(code: val);
		});
		if({ uPos + 4 > rlen }, {
			:unicodeEscEndPos: rlen;
			:addError(tok: originTok, message: "Invalid Unicode escape: \\uXXXX requires 4 hexadecimal digits.");
			return '';
		});
		local Int is val4: 0;
		local Int is k: 0;
		local Boolean is ok4: true;
		while({ k < 4 }, {
			local Int is d: :hexDigitVal(ch: raw:charAt(index: uPos + k, default: ''));
			if({ d < 0 }, {
				ok4: false;
			}, {
				val4: (val4 * 16) + d;
			});
			k: k + 1;
		});
		:unicodeEscEndPos: uPos + 4;
		if({ !ok4 }, {
			:addError(tok: originTok, message: "Invalid Unicode escape: \\uXXXX requires 4 hexadecimal digits.");
			return '';
		});
		if({ val4 >= 55296 && val4 <= 57343 }, {
			:addError(tok: originTok, message: "Invalid Unicode escape: lone surrogate code points (U+D800..U+DFFF) are not valid Unicode scalar values.");
			return '';
		});
		return String:fromCodePoint(code: val4);
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
						if({ nextCh == 'u' }, {
							dRes: dRes . :expandUnicodeEscape(raw: raw, uPos: dPos, originTok: originTok);
							dPos: :unicodeEscEndPos;
						}, {
							dRes: dRes . esc:expand(escaped: nextCh);
						});
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
		local Array of String is lits: Array();
		local String is hole: '';
		local Array of String is holes: Array();
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
							if({ nextCh == 'u' }, {
								lit: lit . :expandUnicodeEscape(raw: raw, uPos: sPos + 2, originTok: originTok);
								sPos: :unicodeEscEndPos;
							}, {
								lit: lit . esc:expand(escaped: nextCh);
								sPos: sPos + 2;
							});
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
			:addError(tok: originTok, message: :errText:errUnterminatedTemplateHole());
			return Expression:StringLit(value: '');
		});
		local Expression is acc: Expression:StringLit(value: lits:get(index: 0));
		if({ holes:length() == 0 }, {
			return acc;
		});

		local Int is k: 0;
		repeat(count: holes:length(), worker: {
			local Expression is holeE: :parseTemplateExpression(text: holes:get(index: k));
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
			:addError(tok: :peek(), message: :errText:errEmptyTemplateExpression());
			return emptyE;
		});
		local Lexer is subLexer: Lexer:init(source: text);
		local [Token] is subTokens: subLexer:tokenize();
		if({ subLexer:hasErrors() }, {
			:addError(tok: :peek(), message: :errText:errInvalidTemplateExpression());
			return emptyE;
		});
		local Parser is subParser: Parser:init(tokens: subTokens);
		subParser:setTemplateDepth(depth: 1);
		local Expression is e: subParser:parseExpression();
		if({ subParser:hasErrors() || subParser:peek():getTokenKind() != TokenKind:EOF }, {
			:addError(tok: :peek(), message: :errText:errInvalidTemplateExpression());
			return emptyE;
		});
		return e;
	}
}
