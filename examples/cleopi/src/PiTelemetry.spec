#! Atomic shared-slot telemetry for parallel Monte Carlo Pi workers.

## Encapsulates atomic slot offsets for sample/hit totals, worker coordinates, and active flags.
Class is PiTelemetry{
	merge [[String]] is using: [
		['base', 'sys', as Process()]
	];

	local Int is SLOT_SAMPLES: 0;
	local Int is SLOT_HITS: 1;
	local Int is SLOT_COORDS_BASE: 2;
	local Int is SLOT_ACTIVE_BASE: 100;

	## Resets all counters and initializes [threads] worker slots to centered idle state.
	Function is reset(Int is threads){
		atomicPut(slot: SLOT_SAMPLES, value: 0);
		atomicPut(slot: SLOT_HITS, value: 0);
		local Int is wi: 0;
		while({ wi < threads }, {
			atomicPut(slot: SLOT_COORDS_BASE + wi * 2, value: 500);
			atomicPut(slot: SLOT_COORDS_BASE + wi * 2 + 1, value: 500);
			atomicPut(slot: SLOT_ACTIVE_BASE + wi, value: 0);
			wi: wi + 1;
		});
	}

	## Atomically adds a completed batch's [batchSamples] and [batchHits] to the global totals.
	Function is recordBatch(Int is batchSamples, Int is batchHits){
		atomicAdd(slot: SLOT_SAMPLES, value: batchSamples);
		atomicAdd(slot: SLOT_HITS, value: batchHits);
	}

	## Updates the normalized `[0, 1000)` position of [threadIndex].
	Function is setWorkerPos(Int is threadIndex, Int is x, Int is y){
		atomicPut(slot: SLOT_COORDS_BASE + threadIndex * 2, value: x);
		atomicPut(slot: SLOT_COORDS_BASE + threadIndex * 2 + 1, value: y);
	}

	## Marks [threadIndex] as active (`1`) or idle (`0`).
	Function is setWorkerActive(Int is threadIndex, Boolean is active){
		local Int is flag: 0;
		if({ active }, { flag: 1; });
		atomicPut(slot: SLOT_ACTIVE_BASE + threadIndex, value: flag);
	}

	Function of Int is samples(){ atomicGet(slot: SLOT_SAMPLES) }

	Function of Int is hits(){ atomicGet(slot: SLOT_HITS) }

	Function of Int is workerX(Int is threadIndex){ atomicGet(slot: SLOT_COORDS_BASE + threadIndex * 2) }

	Function of Int is workerY(Int is threadIndex){ atomicGet(slot: SLOT_COORDS_BASE + threadIndex * 2 + 1) }

	Function of Boolean is isWorkerActive(Int is threadIndex){ atomicGet(slot: SLOT_ACTIVE_BASE + threadIndex) != 0 }
}
