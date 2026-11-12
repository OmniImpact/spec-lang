#! Package examples:regression
#! SpecUnit sweep (from parallel_atomics_test.spec): parallel fan-out and
#! atomic slots — the sum of worker returns equals the iteration count,
#! thread indices cover 0..N-1 exactly, concurrent atomicAdd is exact,
#! and fastRandom stays in [0, 1) with variance.

Class of SpecUnitTest is TestParallelAtomics{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', Output],
		['base', 'sys', Process],
		['base', 'sys', Parallel],
		['base', 'math', Math],
		['base', 'math', as Math()],
		['base', 'sys', as Output()],
		['base', 'sys', as Parallel()],
		['base', 'sys', as Process()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	## Case 1: exact sum — each worker returns its count, total == iterations.
	Function is testParallelSumExact(){
		local Function of Int is counter: local Function of Int(Int is threadIndex, Int is count){
			return count;
		};
		local Int is total: Parallel:run(threads: 4, iterations: 1000, worker: counter);
		Assert:areEqualInt(1000, total);
	}

	## Case 2: thread indices cover 0..N-1 exactly (atomic counters per thread).
	Function is testThreadIndicesCovered(){
		Process:atomicPut(slot: 40, value: 0);
		local Function of Int is marker: local Function of Int(Int is threadIndex, Int is count){
			Process:atomicAdd(slot: 40, value: threadIndex + 1);
			return 0;
		};
		Parallel:run(threads: 4, iterations: 4, worker: marker);
		local Int is indexSum: Process:atomicGet(slot: 40);
		Assert:areEqualInt(10, indexSum);
	}

	## Case 3: concurrent atomic add is exact.
	Function is testConcurrentAtomicAddExact(){
		Process:atomicPut(slot: 41, value: 0);
		local Function of Int is adder: local Function of Int(Int is threadIndex, Int is count){
			local Int is j: 0;
			while(
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
		Assert:areEqualInt(400, added);
	}

	## Case 4: fastRandom range and variance — every draw in [0, 1),
	## draws vary from the previous one.
	Function is testFastRandomRangeAndVariance(){
		local Int is inRange: 0;
		local Int is distinct: 0;
		local Float is last: -1.0;
		local Int is k: 0;
		while(
			evaluate: local Function of Boolean(){ return k < 1000; },
			iteration: local Function(){
				local Float is r: Math:fastRandom();
				Conditional:if(check: { r >= 0.0 && r < 1.0 }, then: {
					inRange: inRange + 1;
				});
				Conditional:if(check: { r != last }, then: {
					distinct: distinct + 1;
				});
				last: r;
				k: k + 1;
			}
		);
		Assert:areEqualInt(1000, inRange);
		Assert:isTrue(distinct > 990);
	}
}
