#! Package examples:regression
#! Tracks parallel fan-out execution and atomic slots.

## Parallel execution and atomic slot semantics.
##
## Guarded behavior:
## - Parallel:run sums worker return values exactly across threads.
## - Work is split so the sum of per-thread counts equals the total iterations.
## - Atomic add is associative and exact under concurrent workers.
## - fastRandom stays within [0, 1) and produces varying values.
## - All checks print "[PASS]"; any "[FAIL]" is a regression.

Class is ParallelAtomicsTest{

	replace Array of Array of String is using: [
		['base', 'io', Output],
		['base', 'sys', Process],
		['base', 'sys', Parallel],
		['base', 'math', Math],
	];

	replace Function is init(Map of String to String is args){
		output:line('=== Regression: Parallel & Atomics ===');

		# Case 1: exact sum - each worker returns its count, total == iterations.
		local Function of Int is counter: local Function of Int(Int is threadIndex, Int is count){
			return count;
		};
		local Int is total: Parallel:run(threads: 4, iterations: 1000, worker: counter);
		if (total == 1000) {
			output:line('[PASS] parallel sum: 4 threads over 1000 = 1000');
		} else {
			output:line('[FAIL] parallel sum: expected 1000, got ' . total);
		}

		# Case 2: thread indices cover 0..N-1 exactly (atomic counters per thread).
		Process:atomicPut(slot: 40, value: 0);
		local Function of Int is marker: local Function of Int(Int is threadIndex, Int is count){
			Process:atomicAdd(slot: 40, value: threadIndex + 1);
			return 0;
		};
		Parallel:run(threads: 4, iterations: 4, worker: marker);
		local Int is indexSum: Process:atomicGet(slot: 40);
		if (indexSum == 10) {
			output:line('[PASS] thread indices: 1+2+3+4 = 10');
		} else {
			output:line('[FAIL] thread indices: expected 10, got ' . indexSum);
		}

		# Case 3: concurrent atomic add is exact.
		Process:atomicPut(slot: 41, value: 0);
		local Function of Int is adder: local Function of Int(Int is threadIndex, Int is count){
			local Int is j: 0;
			While:condition(
				evaluate: local Function of Boolean(){ return j < count; },
				iteration: local Function(){
					Process:atomicAdd(slot: 41, value: 1);
					j: j + 1;
				}
			);
			return 0;
		};
		Parallel:run(threads: 4, iterations: 400, worker: adder);
		local Int is added: Process:atomicGet(slot: 41);
		if (added == 400) {
			output:line('[PASS] concurrent atomicAdd: 400 of 400 increments');
		} else {
			output:line('[FAIL] concurrent atomicAdd: expected 400, got ' . added);
		}

		# Case 4: fastRandom range and variance.
		local Int is inRange: 0;
		local Int is distinct: 0;
		local Float is last: -1.0;
		local Int is k: 0;
		While:condition(
			evaluate: local Function of Boolean(){ return k < 1000; },
			iteration: local Function(){
				local Float is r: math:fastRandom();
				if (r >= 0.0 && r < 1.0) {
					inRange: inRange + 1;
				}
				if (r != last) {
					distinct: distinct + 1;
				}
				last: r;
				k: k + 1;
			}
		);
		if (inRange == 1000 && distinct > 990) {
			output:line('[PASS] fastRandom: 1000 in range, ' . distinct . ' distinct');
		} else {
			output:line('[FAIL] fastRandom: ' . inRange . ' in range, ' . distinct . ' distinct');
		}

		output:line('=== End Parallel & Atomics ===');
	}

}
