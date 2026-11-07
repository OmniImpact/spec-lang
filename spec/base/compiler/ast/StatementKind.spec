#! Package base:compiler:ast
#! The statement node categories.
##
## Enum dispatch is the rule (COMPILER-PLAN section 9.5): passes switch on
## StatementKind with exhaustive `when` arms, never on string comparisons.

Enum of String is StatementKind {
	namespace: ['base', 'compiler', 'ast'],
	VAR_DECL: 'VAR_DECL',
	ASSIGN: 'ASSIGN',
	IF: 'IF',
	RETURN: 'RETURN',
	CLASS: 'CLASS',
	EXPR: 'EXPR',
	WHEN: 'WHEN',
	FORWARD: 'FORWARD'
}
