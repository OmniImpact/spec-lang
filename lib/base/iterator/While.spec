#! Package base:iterator
#! Provides decoupled, stateful iterator abstractions and execution runners.

## Standard iteration runner that executes a [Loop] instance to completion.
Class is While{

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
