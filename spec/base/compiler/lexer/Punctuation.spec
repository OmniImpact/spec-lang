#! Package base:compiler:lexer
#! The structural punctuation, as an enum.
##
## Role-named so parser call sites read as intent
## (matchPunct(p: Punctuation:BLOCK_OPEN)) instead of as lexeme soup.
##
## Keys are unique; VALUES may repeat. The colon is overloaded — one
## variant per role — because every role still matches the same lexeme,
## and the role name tells the reader which grammar production is at work.
## Consequence for [of]-style reverse lookup: the first variant carrying a
## value wins, so overloaded values have no canonical reverse mapping.
## Multi-character operators are classified by [Operator]; single-character
## operators ('+', '.', ...) stay plain lexemes.

Enum of String is Punctuation {
	TERMINATOR: ';',
	SEPARATOR: ',',
	BLOCK_OPEN: '{',
	BLOCK_CLOSE: '}',
	GROUP_OPEN: '(',
	GROUP_CLOSE: ')',
	BRACKET_OPEN: '[',
	BRACKET_CLOSE: ']',
	ACCESSOR: ':',
	ASSIGN: ':',
	PAIR: ':',
	ARM: ':',
	DEFAULT: ':',
	TAG: ':',
	NAMED_ARG: ':'
}
