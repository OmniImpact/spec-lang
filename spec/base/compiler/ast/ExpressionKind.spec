#! Package base:compiler:ast
#! The expression node categories.
##
## Enum dispatch is the rule (COMPILER-PLAN section 9.5): passes switch on
## ExpressionKind with exhaustive `when` arms, never on string comparisons.

Enum of String is ExpressionKind {
	STRING: 'STRING',
	NUMBER: 'NUMBER',
	FLOAT: 'FLOAT',
	BOOL: 'BOOL',
	IDENT: 'IDENT',
	PATH: 'PATH',
	ARRAY: 'ARRAY',
	MAP: 'MAP',
	CAST: 'CAST',
	FIELD_ACCESS: 'FIELD_ACCESS',
	INDEX: 'INDEX',
	CALL: 'CALL',
	BINARY: 'BINARY',
	UNARY: 'UNARY',
	IF_ELSE: 'IF_ELSE',
	WHEN: 'WHEN',
	ANON_FN: 'ANON_FN',
	UNKNOWN: 'UNKNOWN'
}
