#! Package base:sysinternal
#! Pure-Spec unmanaged floor for the thread-local deferred-cleanup stack.
#! Floor name is Cleanup (NOT Defer): body-bearing floors must have a bare
#! name unique in the program — the checker and emitted vtable globals
#! resolve by bare name, so a floor sharing its wrapper's name collides
#! (the only same-named floor, Mem, is declaration-only and emits nothing).
##
## TLS slots in @_spec_tls_i64:
##   slot 9:  cleanup_stack (i64 address of i64[] entry buffer)
##   slot 10: cleanup_top   (i64 current stack depth)
##   slot 11: cleanup_cap   (i64 allocated slot capacity)
##
## Entry encoding on the shared stack:
##   nonzero: closure object address (a registration; owns its own +1)
##   zero:    live barrier (pushed by frameEnter for a defer-ful frame)
##
## Contract: a defer-ful frame calls frameEnter() at entry and frameExit()
## on EVERY exit path (normal and unwind — on unwind the emitter runs it
## before the handler walk). frameExit() runs every registration above the
## frame's barrier newest-first, releases each registration after its
## action runs, and pops the barrier. Because barriers delimit frame
## regions on ONE shared thread-local stack, a push made anywhere during a
## frame's dynamic extent binds to the innermost enclosing defer-ful frame
## — the frame whose body performed the push. The emitter never gives the
## Defer wrapper/floor classes their own barriers, so their frames are
## transparent and ownership lands on the caller whose source pushed.
## Actions must not raise (a raising action's error flows into the exiting
## frame's handler walk; its remaining siblings stay registered and owned)
## and must not rely on later sibling registrations.

Class is Cleanup{
	namespace: ['base', 'sysinternal'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', as Mem()],
		['base', 'sysinternal', as Conditional()],
		['base', 'sysinternal', as Loops()]
	];

	## Marks the current frame's cleanup region on the shared stack.
	Function is frameEnter(){
		local Int is top: base:sysinternal:Mem:tlsGetI64(slot: 10);
		local Int is cap: base:sysinternal:Mem:tlsGetI64(slot: 11);
		if({ top == cap }, {
			local Int is ncap: if({ cap == 0 }, { 8 }, { cap * 2 });
			local Int is nstk: base:sysinternal:Mem:realloc(ptr: base:sysinternal:Mem:tlsGetI64(slot: 9), bytes: ncap * 8);
			base:sysinternal:Mem:tlsSetI64(slot: 9, val: nstk);
			base:sysinternal:Mem:tlsSetI64(slot: 11, val: ncap);
		});
		local Int is stk: base:sysinternal:Mem:tlsGetI64(slot: 9);
		base:sysinternal:Mem:storeI64(ptr: stk, byteOffset: top * 8, val: 0);
		base:sysinternal:Mem:tlsSetI64(slot: 10, val: top + 1);
	}

	local Function is invokeCleanup(Function is cb){
		cb();
	}

	## Adopts a deferred action: retains the closure object (+1 owned by the
	## registration) and pushes it above the innermost live barrier.
	Function is pushCleanup(Function is action){
		local Int is addr: base:sysinternal:Mem:objToAddr(obj: action);
		if({ addr == 0 }, { return; });
		base:sysinternal:Mem:retainAddr(objAddr: addr);
		local Int is top: base:sysinternal:Mem:tlsGetI64(slot: 10);
		local Int is cap: base:sysinternal:Mem:tlsGetI64(slot: 11);
		if({ top == cap }, {
			local Int is ncap: if({ cap == 0 }, { 8 }, { cap * 2 });
			local Int is nstk: base:sysinternal:Mem:realloc(ptr: base:sysinternal:Mem:tlsGetI64(slot: 9), bytes: ncap * 8);
			base:sysinternal:Mem:tlsSetI64(slot: 9, val: nstk);
			base:sysinternal:Mem:tlsSetI64(slot: 11, val: ncap);
		});
		local Int is stk: base:sysinternal:Mem:tlsGetI64(slot: 9);
		base:sysinternal:Mem:storeI64(ptr: stk, byteOffset: top * 8, val: addr);
		base:sysinternal:Mem:tlsSetI64(slot: 10, val: top + 1);
	}

	## Runs every registration above the innermost live barrier newest-first,
	## releasing each after its action runs, then pops the barrier. Safe
	## mid-unwind: the pending error is stashed while actions run (an
	## action's own calls must not observe a set pending error, or their
	## frames would unwind instantly) and restored afterwards.
	Function is frameExit(){
		local Int is top: base:sysinternal:Mem:tlsGetI64(slot: 10);
		if({ top == 0 }, { return; });
		local Int is stk: base:sysinternal:Mem:tlsGetI64(slot: 9);
		local Int is barrierIdx: -1;
		local Int is i: top - 1;
		while({ i >= 0 && barrierIdx == -1 }, {
			if({ base:sysinternal:Mem:loadI64(ptr: stk, byteOffset: i * 8) == 0 }, {
				barrierIdx: i;
			});
			i: i - 1;
		});
		local Int is stop: if({ barrierIdx == -1 }, { 0 }, { barrierIdx });
		local Int is pend: base:sysinternal:Mem:tlsGetI64(slot: 15);
		if({ pend != 0 }, {
			base:sysinternal:Mem:tlsSetI64(slot: 15, val: 0);
		});
		local Int is j: top - 1;
		while({ j >= stop }, {
			local Int is addr: base:sysinternal:Mem:loadI64(ptr: stk, byteOffset: j * 8);
			if({ addr != 0 }, {
				:invokeCleanup(cb: base:sysinternal:Mem:addrToObj(addr: addr));
				base:sysinternal:Mem:releaseAddr(objAddr: addr);
			});
			j: j - 1;
		});
		base:sysinternal:Mem:tlsSetI64(slot: 10, val: stop);
		if({ pend != 0 }, {
			base:sysinternal:Mem:tlsSetI64(slot: 15, val: pend);
		});
	}

	Function is threadCleanup(){
		local Int is top: base:sysinternal:Mem:tlsGetI64(slot: 10);
		local Int is stk: base:sysinternal:Mem:tlsGetI64(slot: 9);
		if({ stk != 0 }, {
			local Int is i: top - 1;
			while({ i >= 0 }, {
				local Int is addr: base:sysinternal:Mem:loadI64(ptr: stk, byteOffset: i * 8);
				if({ addr != 0 }, {
					base:sysinternal:Mem:releaseAddr(objAddr: addr);
				});
				i: i - 1;
			});
			base:sysinternal:Mem:free(ptr: stk);
			base:sysinternal:Mem:tlsSetI64(slot: 9, val: 0);
			base:sysinternal:Mem:tlsSetI64(slot: 10, val: 0);
			base:sysinternal:Mem:tlsSetI64(slot: 11, val: 0);
		});
	}
}
