#! Package newc:lexer
#! The lexical token categories of the new compiler.
##
## Enum dispatch is the rule (COMPILER-PLAN section 9.5): parsers and
## generators switch on TokenKind with exhaustive `when` arms, never on
## string comparisons.

Enum of String is TokenKind {
	KEYWORD: 'KEYWORD',
	IDENTIFIER: 'IDENTIFIER',
	SYMBOL: 'SYMBOL',
	INT: 'INT',
	FLOAT: 'FLOAT',
	STRING: 'STRING',
	RAWSTRING: 'RAWSTRING',
	FANCYSTRING: 'FANCYSTRING',
	BOOL: 'BOOL',
	EOF: 'EOF'
}
