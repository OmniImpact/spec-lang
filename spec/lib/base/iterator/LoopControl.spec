#! Package base:iterator
#! Decoupled, stateful iteration abstractions and execution runners.

## Manages loop flow control, early termination halts, and completion callbacks.
##
## Runtime-managed: instances are the runtime's
## SpecLoopControl objects; the declaration is the API surface the runners
## and loop bodies see.

Class is LoopControl{
	namespace: ['base', 'iterator'];

	## Flag indicating whether a halt was requested.
	local Boolean is stopped: false;

	## Initializes a loop controller with an optional completion callback.
	##
	## @param callback: Optional completion handler ([LoopCallback] or closure).
	replace Function is init(Any is callback){
	}

	## Requests an immediate halt of loop execution.
	Function is stop(){
	}
}
