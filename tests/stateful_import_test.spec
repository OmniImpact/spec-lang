#! Regression: field-ful as-imports (§10). The import
#! materializes a hidden field, constructed with the as-form's literal
#! arguments; state persists across prefixed calls, dispatches through
#! the field, and bare calls resolve to the same instance.

Class is StatefulImportTest {
	replace Array of Array of String is using: [
		['base', 'sys', as Output()],
		['instimport', 'counter', as StatefulCounter(label: 'owned')],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args) {
		Output:line('=== Instance-Import: Field-Ful Classes ===');
		StatefulCounter:tick();
		StatefulCounter:tick();
		StatefulCounter:tick();
		local String is first: StatefulCounter:report();
		tick();
		local String is second: StatefulCounter:report();
		Conditional:if(check: { first == 'owned=3' && second == 'owned=4' }, then: {
			Output:line('[PASS] field-ful import: state persists, bare and prefixed calls share the instance');
		}, else: {
			Output:line('[FAIL] field-ful import: ' . first . ' / ' . second);
		});
	}
}
