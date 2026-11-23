#! Package base:sys
#! Parallel fan-out execution over worker closures, built on ThreadScope.

## Runs a worker closure across multiple threads inside a [ThreadScope] and sums the results.
##
## Synchronization is provided by [sync] / [syncWith] or atomic primitives
## (`Process:atomicAdd` / `atomicPut` / `atomicGet`). Each thread receives a
## distinct, deterministic RNG seed.

Class is Parallel{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task],
		['base', 'sys', as Defer()],
		['base', 'sys', as Thread()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'struct', Map]
	];

	held Int is tableMutex: Thread:mutexCreate();
	held Map of Int to Int is lockSlots: Map:init();

	local Function of Int is getLockSlot(Int is key){
		Thread:mutexLock(handle: Parallel:tableMutex);
		local Int is slot: 0;
		if({ Parallel:lockSlots:has(key: key) }, {
			slot: Parallel:lockSlots:get(key: key, default: 0);
		}, {
			slot: Mem:alloc(bytes: 24);
			Mem:storeI64(ptr: slot, byteOffset: 0, val: Thread:mutexCreate());
			Mem:storeI64(ptr: slot, byteOffset: 8, val: 0);
			Mem:storeI64(ptr: slot, byteOffset: 16, val: 0);
			Parallel:lockSlots:set(key: key, value: slot);
		});
		Thread:mutexUnlock(handle: Parallel:tableMutex);
		return slot;
	}

	local Function of Int is invokeWorker(Function is w, Int is tid, Int is cnt){
		local Any is res: w(tid, cnt);
		return Mem:objToAddr(obj: res);
	}

	## Executes [worker] across [threads] OS threads inside [scope] over
	## [iterations] total work units and returns the sum of all worker return values.
	##
	## Worker signature: `Function of Int is worker(Int is threadIndex, Int is count)`.
	##
	## @param scope: Active [ThreadScope] in which worker tasks are spawned.
	## @param threads: Number of threads to spawn (no upper-bound clamp).
	## @param iterations: Total work units, split evenly across threads.
	## @param worker: Worker closure invoked once per thread.
	## @return: Sum of every worker's return value.
	Function of Int is run(ThreadScope is scope, Int is threads, Int is iterations, Function is worker){
		local Int is wAddr: Mem:objToAddr(obj: worker);
		if({ wAddr == 0 || Mem:loadI64(ptr: wAddr, byteOffset: 0) == 0 }, {
			return 0;
		});
		local Int is nThreads: if({ threads < 1 }, { 1 }, { threads });
		local Int is baseCount: iterations / nThreads;
		local Int is rem: iterations % nThreads;
		local Array of Task of Int is tasks: Array();
		local Int is i: 0;
		while({ i < nThreads }, {
			local Int is tid: i;
			local Int is cnt: baseCount + if({ tid < rem }, { 1 }, { 0 });
			local Task of Int is t: scope:spawn(task: local Function of Int(){
				return :invokeWorker(w: worker, tid: tid, cnt: cnt);
			});
			tasks:add(item: t);
			i: i + 1;
		});
		local Int is total: 0;
		local Int is k: 0;
		while({ k < tasks:length() }, {
			local Task of Int is tk: tasks:get(index: k);
			total: total + tk:await();
			k: k + 1;
		});
		return total;
	}

	## Executes [action] inside a critical section synchronized across all worker
	## threads using a recursive mutex. Safely guards access and mutation of captured
	## heap cells or shared state.
	##
	## @param action: Closure to execute under mutual exclusion.
	## @return: Value returned by [action], or void if none.
	Function of Any is sync(Function is action){
		return :syncWith(lock: 0, action: action);
	}

	## Executes [action] inside a critical section locked specifically on [lock].
	## Distinct lock keys map to dynamically allocated recursive mutex slots, allowing
	## fine-grained concurrency across disjoint data structures or slots.
	##
	## @param lock: Integer key designating the lock slot.
	## @param action: Closure to execute under mutual exclusion for [lock].
	## @return: Value returned by [action], or void if none.
	Function of Any is syncWith(Int is lock, Function is action){
		local Int is aAddr: Mem:objToAddr(obj: action);
		if({ aAddr == 0 || Mem:loadI64(ptr: aAddr, byteOffset: 0) == 0 }, {
			return Mem:addrToObj(addr: 0);
		});
		local Int is slot: :getLockSlot(key: lock);
		local Int is tid: Thread:currentId();
		if({ Mem:atomicLoadI64(addr: slot + 8) == tid }, {
			# Reentrant: the depth counter rises for this frame and is
			# restored by a deferred cleanup, so an unwinding action cannot
			# strand the count.
			local Int is depth: Mem:loadI64(ptr: slot, byteOffset: 16);
			Mem:storeI64(ptr: slot, byteOffset: 16, val: depth + 1);
			Defer:push(action: local Function(){
				Mem:storeI64(ptr: slot, byteOffset: 16, val: Mem:loadI64(ptr: slot, byteOffset: 16) - 1);
			});
			local Any is resInner: action();
			return resInner;
		});
		local Int is mtx: Mem:loadI64(ptr: slot, byteOffset: 0);
		Thread:mutexLock(handle: mtx);
		Mem:atomicStoreI64(addr: slot + 8, val: tid);
		Mem:storeI64(ptr: slot, byteOffset: 16, val: 1);
		# The lock and its bookkeeping are released by a deferred cleanup,
		# which runs on the normal return AND on an unwinding action before
		# the error propagates outward — a raising action can no longer
		# deadlock every later entrant.
		Defer:push(action: local Function(){
			Mem:storeI64(ptr: slot, byteOffset: 16, val: 0);
			Mem:atomicStoreI64(addr: slot + 8, val: 0);
			Thread:mutexUnlock(handle: mtx);
		});
		local Any is res: action();
		return res;
	}
}
