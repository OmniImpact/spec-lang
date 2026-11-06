#! Package base:compiler:lexer
#! The multi-character operators, as an enum.
##
## The scanner classifies a symbol lexeme once (operatorFor); downstream
## consumers dispatch on the enum instead of comparing lexemes. Single-
## character symbols have no Operator variant — they are structural and
## stay plain lexemes. [NONE] marks "not a multi-character operator".

Enum of String is Operator {
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
