#! Package base:iterator
#! Provides decoupled, stateful iterator abstractions and execution runners.

## Callback interface invoked when a [Loop] finishes execution via [LoopControl].
Class is LoopCallback{

	replace local Array of String is using: [
		base:iterator:LoopControl
	];

	## Invoked when the associated loop completes.
	##
	## @param control: The [LoopControl] coordinator for the finished loop.
	Function is onComplete(LoopControl is control){
	}

}
