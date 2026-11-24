#! specunit: suite

Class of SpecUnitTest is TestMandelbrot{

	replace [[String]] is using: [
		['specunit', SpecUnitTest],
		['specunit', as Assert()],
		[FractalMath]
	];

	Function is testInteriorAndExteriorEscape(){
		local FractalMath is fm: FractalMath();
		Assert:isTrue(fm:smoothEscape(cr: 0.0, ci: 0.0, maxIter: 50) < 0.0);
		Assert:isTrue(fm:smoothEscape(cr: 2.0, ci: 2.0, maxIter: 50) >= 0.0);
		Assert:areEqualInt(2, fm:pointsRendered);
	}

	Function is testClampAndShadeGlyph(){
		local FractalMath is fm: FractalMath();
		Assert:areEqualString(' ', fm:shadeGlyph(mu: -1.0));
		Assert:areEqualString('░', fm:shadeGlyph(mu: 0.0));
		Assert:isTrue(fm:clampFloat(v: 10.0, lo: 0.0, hi: 5.0) == 5.0);
		Assert:isTrue(fm:clampFloat(v: -2.0, lo: 0.0, hi: 5.0) == 0.0);
	}

}
