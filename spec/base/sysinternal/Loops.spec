#! Package base:sysinternal
#! The iteration floor: the single loop primitive. Every
#! loop shape composes above it — `until` runs the body once and then
#! negates the predicate, `repeat` counts, `run` drives the Loop
#! protocol — only this one item binds to C.

Class is Loops{
	namespace: ['base', 'sysinternal'];

	## Runs [iterate] repeatedly while [evaluate] returns `true`.
	##
	## Bound to `spec_while` at the floor; the base:iterator wrapper
	## composes every loop shape from this one item.
	##
	## @param evaluate: The predicate closure returning `true` to continue.
	## @param iterate: The body closure run on each step.
	Function is while(Function of Boolean is evaluate, Function is iterate){
	}
}
