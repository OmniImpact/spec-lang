#! Package base:sys
#! Parallel fan-out execution over worker closures.

## Runs a worker closure across multiple threads and sums the results.
##
## Runtime-managed: [run] binds to the runtime's
## pthread trampoline. Workers must be pure functions of their two
## parameters (thread index and sample count): captured mutable variables
## share heap cells across all worker threads and must not be mutated
## concurrently without synchronization. Synchronization is provided by
## [sync] / [syncWith] or atomic primitives (`Process:atomicAdd` /
## `atomicPut` / `atomicGet`). Each thread receives a distinct, deterministic
## RNG seed.

Class is Parallel{
	namespace: ['base', 'sys'];

	## Executes [worker] across [threads] pthreads over [iterations] total work
	## units and returns the sum of all worker return values.
	##
	## Worker signature: `Function of Int is worker(Int is threadIndex, Int is count)`.
	##
	## @param threads: Number of pthreads to spawn (clamped to 1..64).
	## @param iterations: Total work units, split evenly across threads.
	## @param worker: Pure worker closure invoked once per thread.
	## @return: Sum of every worker's return value.
	Function of Int is run(Int is threads, Int is iterations, Function is worker){
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
