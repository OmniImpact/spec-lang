#! specunit: suite

Class of SpecUnitTest is TestPiBenchmark{

	replace [[String]] is using: [
		['specunit', SpecUnitTest],
		['specunit', as Assert()],
		[PiStats]
	];

	Function is testEstimatePiAndFormat(){
		local PiStats is st: PiStats();
		local Float is pi: st:estimatePi(hits: 785, samples: 1000);
		Assert:areEqualString('3.140', st:piText(value: pi));
		Assert:areEqualString('0.000', st:piText(value: st:estimatePi(hits: 0, samples: 0)));
	}

	Function is testBarAndBoxed(){
		local PiStats is st: PiStats();
		Assert:areEqualString('═══', st:bar(width: 3));
		local String is row: st:boxed(inner: 'Hi', width: 8);
		Assert:areEqualString('║ Hi    ║', row);
	}

}
