#! Package theofractal:model:fractals
#! Barnsley Fern IFS attractor with adaptive zoom sampling and logarithmic density shading.

Class of Fractal is BarnsleyFernFractal{
	replace [String] is namespace: ['theofractal', 'model', 'fractals'];

	replace [[String]] is using: [
		['theofractal', 'model', [Fractal, FractalViewport]],
		['theofractal', 'util', [FractalStrings, as GridRasterizer()]],
		['base', 'math', as Math()],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	replace Function of String is name(){ FractalStrings:OPT_BARNSLEY_FERN }

	replace Function of Boolean is isYUp(){ true }

	replace Function of FractalViewport is defaultViewport(){
		FractalViewport(centerX: 0.0, centerY: 5.0, baseSpan: 10.8, zoom: 1.0)
	}

	replace Function of Array of Float is sampleGrid(FractalViewport is viewport, Int is w, Int is h){
		local Array of Float is grid: newGrid(w: w, h: h);
		local Int is totalPixels: w * h;
		local Array of Int is counts: Array();
		local Int is ci: 0;
		while({ ci < totalPixels }, {
			counts:add(item: 0);
			ci: ci + 1;
		});

		local Float is spanY: viewport:spanY();
		local Float is spanX: spanY * (toFloat(value: w) / toFloat(value: h));
		local Float is xMin: viewport:centerX - spanX * 0.5;
		local Float is yMax: viewport:centerY + spanY * 0.5;
		local Float is invSpanX: 1.0 / spanX;
		local Float is invSpanY: 1.0 / spanY;

		local Float is x: 0.0;
		local Float is y: 0.0;
		local Int is seed: 1337;
		local Int is i: 0;
		local Int is minTotal: 65000;
		local Int is maxTotal: 1500000;
		local Int is targetInView: totalPixels * 8;
		local Int is inViewHits: 0;
		local Int is maxCount: 1;
		while({ i < maxTotal && (i < minTotal || inViewHits < targetInView) }, {
			seed: (seed * 1103515245 + 12345) % 2147483647;
			if({ seed < 0 }, { seed: -seed; });
			local Int is r: seed % 100;
			local Float is nx: 0.0;
			local Float is ny: 0.0;
			if({ r < 1 }, {
				nx: 0.0;
				ny: 0.16 * y;
			}, {
				if({ r < 86 }, {
					nx: 0.85 * x + 0.04 * y;
					ny: -0.04 * x + 0.85 * y + 1.6;
				}, {
					if({ r < 93 }, {
						nx: 0.2 * x - 0.26 * y;
						ny: 0.23 * x + 0.22 * y + 1.6;
					}, {
						nx: -0.15 * x + 0.28 * y;
						ny: 0.26 * x + 0.24 * y + 0.44;
					});
				});
			});
			x: nx;
			y: ny;
			if({ i >= 20 }, {
				local Int is sx: toInt(value: round(value: worldToScreenX(wx: x, xMin: xMin, invSpanX: invSpanX, w: w)));
				local Int is sy: toInt(value: round(value: worldToScreenYUp(wy: y, yMax: yMax, invSpanY: invSpanY, h: h)));
				if({ sx >= 0 && sx < w && sy >= 0 && sy < h }, {
					local Int is idx: sy * w + sx;
					local Int is nextCount: counts:get(index: idx) + 1;
					counts:set(index: idx, item: nextCount);
					if({ nextCount > maxCount }, { maxCount: nextCount; });
					inViewHits: inViewHits + 1;
				});
			});
			i: i + 1;
		});

		local Float is denom: log(value: 1.0 + toFloat(value: maxCount));
		if({ denom <= 0.0 }, { denom: 1.0; });
		local Int is pi: 0;
		while({ pi < totalPixels }, {
			local Int is c: counts:get(index: pi);
			if({ c > 0 }, {
				local Float is density: log(value: 1.0 + toFloat(value: c)) / denom;
				grid:set(index: pi, item: clamp01(v: 0.15 + 0.85 * density));
			});
			pi: pi + 1;
		});
		return grid;
	}
}
