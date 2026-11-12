#! The named-argument contract for the bare if call: all three (and the
#! four-argument finally form) may be passed BY NAME — check:, then:,
#! else:, finally: — because those are the parameter names on
#! Conditional.if. Locks the capability after a misdiagnosis claimed
#! the bare 3-arg if was positional-only: what tripped the mixed-args
#! rule in the original report was a genuinely mixed call (two
#! positional arguments plus a named else), which §I.3 correctly
#! rejects. All-named never trips.

Class is TestNamedElse{

	replace Array of Array of String is using: [
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', as Conditional()]
	];

	Function is testThenBranchByName(){
		local Int is v: 0;
		if(check: { v == 0 }, then: {
			v: 1;
		}, else: {
			v: 2;
		});
		Assert:areEqualInt(1, v);
	}

	Function is testElseBranchByName(){
		local Int is v: 5;
		if(check: { v == 0 }, then: {
			v: 1;
		}, else: {
			v: 2;
		});
		Assert:areEqualInt(2, v);
	}

	Function is testFinallyByName(){
		local Int is v: 0;
		local Int is cleanup: 0;
		if(check: { v == 0 }, then: {
			v: 1;
		}, else: {
			v: 2;
		}, finally: {
			cleanup: 9;
		});
		Assert:areEqualInt(1, v);
		Assert:areEqualInt(9, cleanup);
	}
}
