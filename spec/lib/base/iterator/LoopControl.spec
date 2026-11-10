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

	## Whether a halt was requested on this controller.
	##
	## The query the runtime loop runners compose from: the compile-time
	## loop inlines read the runtime's control state directly, and the
	## `Loops:run` wrapper polls this between iterations. Safe on an
	## omitted (null) control: answers false.
	##
	## @return: true when [stop] was requested.
	Function of Boolean is isStopped(){
	}

	## Fires the completion callback registered at [init], if any.
	##
	## The runtime `Loops:run` calls this after the loop ends — the
	## same tail the compile-time inlines emit. No callback
	## registered: nothing happens.
	Function is complete(){
	}
}
