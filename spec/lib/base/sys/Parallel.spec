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
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array]
	];

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
		local Array of Task of Int is tasks: [];
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
	}

	## Executes [action] inside a critical section locked specifically on [lock].
	## Distinct lock keys map to striped recursive mutexes (64 stripes), allowing
	## fine-grained concurrency across disjoint data structures or slots.
	##
	## @param lock: Integer key designating the lock stripe.
	## @param action: Closure to execute under mutual exclusion for [lock].
	## @return: Value returned by [action], or void if none.
	Function of Any is syncWith(Int is lock, Function is action){
	}
}
