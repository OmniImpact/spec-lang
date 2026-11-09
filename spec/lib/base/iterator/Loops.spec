#! Package base:iterator
#! Decoupled, stateful iteration abstractions and execution runners.

## The control-flow provider (FUNCTIONS.md §II.4): one as-import serves
## the loop constructs bare — `Loops:loop(evaluate:, iteration:)` mirrors
## `Conditional`'s `if(...)`. Runtime-managed: every method is
## intercepted by the generator — [while]/[loop] inline their closures
## as native C loops, [repeat] inlines a counting loop, [until] inlines
## a do-while, [run] drives the loop protocol directly — so no body is
## emitted.

Class is Loops{
	namespace: ['base', 'iterator'];

	replace Array of Array of String is using: [
		['base', 'iterator', Loop]
];

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
	Function is while(Function is evaluate, Function is iteration){
	}

	## Repeatedly executes [iterate] while [evaluate] returns `true`,
	## binding any scoped loop state in [vars].
	##
	## @param vars: Loop state variable declarations or empty.
	## @param evaluate: Predicate closure returning `true` to continue.
	## @param iterate: Body closure executed on each step.
	Function is loop(Any is vars, Function is evaluate, Function is iterate){
	}

	## Executes [worker] exactly [count] times.
	##
	## @param count: The iteration count.
	## @param worker: Body closure executed on each step.
	Function is repeat(Int is count, Function is worker){
	}

	## Executes [iteration] once, then repeats while [evaluate] returns
	## `true` — the body always runs at least once.
	##
	## @param evaluate: Predicate closure returning `true` to continue.
	## @param iteration: Body closure executed on each step.
	Function is until(Function is evaluate, Function is iteration){
	}
}
