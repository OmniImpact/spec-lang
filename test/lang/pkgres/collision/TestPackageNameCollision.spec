#! specunit: suite

Class of SpecUnitTest is TestPackageNameCollision{
	replace [String] is namespace: ['test', 'lang', 'pkgres', 'collision'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['test', 'lang', 'pkgres', 'collision', 'alpha', AlphaUser],
		['test', 'lang', 'pkgres', 'collision', 'beta', BetaUser]
	];

	Function is testSameShortNameInDifferentPackages(){
		local AlphaUser is au: AlphaUser();
		local BetaUser is bu: BetaUser();
		Assert:areEqualInt(42, au:run());
		Assert:areEqualString('second', bu:run());
	}
}
