#! Package base:sysinternal
#! Pure-Spec unmanaged floor for the thread-local deferred-cleanup stack.
##
## TLS slots in @_spec_tls_i64:
##   slot 9:  cleanup_stack (i64 address of i64[] closure-address buffer)
##   slot 10: cleanup_top   (i64 current stack depth)
##   slot 11: cleanup_cap   (i64 allocated slot capacity)
##
## Contract (consumed by the base:sys Defer wrapper and the frame-exit
## emission): a defer-ful frame snapshots `frameMark()` at entry. Deferred
## actions are pushed as retained closure objects — a registration OWNS its
## +1, so pool-drain timing can never dangle it. On ANY frame exit (normal
## or unwind) the frame calls `runTo(mark)`: every registration above the
## mark runs newest-first, each released right after it runs, leaving the
## stack at the mark. Actions must not raise (a raising action supersedes
## the in-flight unwind error and its remaining siblings stay registered,
## still owned) and must not register new cleanups.

Class is Defer{
	namespace: ['base', 'sysinternal'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', as Mem()],
		['base', 'sysinternal', as Conditional()],
		['base', 'sysinternal', as Loops()]
	];

	Function of Int is frameMark(){
		return Mem:tlsGetI64(slot: 10);
	}

	## Adopts a deferred action: retains the closure object (+1 owned by the
	## registration) and pushes it onto the thread's cleanup stack.
	Function is pushCleanup(Function is action){
		local Int is addr: Mem:objToAddr(obj: action);
		if({ addr == 0 }, { return; });
		Mem:retainAddr(objAddr: addr);
		local Int is top: Mem:tlsGetI64(slot: 10);
		local Int is cap: Mem:tlsGetI64(slot: 11);
		if({ top == cap }, {
			local Int is ncap: if({ cap == 0 }, { 8 }, { cap * 2 });
			local Int is ostk: Mem:tlsGetI64(slot: 9);
			local Int is nstk: Mem:realloc(ptr: ostk, bytes: ncap * 8);
			Mem:tlsSetI64(slot: 9, val: nstk);
			Mem:tlsSetI64(slot: 11, val: ncap);
		});
		local Int is stk: Mem:tlsGetI64(slot: 9);
		Mem:storeI64(ptr: stk, byteOffset: top * 8, val: addr);
		Mem:tlsSetI64(slot: 10, val: top + 1);
	}

	## Runs every cleanup above [mark] newest-first, releasing each
	## registration after its action runs. Safe mid-unwind: the pending
	## error is stashed while actions run (an action's own calls must not
	## observe a set pending error, or their frames would unwind instantly)
	## and restored afterwards.
	Function is runTo(Int is mark){
		local Int is top: Mem:tlsGetI64(slot: 10);
		if({ top <= mark }, { return; });
		local Int is pend: Mem:tlsGetI64(slot: 15);
		if({ pend != 0 }, {
			Mem:tlsSetI64(slot: 15, val: 0);
		});
		local Int is i: top - 1;
		while({ i >= mark }, {
			local Int is stk: Mem:tlsGetI64(slot: 9);
			local Int is addr: Mem:loadI64(ptr: stk, byteOffset: i * 8);
			if({ addr != 0 }, {
				Mem:storeI64(ptr: stk, byteOffset: i * 8, val: 0);
				:invokeCleanup(cb: Mem:addrToObj(addr: addr));
				Mem:releaseAddr(objAddr: addr);
			});
			i: i - 1;
		});
		Mem:tlsSetI64(slot: 10, val: mark);
		if({ pend != 0 }, {
			Mem:tlsSetI64(slot: 15, val: pend);
		});
	}

	local Function is invokeCleanup(Function is cb){
		cb();
	}

	Function is threadCleanup(){
		local Int is top: Mem:tlsGetI64(slot: 10);
		local Int is stk: Mem:tlsGetI64(slot: 9);
		if({ stk != 0 }, {
			local Int is i: top - 1;
			while({ i >= 0 }, {
				local Int is addr: Mem:loadI64(ptr: stk, byteOffset: i * 8);
				if({ addr != 0 }, {
					Mem:releaseAddr(objAddr: addr);
				});
				i: i - 1;
			});
			Mem:free(ptr: stk);
			Mem:tlsSetI64(slot: 9, val: 0);
			Mem:tlsSetI64(slot: 10, val: 0);
			Mem:tlsSetI64(slot: 11, val: 0);
		});
	}
}
