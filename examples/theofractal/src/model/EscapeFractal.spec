#! Package theofractal:model
#! Shared base class for smooth escape-time complex-plane fractals (Mandelbrot, Julia, Burning Ship).

Class of Fractal is EscapeFractal{
	replace [String] is namespace: ['theofractal', 'model'];

	merge [[String]] is using: [
		['theofractal', 'model', [Fractal, FractalViewport]],
		['base', 'math', as Math()],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	## Override to evaluate smooth escape count at `(cr, ci)` up to [maxIter], or `-1.0` if interior.
	Function of Float is evaluatePoint(Float is cr, Float is ci, Int is maxIter){ -1.0 }

	## Computes smooth continuous escape value from escape iteration [iter] and squared magnitude [mag2].
	Function of Float is smoothEscapeValue(Int is iter, Float is mag2){
		local Float is mag: sqrt(value: mag2);
		local Float is logMag: log(value: mag);
		local Float is nu: if({ logMag > 0.0 }, { log2(value: logMag) }, { 0.0 });
		return (toFloat(value: iter) + 1.0) - nu;
	}

	replace Function of Array of Float is sampleGrid(FractalViewport is viewport, Int is w, Int is h){
		local Array of Float is grid: Array();
		if({ w <= 0 || h <= 0 }, { return grid; });

		local Float is spanY: viewport:spanY();
		local Float is spanX: spanY * (toFloat(value: w) / toFloat(value: h));
		local Float is xMin: viewport:centerX - spanX * 0.5;
		local Float is yMin: viewport:centerY - spanY * 0.5;
		local Float is zoomBoost: if({ viewport:zoom > 1.0 }, { log2(value: viewport:zoom) * 16.0 }, { 0.0 });
		local Int is maxIter: 80 + toInt(value: zoomBoost);
		if({ maxIter > 220 }, { maxIter: 220; });

		local Int is py: 0;
		while({ py < h }, {
			local Float is ci: yMin + ((toFloat(value: py) + 0.5) / toFloat(value: h)) * spanY;
			local Int is px: 0;
			while({ px < w }, {
				local Float is cr: xMin + ((toFloat(value: px) + 0.5) / toFloat(value: w)) * spanX;
				local Float is mu: evaluatePoint(cr: cr, ci: ci, maxIter: maxIter);
				if({ mu < 0.0 }, {
					grid:add(item: -1.0);
				}, {
					grid:add(item: 0.5 - 0.5 * cos(value: mu * 0.25));
				});
				px: px + 1;
			});
			py: py + 1;
		});
		return grid;
	}
}
