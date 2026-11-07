#! Package base:compiler:lexer
#! The reserved words, as an enum.
##
## The scanner maps identifier text to a [Keyword] variant once; every
## downstream consumer dispatches on the enum instead of comparing strings.
## [NONE] marks "not a keyword".

Enum of String is Keyword {
	namespace: ['base', 'compiler', 'lexer'],
	NONE: '',
	LOCAL: 'local',
	CONTAINED: 'contained',
	REPLACE: 'replace',
	MERGE: 'merge',
	IS: 'is',
	AS: 'as',
	OF: 'of',
	TO: 'to',
	RETURN: 'return',
	IF: 'if',
	ELSE: 'else',
	WHEN: 'when'
}
