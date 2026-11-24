#! Package theofractal:model:fractals
#! Julia set fractal implementation (`c = -0.7 + 0.27015i`).

Class of EscapeFractal is JuliaFractal{
	replace [String] is namespace: ['theofractal', 'model', 'fractals'];

	merge [[String]] is using: [
		['theofractal', 'model', [EscapeFractal, FractalViewport]],
		['theofractal', 'util', FractalStrings]
	];

	replace Function of String is name(){ FractalStrings:OPT_JULIA }

	replace Function of FractalViewport is defaultViewport(){
		FractalViewport(centerX: 0.0, centerY: 0.0, baseSpan: 2.6, zoom: 1.0)
	}

	replace Function of Float is evaluatePoint(Float is cr, Float is ci, Int is maxIter){
		local Float is jc: -0.7;
		local Float is ji: 0.27015;
		local Float is zr: cr;
		local Float is zi: ci;
		local Float is zr2: zr * zr;
		local Float is zi2: zi * zi;
		local Int is iter: 0;
		while({ (iter < maxIter) && ((zr2 + zi2) <= 16.0) }, {
			zi: (2.0 * zr * zi) + ji;
			zr: (zr2 - zi2) + jc;
			zr2: zr * zr;
			zi2: zi * zi;
			iter: iter + 1;
		});
		if({ iter >= maxIter }, { return -1.0; });
		return smoothEscapeValue(iter: iter, mag2: zr2 + zi2);
	}
}
