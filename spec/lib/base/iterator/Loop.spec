#! Package base:iterator
#! Decoupled, stateful iteration abstractions and execution runners.

## Abstract base class for decoupled loop iteration logic.
##
## Encapsulates the continuation condition in [evaluate] and loop body
## execution in [iteration]. Terminated when [evaluate] returns `false` or
## the run's [LoopControl] is stopped. Every compile-time loop class in a
## program extends [Loop]; the `Loops` runners drive it through the runtime'
## loop protocol.

Class is Loop{
	namespace: ['base', 'iterator'];

	## Evaluates whether another loop iteration should proceed.
	##
	## @return: `true` to continue running, `false` to terminate the loop.
	Function of Boolean is evaluate(){
		return false;
	}

	## Executes a single iteration of the loop body.
	##
	## @param control: The [LoopControl] coordinator managing halts and callbacks.
	## @return: `true` to continue, `false` to break.
	Function of Boolean is iteration(LoopControl is control){
		return false;
	}
}
