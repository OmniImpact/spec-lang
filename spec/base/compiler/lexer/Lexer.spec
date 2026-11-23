#! Package base:compiler:lexer
#! Turns Spec source text into a token stream.
##
## The scanner is pure and position-driven: it holds the source, a cursor,
## and line/col tracking, and produces [Token] values ending with EOF.
## Scan work runs in private [Loop] classes (one concern each); the public
## surface is `init` + `tokenize` + the error accessors. String families
## follow the language's two-family rule: raw ('...' and ''') keep bytes
## exactly as written (minimal quote escapes for single quotes); the fancy
## family ("..." and ```) is scanned raw here and interpreted later by the
## parser's template desugar.
##
## Reported errors are [Error] values carrying provenance; message
## wordings come from an [ErrorText] instance the lexer owns (a lexer uses
## a vocabulary, it is not one).

Class is Lexer{
	replace Array of String is namespace: ['base', 'compiler', 'lexer'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'utils', Chars],
		['base', 'compiler', 'lexer', Token],
		['base', 'compiler', 'lexer', TokenKind],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'compiler', WellKnown],
		['base', 'compiler', 'lexer', Operator],
		['base', 'compiler', Error],
		['base', 'compiler', ErrorText],
		['base', 'sys', as Reflection()],
		['base', 'iterator'],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	## The full source text being scanned. Public because the scan loops
	## are collaborators that drive the cursor; lifecycle stays with the
	## lexer.
	Str is source: '';

	## Source length, cached to keep loop guards cheap.
	Int is length: 0;

	## Byte cursor into [source].
	Int is pos: 0;

	## One-based line of the cursor.
	Int is line: 1;

	## One-based column of the cursor.
	Int is col: 1;

	## Lexical errors, in scan order.
	local [Error] is errors: [];

	## Well-known names.
	local WellKnown is names: WellKnown:init();

	## Stateless character classification (letters, digits, case). Public
	## for the same reason as the cursor: the digit scan loops consult it.
	Chars is chars: Chars:init();

	## Message wordings, owned by composition.
	local ErrorText is errText: ErrorText:init();

	## Initializes a lexer over the given source text.
	##
	## @param source: Spec source code to tokenize.
	replace Function is init(Str is source){
		:source: source;
		:length: source:length();
		:pos: 0;
		:line: 1;
		:col: 1;
		:errors: [];
	}

	## Records a lexical error at the current scan position: the message
	## carries the line, and the first provenance frame records exactly
	## where the scanner observed the problem.
	##
	## @param msg: Error description.
	Function is addError(String is msg){
		local Error is e: Error(message: "Line {{:line}}: {{msg}}");
		e:addTraceAt(className: Reflection:class(), methodName: Reflection:method(), line: :line, col: :col);
		:errors:push(item: e);
	}

	## Returns whether any lexical errors were recorded.
	##
	## @return: true when [errors] is non-empty.
	Function of Boolean is hasErrors(){
		return :errors:length() > 0;
	}

	## Returns all recorded lexical errors.
	##
	## @return: [Error] values, in scan order.
	Function of [Error] is getErrors(){
		return :errors;
	}

	## Tokenizes the entire source, ending with an EOF token at the final
	## cursor position.
	##
	## @return: The token stream.
	Function of [Token] is tokenize(){
		local [Token] is tokens: [];
		while({ :pos < :length }, {
			:skipWhitespaceAndComments();
			if({ :pos < :length }, {
				local String is ch: :source:charAt(index: :pos, default: '');
				if({ ch == '"' || ch == '\'' }, {
					local String is triple: :source:substring(start: :pos, end: :pos + 3);
					if({ triple == "'''" }, {
						tokens:push(item: :readTriple(quote: "'''", kind: TokenKind:RAWSTRING));
					}, {
						tokens:push(item: :readString(quote: ch));
					});
				}, {
					if({ ch == '`' }, {
						local String is triple: :source:substring(start: :pos, end: :pos + 3);
						if({ triple == "```" }, {
							tokens:push(item: :readTriple(quote: "```", kind: TokenKind:TEMPLATESTRING));
						}, {
							tokens:push(item: :readSymbol());
						});
					}, {
						if({ ch:isDigit() }, {
							tokens:push(item: :readNumber());
						}, {
							if({ :isIdentifierStart(ch: ch) }, {
								tokens:push(item: :readIdentifierOrKeyword());
							}, {
								tokens:push(item: :readSymbol());
							});
						});
					});
				});
			});
		});
		tokens:push(item: Token:init(kind: TokenKind:EOF, value: '', line: :line, col: :col));
		return tokens;
	}

	## Scans and returns the next token from the source stream.
	## When the end of source is reached, returns an EOF token.
	##
	## @return: The next Token.
	Function of Token is nextToken(){
		:skipWhitespaceAndComments();
		if({ :pos >= :length }, {
			return Token:init(kind: TokenKind:EOF, value: '', line: :line, col: :col);
		});

		local String is ch: :source:charAt(index: :pos, default: '');
		if({ ch == '"' || ch == '\'' }, {
			local String is triple: :source:substring(start: :pos, end: :pos + 3);
			if({ triple == "'''" }, {
				return :readTriple(quote: "'''", kind: TokenKind:RAWSTRING);
			});
			return :readString(quote: ch);
		});
		if({ ch == '`' }, {
			local String is triple: :source:substring(start: :pos, end: :pos + 3);
			if({ triple == "```" }, {
				return :readTriple(quote: "```", kind: TokenKind:TEMPLATESTRING);
			});
			return :readSymbol();
		});
		if({ ch:isDigit() }, {
			return :readNumber();
		});
		if({ :isIdentifierStart(ch: ch) }, {
			return :readIdentifierOrKeyword();
		});
		return :readSymbol();
	}

	## Maps a hexadecimal digit character to its value (0..15), or -1.
	##
	## @param ch: Digit character.
	## @return: Digit value, or -1 when not a hex digit.
	Function of Int is digitValue(Str is ch){
		local Str is lower: '0123456789abcdef';
		local Int is d: lower:indexOf(search: ch, default: -1);
		if({ d >= 0 }, {
			return d;
		});
		local Str is upper: 'ABCDEF';
		local Int is u: upper:indexOf(search: ch, default: -1);
		if({ u >= 0 }, {
			return u + 10;
		});
		return -1;
	}

	## Consumes the current character and updates line/col tracking.
	##
	## @return: The consumed character ('' at end of source).
	Function of String is advance(){
		local Int is b: :source:byteAt(index: :pos, default: -1);
		if({ b < 0 }, { return ''; });
		:pos: :pos + 1;
		if({ b == 10 }, {
			:line: :line + 1;
			:col: 1;
		}, {
			:col: :col + 1;
		});
		return String:fromCharCode(code: b);
	}

	## True when [ch] may begin an identifier.
	##
	## @param ch: Candidate character.
	## @return: Classification result.
	Function of Boolean is isIdentifierStart(String is ch){
		return :chars:isIdentifierStart(ch: ch);
	}

	## True when [ch] may continue an identifier.
	##
	## @param ch: Candidate character.
	## @return: Classification result.
	Function of Boolean is isIdentifierContinue(String is ch){
		return :chars:isIdentifierContinue(ch: ch);
	}

	## Skips whitespace and `#` comment lines before the next token.
	Function is skipWhitespaceAndComments(){
		local Int is p: :pos;
		local Int is len: :length;
		local Boolean is skipping: true;
		while(
			{ skipping && p < len },
			{
				local Int is b: :source:byteAt(index: p, default: -1);
				if({ b == 32 || b == 9 || b == 13 }, {
					p++;
					:col++;
				}, {
					if({ b == 10 }, {
						p++;
						:line++;
						:col: 1;
					}, {
						if({ b == 35 }, {
							p++;
							local Boolean is inComment: true;
							while(
								{ inComment && p < len },
								{
									local Int is cb: :source:byteAt(index: p, default: -1);
									if({ cb == 10 }, {
										inComment: false;
									}, {
										p++;
									});
								}
							);
						}, {
							skipping: false;
						});
					});
				});
			}
		);
		:pos: p;
	}

	## Scans an identifier or reserved word into a token. Reserved words
	## carry their [Keyword] classification for downstream enum dispatch.
	##
	## @return: KEYWORD or IDENTIFIER token.
	Function of Token is readIdentifierOrKeyword(){
		local Int is startLine: :line;
		local Int is startCol: :col;
		local Int is startPos: :pos;

		local Int is p: :pos;
		local Int is len: :length;
		local Boolean is scanning: true;
		while(
			{ scanning && p < len },
			{
				local Int is b: :source:byteAt(index: p, default: -1);
				local Boolean is isId: (b >= 97 && b <= 122) || (b >= 65 && b <= 90) || (b >= 48 && b <= 57) || b == 95;
				if({ isId }, {
					p++;
					:col++;
				}, {
					scanning: false;
				});
			}
		);
		:pos: p;

		local String is text: :source:substring(start: startPos, end: :pos);
		local Keyword is kw: Keyword:of(text);
		local TokenKind is kind: TokenKind:IDENTIFIER;
		if({ kw != Keyword:NONE }, {
			kind: TokenKind:KEYWORD;
		});
		# Boolean literals are identifier-shaped but scan as their own kind.
		if({ text == :names:boolTrue() || text == 'false' }, {
			kind: TokenKind:BOOL;
		});
		local Token is t: Token:init(kind: kind, value: text:intern(), line: startLine, col: startCol);
		if({ kw != Keyword:NONE }, {
			t:setKeyword(kw: kw);
		});
		return t;
	}

	## Scans a numeric literal: decimal, base-prefixed (0x/0b/0o), floats,
	## with `_` separators stripped and bare leading zeros normalized so the
	## emitted C literal stays decimal.
	##
	## @return: INT or FLOAT token.
	Function of Token is readNumber(){
		local Int is startLine: :line;
		local Int is startCol: :col;

		local String is ch: :source:charAt(index: :pos, default: '');
		local String is nextCh: :source:charAt(index: :pos + 1, default: '');
		if({ ch == '0' && nextCh != '' && nextCh != '.' && !nextCh:isDigit() }, {
			# the base prefix table: 0x/0b/0o (case-insensitive) ground the
			# literal's base; any other byte falls through to decimal.
			local Int is base: match(on: nextCh, when: [
				['x', 'X']: { 16 },
				['b', 'B']: { 2 },
				['o', 'O']: { 8 },
				else: { 0 }
			]);
			if({ base > 0 }, {
				:advance();
				:advance();
				local Int is val: 0;
				local Int is digitCount: 0;
				local Boolean is hadInvalid: false;
				local Boolean is keepGoing: true;
				while({ keepGoing && :pos < :length }, {
					local String is dch: :source:charAt(index: :pos, default: '');
					if({ dch == '_' }, {
						:advance();
					}, {
						local Int is d: :digitValue(ch: dch);
						if({ d >= 0 && d < base }, {
							val: (val * base) + d;
							digitCount: digitCount + 1;
							:advance();
						}, {
							if({ :chars:isIdentifierContinue(ch: dch) }, {
								hadInvalid: true;
								:advance();
							}, {
								keepGoing: false;
							});
						});
					});
				});
				if({ hadInvalid }, {
					:addError(msg: :errText:errInvalidDigitInBase(base: base));
				});
				if({ digitCount == 0 }, {
					:addError(msg: :errText:errMissingDigitsAfterPrefix());
				});
				return Token:init(kind: TokenKind:INT, value: '' . val, line: startLine, col: startCol);
			});
		});

		local Int is startPos: :pos;
		local Boolean is isFloat: false;
		local Boolean is keepScanning: true;
		while({ keepScanning && :pos < :length }, {
			local String is dch: :source:charAt(index: :pos, default: '');
			if({ dch == '_' }, {
				local String is nextD: :source:charAt(index: :pos + 1, default: '');
				if({ nextD:isDigit() }, {
					:advance();
				}, {
					keepScanning: false;
				});
			}, {
				if({ dch:isDigit() }, {
					:advance();
				}, {
					if({ dch == '.' && !isFloat }, {
						local String is nextD: :source:charAt(index: :pos + 1, default: '');
						if({ nextD:isDigit() }, {
							isFloat: true;
							:advance();
						}, {
							keepScanning: false;
						});
					}, {
						keepScanning: false;
					});
				});
			});
		});

		local String is text: :source:substring(start: startPos, end: :pos);
		text: text:replaceAll(search: '_', replacement: '');

		local TokenKind is kind: TokenKind:INT;
		if({ isFloat }, {
			kind: TokenKind:FLOAT;
		});
		if({ kind == TokenKind:INT && text:length() > 1 && text:charAt(index: 0, default: '') == '0' }, {
			# A bare leading zero stays decimal in Spec; strip it so C does
			# not reinterpret the emitted literal as octal.
			while(
				{ text:length() > 1 && text:charAt(index: 0, default: '') == '0' },
				{
					text: text:substring(start: 1, end: text:length());
				}
			);
		});
		return Token:init(kind: kind, value: text, line: startLine, col: startCol);
	}

	## Scans a single- or double-quoted string literal. The scan stays
	## escape-aware so an escaped quote cannot terminate the literal; the
	## template family carries raw content (its escapes and templates are
	## the parser's desugar), single quotes keep their two minimal escapes
	## (\' and \\) here.
	##
	## @param quote: The quote character being scanned.
	## @return: TEMPLATESTRING for double quotes, STRING otherwise.
	Function of Token is readString(String is quote){
		local Int is startLine: :line;
		local Int is startCol: :col;
		:advance();

		local String is res: '';
		local Boolean is keepScanning: true;
		while({ keepScanning && :pos < :length }, {
			local String is sch: :source:charAt(index: :pos, default: '');
			if({ sch == quote }, {
				keepScanning: false;
			}, {
				if({ sch == "\\" }, {
					if({ quote == '\'' }, {
						:advance();
						if({ :pos < :length }, {
							local String is nextCh: :advance();
							if({ nextCh == '\'' || nextCh == "\\" }, {
								res: res . nextCh;
							}, {
								res: res . "\\" . nextCh;
							});
						});
					}, {
						res: res . "\\";
						:advance();
						if({ :pos < :length }, {
							local String is nextCh: :advance();
							res: res . nextCh;
							if({ nextCh == 'u' }, {
								:validateUnicodeEscapeAt(uPos: :pos);
							});
						});
					});
				}, {
					res: res . sch;
					:advance();
				});
			});
		});

		if({ :pos < :length }, {
			:advance();
		});
		if({ quote == '"' }, {
			return Token:init(kind: TokenKind:TEMPLATESTRING, value: res, line: startLine, col: startCol);
		});
		return Token:init(kind: TokenKind:STRING, value: res, line: startLine, col: startCol);
	}

	## Validates a `\uXXXX` or `\u{...}` Unicode escape starting immediately
	## after `\u` at byte offset [uPos] in [:source], recording a lexical error
	## if the hex sequence is malformed, out of range (`> 0x10FFFF`), or a lone
	## surrogate (`0xD800..0xDFFF`).
	Function is validateUnicodeEscapeAt(Int is uPos){
		if({ uPos >= :length }, {
			:addError(msg: "Invalid Unicode escape: expected 4 hex digits (\\uXXXX) or braced hex (\\u{...}).");
			return;
		});
		local String is first: :source:charAt(index: uPos, default: '');
		if({ first == '{' }, {
			local Int is p: uPos + 1;
			local Int is digits: 0;
			local Int is val: 0;
			local Boolean is closed: false;
			local Boolean is badChar: false;
			while({ p < :length && !closed && !badChar }, {
				local String is ch: :source:charAt(index: p, default: '');
				if({ ch == '}' }, {
					closed: true;
				}, {
					local Int is d: :digitValue(ch: ch);
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
			if({ !closed || badChar || digits == 0 || digits > 6 }, {
				:addError(msg: "Invalid Unicode escape: \\u{...} requires 1 to 6 hexadecimal digits.");
				return;
			});
			if({ val > 1114111 }, {
				:addError(msg: "Invalid Unicode escape: code point exceeds maximum U+10FFFF.");
				return;
			});
			if({ val >= 55296 && val <= 57343 }, {
				:addError(msg: "Invalid Unicode escape: lone surrogate code points (U+D800..U+DFFF) are not valid Unicode scalar values.");
				return;
			});
			return;
		});
		if({ uPos + 4 > :length }, {
			:addError(msg: "Invalid Unicode escape: \\uXXXX requires 4 hexadecimal digits.");
			return;
		});
		local Int is val4: 0;
		local Int is k: 0;
		local Boolean is ok4: true;
		while({ k < 4 }, {
			local Int is d: :digitValue(ch: :source:charAt(index: uPos + k, default: ''));
			if({ d < 0 }, {
				ok4: false;
			}, {
				val4: (val4 * 16) + d;
			});
			k: k + 1;
		});
		if({ !ok4 }, {
			:addError(msg: "Invalid Unicode escape: \\uXXXX requires 4 hexadecimal digits.");
			return;
		});
		if({ val4 >= 55296 && val4 <= 57343 }, {
			:addError(msg: "Invalid Unicode escape: lone surrogate code points (U+D800..U+DFFF) are not valid Unicode scalar values.");
		});
	}

	## Scans a triple-delimiter heredoc. The delimiter line's own newline is
	## not content (shell heredoc convention); the first closing triple ends
	## the block.
	##
	## @param quote: The three-character delimiter.
	## @param kind: RAWSTRING for '''''' or TEMPLATESTRING for backticks.
	## @return: The heredoc token with raw content.
	Function of Token is readTriple(String is quote, TokenKind is kind){
		local Int is startLine: :line;
		local Int is startCol: :col;
		:advance();
		:advance();
		:advance();
		if({ :pos < :length && :source:charAt(index: :pos, default: '') == "\n" }, {
			:advance();
		});

		local String is res: '';
		local Boolean is closed: false;
		while({ !closed && :pos < :length }, {
			local String is triple: :source:substring(start: :pos, end: :pos + 3);
			if({ triple == quote }, {
				:advance();
				:advance();
				:advance();
				closed: true;
			}, {
				res: res . :advance();
			});
		});

		if({ !closed }, {
			:addError(msg: :errText:errUnterminatedHeredoc(quote: quote));
		});
		return Token:init(kind: kind, value: res, line: startLine, col: startCol);
	}

	## Scans one symbol token: two-character operators take precedence over
	## their one-character prefixes and carry their [Operator]
	## classification for downstream enum dispatch.
	##
	## @return: SYMBOL token.
	Function of Token is readSymbol(){
		local Int is startLine: :line;
		local Int is startCol: :col;
		local String is ch: :advance();
		local String is nextCh: :source:charAt(index: :pos, default: '');
		local String is pair: ch . nextCh;

		local Operator is op: Operator:of(pair);
		if({ op != Operator:NONE }, {
			:advance();
			local Token is t: Token:init(kind: TokenKind:SYMBOL, value: pair:intern(), line: startLine, col: startCol);
			t:setOperator(op: op);
			return t;
		});
		return Token:init(kind: TokenKind:SYMBOL, value: ch:intern(), line: startLine, col: startCol);
	}

}
