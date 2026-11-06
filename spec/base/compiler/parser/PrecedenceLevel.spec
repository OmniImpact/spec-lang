#! Package base:compiler:parser
#! The binary-operator precedence levels, loosest to tightest.
##
## One parameterized fold loop ([BinaryFoldLoop]) walks these levels; the
## chain order lives here instead of in eleven copy-pasted loop classes.
## [NONE] marks "descend to unary" (the tightest level, not a binary one).

Enum of String is PrecedenceLevel {
	NONE: 'NONE',
	MULTIPLICATIVE: 'MULTIPLICATIVE',
	ADDITIVE: 'ADDITIVE',
	SHIFT: 'SHIFT',
	CONCAT: 'CONCAT',
	RELATIONAL: 'RELATIONAL',
	EQUALITY: 'EQUALITY',
	BIT_AND: 'BIT_AND',
	BIT_XOR: 'BIT_XOR',
	BIT_OR: 'BIT_OR',
	LOGICAL_AND: 'LOGICAL_AND',
	LOGICAL_OR: 'LOGICAL_OR'
}
