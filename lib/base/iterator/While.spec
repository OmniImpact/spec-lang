#! Package base:iterator
#! Provides decoupled, stateful iterator abstractions and execution runners.

## Standard iteration runner that executes a [Loop] instance to completion.
class While{

	## Repeatedly evaluates and steps [loop] until termination or halt.
	##
	## @param loop: The [Loop] instance executing iterations.
	## @param control: Optional [LoopControl] coordinator.
	replace Function is run(Loop is loop, LoopControl is control){
	}

}
