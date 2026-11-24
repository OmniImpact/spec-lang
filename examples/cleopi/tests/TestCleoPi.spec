#! specunit: suite

Class of SpecUnitTest is TestCleoPi{
	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		[DomainGrid],
		[PiStats],
		[PiTelemetry]
	];

	Function is testEstimatePiAndFormat(){
		local PiStats is st: PiStats();
		local Float is pi: st:estimatePi(hits: 785, samples: 1000);
		Assert:areEqualString('3.140', st:piText(value: pi));
		Assert:areEqualString('0.000', st:piText(value: st:estimatePi(hits: 0, samples: 0)));
	}

	Function is testTelemetryAndDomainGrid(){
		local PiTelemetry is telemetry: PiTelemetry();
		telemetry:reset(threads: 2);
		Assert:isFalse(telemetry:isWorkerActive(threadIndex: 0));

		telemetry:setWorkerActive(threadIndex: 0, active: true);
		telemetry:setWorkerPos(threadIndex: 0, x: 500, y: 500);
		telemetry:recordBatch(batchSamples: 100, batchHits: 78);

		Assert:isTrue(telemetry:isWorkerActive(threadIndex: 0));
		Assert:areEqualInt(100, telemetry:samples());
		Assert:areEqualInt(78, telemetry:hits());

		local DomainGrid is grid: DomainGrid(width: 10, height: 10);
		Assert:areEqualInt(0, grid:markerAt(col: 5, row: 5, threads: 2, telemetry: telemetry));
		Assert:isTrue(grid:renderRow(row: 5, threads: 2, telemetry: telemetry):length() > 0);
	}
}
