#! Package base:compiler:lexer
#! The multi-character operators, as an enum.
##
## The scanner classifies a symbol lexeme once (operatorFor); downstream
## consumers dispatch on the enum instead of comparing lexemes. Single-
## character operators ('+', '.', ...) stay plain lexemes; structural
## punctuation lives in [Punctuation]. [NONE] marks "not a multi-character
## operator".

Enum of String is Operator {
	namespace: ['base', 'compiler', 'lexer'],
	NONE: '',
	EQ: '==',
	NE: '!=',
	LE: '<=',
	GE: '>=',
	AND: '&&',
	OR: '||',
	SHL: '<<',
	SHR: '>>',
	SCOPE: '::'
}
