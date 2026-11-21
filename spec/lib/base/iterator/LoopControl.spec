#! Package base:iterator
#! Decoupled, stateful iteration abstractions and execution runners.

## Coordinates loop flow control, early termination halts, and completion
## callbacks. Instances are ordinary ARC objects: `stop` raises the halt
## flag, `isStopped` reports it, and `complete` fires the registered
## completion callback — a no-op until one is assigned.

Class is LoopControl{
	namespace: ['base', 'iterator'];

	## Flag indicating whether a halt was requested.
	local Boolean is stopped: false;

	## Optional completion callback, fired by [complete] when the loop
	## finishes. Defaults to a no-op; assign a closure to observe
	## completion (it may capture the loop owner's state directly).
	Function is onComplete: local Function(){};

	## Requests an immediate halt of loop execution.
	Function is stop(){
		:stopped: true;
	}

	## Whether a halt was requested on this controller.
	##
	## @return: true when [stop] was requested.
	Function of Boolean is isStopped(){
		return :stopped;
	}

	## Fires the completion callback registered in [onComplete].
	Function is complete(){
		onComplete();
	}
}
