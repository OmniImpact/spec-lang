#! Monte Carlo Pi benchmark with live Cleo terminal UI, parallel sampling, and worker telemetry.

## CLI entry point coordinating parallel Monte Carlo Pi sampling and live [CleoDashboard] updates.
Class is CleoPi{
	merge [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'math', as Math()],
		['base', 'sys', [Parallel, as Process()]],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'struct', Map],
		[CleoDashboard],
		[DomainGrid],
		[PiTelemetry]
	];

	## Entry point; reads optional [args] (`threads`, `points`, `refresh`) and runs the parallel benchmark.
	replace Function is init(Map of String to String is args){
		local Int is threads: args:getInt(key: 'threads', default: 4);
		local Int is points: args:getInt(key: 'points', default: 1_000_000_000);
		local Int is refreshMs: args:getInt(key: 'refresh', default: 40);

		if({ threads < 1 }, { threads: 1; });
		if({ threads > 16 }, { threads: 16; });

		local PiTelemetry is telemetry: PiTelemetry();
		telemetry:reset(threads: threads);

		local DomainGrid is grid: DomainGrid(width: 44, height: 20);
		local CleoDashboard is dashboard: CleoDashboard(
			threads: threads,
			points: points,
			startedAtMs: clockMs(),
			grid: grid,
			telemetry: telemetry
		);

		local Function of Int is sampler: local Function of Int(Int is threadIndex, Int is count){
			telemetry:setWorkerActive(threadIndex: threadIndex, active: true);
			local Int is hits: 0;
			local Int is done: 0;
			local Int is batch: count / 100 + 1;
			local Int is lastX: 500;
			local Int is lastY: 500;
			local Int is lastHits: 0;
			local Int is lastDraw: clockMs();

			while({ done < count }, {
				local Int is b: 0;
				while({ b < batch && done < count }, {
					local Float is x: fastRandom();
					local Float is y: fastRandom();
					if({ (x * x + y * y) <= 1.0 }, {
						hits: hits + 1;
					});
					lastX: toInt(value: x * 1000.0);
					lastY: toInt(value: y * 1000.0);
					done: done + 1;
					b: b + 1;
				});
				telemetry:recordBatch(batchSamples: batch, batchHits: hits - lastHits);
				lastHits: hits;
				telemetry:setWorkerPos(threadIndex: threadIndex, x: lastX, y: lastY);

				if({ threadIndex == 0 }, {
					local Int is now: clockMs();
					if({ now - lastDraw >= refreshMs }, {
						dashboard:sync(curSamples: telemetry:samples(), curHits: telemetry:hits(), nowMs: now, telemetry: telemetry);
						lastDraw: now;
					});
				});
			});
			telemetry:setWorkerActive(threadIndex: threadIndex, active: false);
			return hits;
		};

		local Parallel is par: Parallel();
		local Int is totalHits: 0;
		ThreadScope:open(
			body: local Function(ThreadScope is scope){
				dashboard:start(scope: scope);
				totalHits: par:run(scope: scope, threads: threads, iterations: points, worker: sampler);
				dashboard:sync(curSamples: points, curHits: totalHits, nowMs: clockMs(), telemetry: telemetry);
				dashboard:finish();
			},
			onError: local Function of Boolean(SpecError is _err){ false }
		);
	}
}
