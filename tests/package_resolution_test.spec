#! Package resolution regression: array-form using with a bare class
#! terminator discovered against the input-directory scan root.

Class is PackageResolutionTest{

	replace Array of Array of String is using: [
		['pkgres', 'widget', Widget]
	];

	replace Function is init(Map of String to String is args){
		output:line('=== Package Resolution Test ===');
		local Widget is w: Widget:init();
		local String is msg: w:speak();
		if (msg == 'widget online') {
			output:line('[PASS] array-form using resolved the class from the package tree');
		} else {
			output:line('[FAIL] package resolution: ' . msg);
		}
	}
}
