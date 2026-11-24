#! specunit: suite

Class of SpecUnitTest is TestCleoPi{
	replace [String] is namespace: ['cleopi', 'tests'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['cleopi', 'model', [PiStats, PiTelemetry]],
		['cleopi', 'vm', CleoPiViewModel],
		['cleopi', 'view', DomainGrid]
	];

	Function is testEstimatePiAndFormat(){
		local PiStats is st: PiStats();
		local Float is pi: st:estimatePi(hits: 785, samples: 1000);
		Assert:areEqualString('3.140', st:piText(value: pi));
		Assert:areEqualString('0.000', st:piText(value: st:estimatePi(hits: 0, samples: 0)));
	}

	Function is testViewModelTelemetryAndDomainGrid(){
		local CleoPiViewModel is vm: CleoPiViewModel(threads: 2, points: 1000, gridWidth: 10, gridHeight: 10);
		Assert:isFalse(vm:telemetry:isWorkerActive(threadIndex: 0));

		vm:telemetry:setWorkerActive(threadIndex: 0, active: true);
		vm:telemetry:setWorkerPos(threadIndex: 0, x: 500, y: 500);
		vm:syncSnapshot(samples: 250, hits: 196, timestampMs: vm:startedAtMs + 500);

		Assert:isTrue(vm:telemetry:isWorkerActive(threadIndex: 0));
		Assert:areEqualString('■ □', vm:workerBarText());
		Assert:areEqualString('1/2 active', vm:workerCountText());
		Assert:areEqualString('Samples: 250 · Hits: 196', vm:samplesText());
		Assert:areEqualString('250/1000 points', vm:progressText());
		Assert:areClose(0.25, vm:progressFraction(), 0.001);

		local DomainGrid is grid: DomainGrid(width: 10, height: 10);
		Assert:areEqualInt(0, grid:markerAt(col: 5, row: 5, threads: 2, telemetry: vm:telemetry));
		Assert:isTrue(grid:renderRow(row: 5, threads: 2, telemetry: vm:telemetry):length() > 0);
	}
}
