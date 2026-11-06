#! Package base:compiler:utils
#! Character classification for the scanner and parser.
##
## Stateless utility class: construct-and-call is the whole protocol
## (`Chars():isIdentifierStart(ch)`). Classification rides the compiled
## String predicates — the compiler eats its own String migration.

Class is Chars{
	replace Array of String is namespace: ['base', 'compiler', 'utils'];

	## True when [ch] may begin an identifier: a letter or an underscore.
	Function of Boolean is isIdentifierStart(String is ch){
		return ch:isAlpha() || ch == '_';
	}

	## True when [ch] may continue an identifier: letters, digits, underscore.
	Function of Boolean is isIdentifierContinue(String is ch){
		return ch:isAlpha() || ch:isDigit() || ch == '_';
	}

	## True when [ch] is an ASCII uppercase letter.
	Function of Boolean is isUpper(String is ch){
		local String is uppers: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
		return uppers:indexOf(search: ch, default: -1) >= 0;
	}
}
