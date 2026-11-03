#! Package base:sys
#! Provides parallel fan-out execution over worker closures.

## Runs a worker closure across multiple threads and sums the results.
##
## Workers must be pure functions of their two parameters (thread index and
## sample count): captured variables are shared static slots and must not be
## mutated from worker threads. Communication happens through atomic slots
## (`Process:atomicAdd` / `atomicPut` / `atomicGet`) and the worker's return
## value. Each thread receives a distinct, deterministic RNG seed.
Class is Parallel{

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
}
