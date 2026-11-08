#! Package base:sysinternal
#! The conditional floor (FUNCTIONS.md Part II): the single control-flow
#! primitive. `else` is composed above it as `if(!check, else)` — only
#! this one item binds to C.

Class is Conditional{
	namespace: ['base', 'sysinternal'];

	## Runs [then] exactly when [check] holds.
	##
	## Bound to `spec_branch` at the floor; the base:sys wrapper composes
	## every conditional shape from this one item.
	##
	## @param check: The condition.
	## @param then: The closure to run when the condition holds.
	Function is branch(Function of Boolean is check, Function is then){
	}
}
