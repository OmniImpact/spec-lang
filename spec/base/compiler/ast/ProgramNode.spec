#! Package base:compiler:ast
#! The root node of a parsed compilation: every top-level class in load
## order.

Class is ProgramNode{
	namespace: ['base', 'compiler', 'ast'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'ast', ClassInfo]
	];

	## Top-level classes, in load order.
	Array of ClassInfo is classes: [];

	## Initializes the program node.
	##
	## @param classes: Top-level classes.
	replace Function is init(Array of ClassInfo is classes){
		self:classes: classes;
	}
}
