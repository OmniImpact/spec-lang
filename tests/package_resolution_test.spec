#! Package resolution regression: array-form using with a bare class
#! terminator discovered against the input-directory scan root.

Class is PackageResolutionTest{

	replace Array of Array of String is using: [
		['pkgres', 'widget', Widget],
		['base', 'sys', as Output()],
		['base', 'sys', as Conditional()]
	];

	replace Function is init(Map of String to String is args){
		Output:line('=== Package Resolution Test ===');
		local Widget is w: Widget:init();
		local String is msg: w:speak();
		Conditional:if(check: { msg == 'widget online' }, then: {
			Output:line('[PASS] array-form using resolved the class from the package tree');
		}, else: {
			Output:line('[FAIL] package resolution: ' . msg);
		});
	}
}
