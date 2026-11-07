#! Package base:iterator
#! Decoupled, stateful iteration abstractions and execution runners.

## Standard iteration runner that executes a [Loop] instance to completion.
##
## Runtime-managed (TRANSITION.md section 2): both methods are intercepted
## by the generator — [run] drives the loop protocol directly, [condition]
## inlines its two closures as a native C loop — so neither body is emitted.

Class is While{
	namespace: ['base', 'iterator'];

	## Repeatedly evaluates and steps [loop] until termination or halt.
	##
	## @param loop: The [Loop] instance executing iterations.
	## @param control: Optional [LoopControl] coordinator.
	Function is run(Loop is loop, LoopControl is control){
	}

	## Repeatedly executes [iteration] while [evaluate] returns `true`.
	##
	## @param evaluate: Predicate closure returning `true` to continue.
	## @param iteration: Body closure executed on each step.
	Function is condition(Function is evaluate, Function is iteration){
	}
}
