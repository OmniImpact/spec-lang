#! Package base:iterator
#! Provides decoupled, stateful iterator abstractions and execution runners.

## Manages loop flow control, early termination halts, and completion callbacks.
class LoopControl{

	## Flag indicating whether a halt was requested.
	local Boolean is stopped: false;

	## Initializes a loop controller with an optional completion callback.
	##
	## @param callback: Optional completion handler.
	init(Any is callback){
	}

	## Requests an immediate halt of loop execution.
	Function is stop(){
	}

}
