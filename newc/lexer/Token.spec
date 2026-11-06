#! Package newc:lexer
#! One lexical token: its category, raw lexeme, and source coordinates.
##
## Line and column are carried directly — the token stream has no file
## identity (a compilation may span files); the diagnostic layer that knows
## the current file composes the full location when reporting.

Class is Token{
	namespace: ['newc', 'lexer'];

	## Dependency-free: coordinates are plain integers, the kind is the
	## local enum.
	replace Array of Array of String is using;

	## Lexical token category.
	local TokenKind is kind: TokenKind:EOF;

	## Raw lexeme as scanned (raw heredocs and fancy strings carry their
	## unprocessed bytes; the parser's desugar owns interpretation).
	local String is value: '';

	## One-based line where the token starts.
	local Int is line: 1;

	## One-based column where the token starts.
	local Int is col: 1;

	## Initializes a token with its kind, lexeme, and start coordinates.
	##
	## @param kind: Lexical token category.
	## @param value: Raw lexeme string.
	## @param line: One-based line coordinate.
	## @param col: One-based column coordinate.
	replace Function is init(TokenKind is kind, String is value, Int is line, Int is col){
		self:kind: kind;
		self:value: value;
		self:line: line;
		self:col: col;
	}

	## Returns the token category.
	##
	## @return: [TokenKind] variant for `when` dispatch.
	Function of TokenKind is getTokenKind(){
		return self:kind;
	}

	## Returns the raw lexeme.
	##
	## @return: Value string.
	Function of String is getValue(){
		return self:value;
	}

	## Returns the one-based line coordinate.
	##
	## @return: Line number.
	Function of Int is getLine(){
		return self:line;
	}

	## Returns the one-based column coordinate.
	##
	## @return: Column number.
	Function of Int is getCol(){
		return self:col;
	}

	## Human-readable diagnostic form, used verbatim in error messages.
	##
	## @return: Text like {{KIND}} '{{value}}' at {{line}}:{{col}}.
	Function of String is describe(){
		return "{{self:kind:value()}} '{{self:value}}' at {{self:line}}:{{self:col}}";
	}
}
