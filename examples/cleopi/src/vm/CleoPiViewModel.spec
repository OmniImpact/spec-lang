#! Package cleopi:vm
#! ViewModel managing parallel Monte Carlo Pi state, formatting, and worker execution.

## Owns benchmark configuration, [PiTelemetry], formatted presentation getters, and [Parallel] orchestration.
Class is CleoPiViewModel{
	replace [String] is namespace: ['cleopi', 'vm'];

	merge [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'math', as Math()],
		['base', 'sys', [Parallel, as Process()]],
		['base', 'sys', 'thread', ThreadScope],
		['cleopi', 'model', [PiStats, PiTelemetry]]
	];

	Int is threads: 4;
	Int is points: 1000000000;
	Int is refreshMs: 40;
	Int is gridWidth: 44;
	Int is gridHeight: 20;

	PiTelemetry is telemetry: PiTelemetry();
	local PiStats is stats: PiStats();

	Int is startedAtMs: 0;
	Int is curSamples: 0;
	Int is curHits: 0;
	Int is nowMs: 0;

	Function is onStateChanged: {};

	replace Function is init(
		Int is threads: 4,
		Int is points: 1000000000,
		Int is refreshMs: 40,
		Int is gridWidth: 44,
		Int is gridHeight: 20
	){
		local Int is t: threads;
		if({ t < 1 }, { t: 1; });
		if({ t > 16 }, { t: 16; });
		:threads: t;
		:points: points;
		:refreshMs: refreshMs;
		:gridWidth: gridWidth;
		:gridHeight: gridHeight;
		telemetry:reset(threads: t);
	}

	Function of String is domainTitle(){ " Unit Circle Domain ({{threads}} threads · {{points}} pts) " }

	Function of String is workersTitle(){ " Workers ({{threads}} threads) " }

	Function of String is workerBarText(){
		local String is boxes: '';
		local Int is wi: 0;
		while({ wi < threads }, {
			if({ wi > 0 }, { boxes: "{{boxes}} "; });
			if({ telemetry:isWorkerActive(threadIndex: wi) }, {
				boxes: "{{boxes}}■";
			}, {
				boxes: "{{boxes}}□";
			});
			wi: wi + 1;
		});
		return boxes;
	}

	Function of String is workerCountText(){
		local Int is activeCount: 0;
		local Int is wi: 0;
		while({ wi < threads }, {
			if({ telemetry:isWorkerActive(threadIndex: wi) }, {
				activeCount: activeCount + 1;
			});
			wi: wi + 1;
		});
		return "{{activeCount}}/{{threads}} active";
	}

	Function of String is piEstimateText(){
		local Float is pi: stats:estimatePi(hits: curHits, samples: curSamples);
		return "Pi ≈ {{stats:piText(value: pi)}}";
	}

	Function of String is piErrorText(){
		local Float is pi: stats:estimatePi(hits: curHits, samples: curSamples);
		local Float is err: abs(value: pi - 3.14159265358979);
		return "error {{stats:piText(value: err)}}";
	}

	Function of String is samplesText(){ "Samples: {{curSamples}} · Hits: {{curHits}}" }

	Function of String is throughputText(){
		local Int is elapsed: nowMs - startedAtMs;
		local Int is perSec: if({ elapsed > 0 }, { (curSamples * 1000) / elapsed }, { 0 });
		return "{{elapsed}} ms · {{perSec}} pts/sec";
	}

	Function of String is progressText(){ "{{curSamples}}/{{points}} points" }

	Function of Float is progressFraction(){
		if({ points <= 0 }, { return 1.0; });
		local Float is pct: toFloat(value: curSamples) / toFloat(value: points);
		if({ pct > 1.0 }, { return 1.0; });
		return pct;
	}

	## Updates the snapshot and notifies [onStateChanged].
	Function is syncSnapshot(Int is samples, Int is hits, Int is timestampMs){
		curSamples: samples;
		curHits: hits;
		nowMs: timestampMs;
		onStateChanged();
	}

	## Runs the parallel Monte Carlo benchmark, invoking [onStart] and [onFinish] on the [ThreadScope].
	Function is run(Function is onStart, Function is onFinish){
		telemetry:reset(threads: threads);
		startedAtMs: clockMs();
		curSamples: 0;
		curHits: 0;
		nowMs: startedAtMs;

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
						syncSnapshot(samples: telemetry:samples(), hits: telemetry:hits(), timestampMs: now);
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
				onStart(scope);
				totalHits: par:run(scope: scope, threads: threads, iterations: points, worker: sampler);
				syncSnapshot(samples: points, hits: totalHits, timestampMs: clockMs());
				onFinish();
			},
			onError: local Function of Boolean(SpecError is _err){ false }
		);
	}
}
