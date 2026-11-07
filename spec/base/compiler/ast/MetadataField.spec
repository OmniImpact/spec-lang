#! Package base:compiler:ast
#! The declarative metadata property names (loader directives that are
## per-class by design and never participate in type checking or
## inheritance matching).

Enum of String is MetadataField {
	namespace: ['base', 'compiler', 'ast'],
	NAMESPACE: 'namespace',
	USING: 'using',
	GROUP: 'group',
	CASTABLE: 'castable'
}
