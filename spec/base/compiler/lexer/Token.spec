#! Package base:compiler:lexer
#! One lexical token: its category, raw lexeme, and source coordinates.
##
## Line and column are carried directly — the token stream has no file
## identity (a compilation may span files); the diagnostic layer that knows
## the current file composes the full location when reporting.

Class is Token{
	replace [String] is namespace: ['base', 'compiler', 'lexer'];

	replace [[String]] is using: [
		['base', 'compiler', 'lexer', Keyword],
		['base', 'compiler', 'lexer', Operator]
,
		['base', 'compiler', 'lexer', TokenKind]
];

	## Lexical token category.
	local TokenKind is kind: TokenKind:EOF;

	## Raw lexeme as scanned (raw heredocs and template strings carry their
	## unprocessed bytes; the parser's desugar owns interpretation).
	local String is value: '';

	## One-based line where the token starts.
	local Int is line: 1;

	## One-based column where the token starts.
	local Int is col: 1;

	## The reserved word when [kind] is KEYWORD; [Keyword:NONE] otherwise.
	## Downstream passes dispatch on this enum instead of comparing lexemes.
	local Keyword is keyword: Keyword:NONE;

	## The operator classification when [kind] is SYMBOL and the lexeme is a
	## multi-character operator; [Operator:NONE] otherwise.
	local Operator is operator: Operator:NONE;

	## Initializes a token with its kind, lexeme, and start coordinates.
	##
	## @param kind: Lexical token category.
	## @param value: Raw lexeme string.
	## @param line: One-based line coordinate.
	## @param col: One-based column coordinate.
	replace Function is init(TokenKind is kind, String is value, Int is line, Int is col){
		:kind: kind;
		:value: value;
		:line: line;
		:col: col;
	}

	## Attaches the reserved-word classification to a KEYWORD token.
	##
	## @param kw: The [Keyword] variant scanned.
	Function is setKeyword(Keyword is kw){
		:keyword: kw;
	}

	## Returns the token category.
	##
	## @return: [TokenKind] variant for `when` dispatch.
	Function of TokenKind is getTokenKind(){
		return :kind;
	}

	## Returns the reserved-word classification.
	##
	## @return: [Keyword] variant; [Keyword:NONE] for non-keyword tokens.
	Function of Keyword is getKeyword(){
		return :keyword;
	}

	## Attaches the operator classification to a SYMBOL token.
	##
	## @param op: The [Operator] variant scanned.
	Function is setOperator(Operator is op){
		:operator: op;
	}

	## Returns the operator classification.
	##
	## @return: [Operator] variant; [Operator:NONE] otherwise.
	Function of Operator is getOperator(){
		return :operator;
	}

	## Returns the raw lexeme.
	##
	## @return: Value string.
	Function of String is getValue(){
		return :value;
	}

	## Returns the one-based line coordinate.
	##
	## @return: Line number.
	Function of Int is getLine(){
		return :line;
	}

	## Returns the one-based column coordinate.
	##
	## @return: Column number.
	Function of Int is getCol(){
		return :col;
	}

	## Human-readable diagnostic form, used verbatim in error messages.
	##
	## @return: Text like {{KIND}} '{{value}}' at {{line}}:{{col}}.
	Function of String is describe(){
		return "{{:kind:value()}} '{{:value}}' at {{:line}}:{{:col}}";
	}
}
