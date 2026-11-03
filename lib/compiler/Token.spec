#! Package compiler
#! Pure Spec compiler implementation: Lexer, Parser, AST, and Linter.

## Represents a lexical token emitted by the compiler [Lexer].
class Token{

	replace local Array of String is using: [
		base:sys:SourceLocation
	];

	## Lexical token category ("KEYWORD", "IDENTIFIER", "SYMBOL", "INT", "FLOAT", "STRING", "BOOL", "EOF").
	local String is kind: "";

	## Raw lexeme string value.
	local String is value: "";

	## Source coordinate provenance where this token was scanned.
	local SourceLocation is location;

	## Initializes a token with raw line and column coordinates.
	##
	## @param kind: Lexical token category tag.
	## @param value: Token string value.
	## @param line: One-based line coordinate.
	## @param col: One-based column coordinate.
	replace local Function is init(String is kind, String is value, Int is line, Int is col){
		self:kind: kind;
		self:value: value;
		self:location: SourceLocation:init(file: "", line: line, col: col);
	}

	## Initializes a token with a pre-constructed [SourceLocation].
	##
	## @param kind: Lexical token category tag.
	## @param value: Token string value.
	## @param location: [SourceLocation] provenance.
	replace local Function is withLocation(String is kind, String is value, SourceLocation is location){
		self:kind: kind;
		self:value: value;
		self:location: location;
	}

	## Returns the token category kind.
	##
	## @return: Kind string tag.
	replace local Function of String is getKind(){
		return self:kind;
	}

	## Returns the raw lexeme string value.
	##
	## @return: Value string.
	replace local Function of String is getValue(){
		return self:value;
	}

	## Returns the one-based line number.
	##
	## @return: Line number integer.
	replace local Function of Int is getLine(){
		return self:location:getLine();
	}

	## Returns the one-based column number.
	##
	## @return: Column number integer.
	replace local Function of Int is getCol(){
		return self:location:getCol();
	}

	## Returns the [SourceLocation] of this token.
	##
	## @return: [SourceLocation] coordinate instance.
	replace local Function of SourceLocation is getLocation(){
		return self:location;
	}

}
