#! Package base:sys
#! The control-flow providers: the conditional and the loop constructs,
#! same-name wrappers over their sysinternal floors.

## The loop-control provider: one as-import serves the loop constructs
## bare — `Loops:loop(evaluate:, iteration:)` mirrors `Conditional`'s
## `if(...)`. THE IMPLEMENTATION LIVES HERE, composed from the
## iteration floor's single primitive (base:sysinternal:Loops:while —
## the loop-shape counterpart of the conditional floor's branch). The
## compiler additionally inlines the literal-closure forms as native C
## loops (zero allocation) — the same two-tier shape as Conditional:if:
## the inline is the fast path for inline literals, and THIS body is
## the runtime path a call follows when its closures are not inline
## literals (Function variables, callbacks held as values).
##
## UNIFIED CAPTURE SEMANTICS: Both literal closures and runtime closures
## share frame locals. Mutable variables captured by runtime closures are
## shared by reference via heap-allocated cells (SpecBox), so mutations
## made by any closure or the enclosing method are immediately visible across
## all closures and the caller in real time.

Class is Loops{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'iterator', Loop],
		['base', 'sysinternal', Loops]
];

	## Repeatedly evaluates and steps [loop] until termination or halt.
	##
	## The Loop protocol, composed from the floor's while: run while
	## [loop] evaluates true, the iteration's `false` return breaks,
	## a halt on [control] breaks, and the completion callback fires
	## after the loop ends either way — the same tail the compile-time
	## inline emits. The continue flag rides a reference cell (an
	## Array box): the runtime closures capture frame locals by value,
	## and a shared flag must be reachable through a pointer capture.
	##
	## @param loop: The [Loop] instance executing iterations.
	## @param control: Optional [LoopControl] coordinator.
	Function is run(Loop is loop, LoopControl is control){
		local Boolean is running: true;
		base:sysinternal:Loops:while(
			evaluate: { return running && loop:evaluate() && !control:isStopped(); },
			iterate: {
				running: loop:iteration(control: control);
			}
		);
		control:complete();
	}

	## Repeatedly executes [iteration] while [evaluate] returns `true`.
	##
	## The floor primitive directly: the construct IS the primitive's
	## shape.
	##
	## @param evaluate: Predicate closure returning `true` to continue.
	## @param iteration: Body closure executed on each step.
	Function is while(Function of Boolean is evaluate, Function is iteration){
		base:sysinternal:Loops:while(evaluate: evaluate, iterate: iteration);
	}

	## Repeatedly executes [iterate] while [evaluate] returns `true`,
	## binding any scoped loop state in [vars].
	##
	## [vars] is the compile-time scoping sugar: the vars literal's
	## parameters bind over the closures at the call site, so this
	## member's runtime drive is the bare floor while. The compiler
	## rejects a [vars] form whose closures are not inline literals —
	## the variables could not capture call-scoped parameters.
	##
	## @param vars: Loop state variable declarations or empty.
	## @param evaluate: Predicate closure returning `true` to continue.
	## @param iterate: Body closure executed on each step.
	Function is loop(Any is vars, Function of Boolean is evaluate, Function is iterate){
		base:sysinternal:Loops:while(evaluate: evaluate, iterate: iterate);
	}

	## Executes [worker] exactly [count] times.
	##
	## Composed from the floor's while over a counter. The counter
	## rides a reference cell (an Array box): the runtime closures
	## capture frame locals by value, and the counter must be shared
	## between the predicate and the step — a plain frame local would
	## live in two snapshots and never advance.
	##
	## @param count: The iteration count.
	## @param worker: Body closure executed on each step.
	Function is repeat(Int is count, Function is worker){
		local Int is done: 0;
		base:sysinternal:Loops:while(
			evaluate: { return done < count; },
			iterate: {
				worker();
				done: done + 1;
			}
		);
	}

	## Executes [iteration] once, then repeats while [evaluate] returns
	## `true` — the body always runs at least once.
	##
	## Composed from the floor's while: one unconditional run, then the
	## predicate negated.
	##
	## @param evaluate: Predicate closure returning `true` to continue.
	## @param iteration: Body closure executed on each step.
	Function is until(Function of Boolean is evaluate, Function is iteration){
		iteration();
		base:sysinternal:Loops:while(evaluate: { return !evaluate(); }, iterate: iteration);
	}
}
