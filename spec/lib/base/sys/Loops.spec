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
## THE TWO TIERS' CAPTURE SEMANTICS: the literal closures inline into
## the enclosing frame and SHARE its locals — the counter idiom
## (`local Int is n` mutated by both closures) is theirs. The runtime
## forms' closures are the runtime's closure objects: captures are
## per-closure values written back into that closure's own environment
## at exit. Shared mutable state across a runtime loop's closures
## therefore rides the INSTANCE (`self:` fields — captured by
## reference), not a frame local.

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
		local Array of Boolean is runningCell: [true];
		base:sysinternal:Loops:while(
			evaluate: { return runningCell[0] && loop:evaluate() && !control:isStopped(); },
			iterate: {
				runningCell[0]: loop:iteration(control: control);
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
		local Array of Int is doneCell: [0];
		base:sysinternal:Loops:while(
			evaluate: { return doneCell[0] < count; },
			iterate: {
				worker();
				doneCell[0]: doneCell[0] + 1;
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
