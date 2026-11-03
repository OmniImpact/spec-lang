#! Package base:iterator
#! Provides decoupled, stateful iterator abstractions and execution runners.

## Abstract base class for decoupled loop iteration logic.
##
## Encapsulates the continuation condition in [evaluate] and loop body execution
## in [iteration]. Terminated when [evaluate] returns `false` or [control:stop] is called.
class Loop{

	## Evaluates whether another loop iteration should proceed.
	##
	## @return: `true` to continue running, `false` to terminate the loop.
	replace Function of Boolean is evaluate(){
		return false;
	}

	## Executes a single iteration of the loop body.
	##
	## @param control: The [LoopControl] coordinator managing halts and callbacks.
	## @return: `true` to continue, `false` to break.
	replace Function of Boolean is iteration(LoopControl is control){
		return false;
	}

}
