#! Package theofractal:model:fractals
#! Burning Ship fractal implementation.

Class of EscapeFractal is BurningShipFractal{
	replace [String] is namespace: ['theofractal', 'model', 'fractals'];

	merge [[String]] is using: [
		['theofractal', 'model', [EscapeFractal, FractalViewport]],
		['theofractal', 'util', FractalStrings]
	];

	replace Function of String is name(){ FractalStrings:OPT_BURNING_SHIP }

	replace Function of FractalViewport is defaultViewport(){
		FractalViewport(centerX: -0.45, centerY: -0.55, baseSpan: 2.8, zoom: 1.0)
	}

	replace Function of Float is evaluatePoint(Float is cr, Float is ci, Int is maxIter){
		local Float is zr: 0.0;
		local Float is zi: 0.0;
		local Float is zr2: 0.0;
		local Float is zi2: 0.0;
		local Int is iter: 0;
		while({ (iter < maxIter) && ((zr2 + zi2) <= 16.0) }, {
			local Float is azr: if({ zr < 0.0 }, { -zr }, { zr });
			local Float is azi: if({ zi < 0.0 }, { -zi }, { zi });
			zi: (2.0 * azr * azi) + ci;
			zr: (zr2 - zi2) + cr;
			zr2: zr * zr;
			zi2: zi * zi;
			iter: iter + 1;
		});
		if({ iter >= maxIter }, { return -1.0; });
		return smoothEscapeValue(iter: iter, mag2: zr2 + zi2);
	}
}
