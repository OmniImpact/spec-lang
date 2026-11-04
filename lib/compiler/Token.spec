#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, and Linter.

Enum of String is TokenKind {
	KEYWORD: "KEYWORD",
	IDENTIFIER: "IDENTIFIER",
	SYMBOL: "SYMBOL",
	INT: "INT",
	FLOAT: "FLOAT",
	STRING: "STRING",
	BOOL: "BOOL",
	EOF: "EOF"
}

## Represents a lexical token emitted by the compiler [Lexer].
Class is Token{

	replace Array of String is using: [
		base:sys:SourceLocation
	];

	## Lexical token category kind.
	local TokenKind is kind: TokenKind:EOF;

	## Raw lexeme string value.
	local String is value: "";

	## Source coordinate provenance where this token was scanned.
	local SourceLocation is location;

	## Initializes a token with raw line and column coordinates.
	##
	## @param kind: Lexical token category kind.
	## @param value: Token string value.
	## @param line: One-based line coordinate.
	## @param col: One-based column coordinate.
	replace Function is init(TokenKind is kind, String is value, Int is line, Int is col){
		self:kind: kind;
		self:value: value;
		self:location: SourceLocation:init(file: "", line: line, col: col);
	}

	## Initializes a token with a pre-constructed [SourceLocation].
	##
	## @param kind: Lexical token category kind.
	## @param value: Token string value.
	## @param location: [SourceLocation] provenance.
	local Function is withLocation(TokenKind is kind, String is value, SourceLocation is location){
		self:kind: kind;
		self:value: value;
		self:location: location;
	}

	## Returns the token category enum kind.
	##
	## @return: [TokenKind] enum variant.
	Function of TokenKind is getTokenKind(){
		return self:kind;
	}

	## Returns the token category kind string value.
	##
	## @return: Kind string tag.
	Function of String is getKind(){
		return self:kind:value();
	}

	## Returns the raw lexeme string value.
	##
	## @return: Value string.
	Function of String is getValue(){
		return self:value;
	}

	## Returns the one-based line number.
	##
	## @return: Line number integer.
	Function of Int is getLine(){
		return self:location:getLine();
	}

	## Returns the one-based column number.
	##
	## @return: Column number integer.
	Function of Int is getCol(){
		return self:location:getCol();
	}

	## Returns the [SourceLocation] of this token.
	##
	## @return: [SourceLocation] coordinate instance.
	local Function of SourceLocation is getLocation(){
		return self:location;
	}

}
