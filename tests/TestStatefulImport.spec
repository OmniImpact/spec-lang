#! SpecUnit sweep (from stateful_import_test.spec): field-ful as-imports
#! (§10). The import materializes a hidden field, constructed with the
#! as-form's literal arguments; state persists across prefixed calls,
#! dispatches through the field, and bare calls resolve to the same
#! instance.

Class of SpecUnitTest is TestStatefulImport{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['instimport', 'counter', as StatefulCounter(label: 'owned')]
	];

	## The old suite's exact sequence: three prefixed ticks report
	## 'owned=3', then one BARE tick reports 'owned=4' — the bare call
	## resolved to the same hidden field instance, and state persisted.
	Function is testFieldFulImportStatePersists(){
		StatefulCounter:tick();
		StatefulCounter:tick();
		StatefulCounter:tick();
		local String is first: StatefulCounter:report();
		tick();
		local String is second: StatefulCounter:report();
		Assert:areEqualString('owned=3', first);
		Assert:areEqualString('owned=4', second);
	}
}
