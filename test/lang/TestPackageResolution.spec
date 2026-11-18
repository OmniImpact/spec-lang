#! SpecUnit sweep (from package_resolution_test.spec): array-form using
#! with a bare class terminator discovered against the input-directory
#! scan root.

Class of SpecUnitTest is TestPackageResolution{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['pkgres', 'widget', Widget]
	];

	## The array-form using resolved the class from the package tree:
	## construct it and dispatch into the imported file's method.
	Function is testArrayFormUsingResolution(){
		local Widget is w: Widget:init();
		local String is msg: w:speak();
		Assert:areEqualString('widget online', msg);
	}
}
