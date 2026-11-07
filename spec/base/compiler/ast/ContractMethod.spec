#! Package base:compiler:ast
#! The compiler-recognized method names: the root-contract reservations
#! and the loop protocol. Passes dispatch on the enum instead of comparing
## raw names.

Enum of String is ContractMethod {
	namespace: ['base', 'compiler', 'ast'],
	INIT: 'init',
	USING: 'using',
	TO_STRING: 'toString',
	TYPE_NAME: 'typeName',
	EVALUATE: 'evaluate',
	ITERATION: 'iteration'
}
