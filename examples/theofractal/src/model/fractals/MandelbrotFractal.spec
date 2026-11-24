#! Package theofractal:model:fractals
#! Mandelbrot set fractal implementation.

Class of EscapeFractal is MandelbrotFractal{
	replace [String] is namespace: ['theofractal', 'model', 'fractals'];

	merge [[String]] is using: [
		['theofractal', 'model', [EscapeFractal, FractalViewport]],
		['theofractal', 'util', FractalStrings]
	];

	replace Function of String is name(){ FractalStrings:OPT_MANDELBROT }

	replace Function of FractalViewport is defaultViewport(){
		FractalViewport(centerX: -0.5, centerY: 0.0, baseSpan: 2.6, zoom: 1.0)
	}

	replace Function of Float is evaluatePoint(Float is cr, Float is ci, Int is maxIter){
		local Float is q: ((cr - 0.25) * (cr - 0.25)) + (ci * ci);
		if({ (q * (q + (cr - 0.25))) <= (0.25 * ci * ci) }, { return -1.0; });
		if({ ((cr + 1.0) * (cr + 1.0)) + (ci * ci) <= 0.0625 }, { return -1.0; });
		local Float is zr: 0.0;
		local Float is zi: 0.0;
		local Float is zr2: 0.0;
		local Float is zi2: 0.0;
		local Int is iter: 0;
		while({ (iter < maxIter) && ((zr2 + zi2) <= 16.0) }, {
			zi: (2.0 * zr * zi) + ci;
			zr: (zr2 - zi2) + cr;
			zr2: zr * zr;
			zi2: zi * zi;
			iter: iter + 1;
		});
		if({ iter >= maxIter }, { return -1.0; });
		return smoothEscapeValue(iter: iter, mag2: zr2 + zi2);
	}
}
