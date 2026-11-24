#! Package theofractal:model:fractals
#! Barnsley Fern IFS fractal using viewport-culled parallelogram subdivision for fast, dense rendering at any zoom.

Class of Fractal is BarnsleyFernFractal{
	replace [String] is namespace: ['theofractal', 'model', 'fractals'];

	merge [[String]] is using: [
		['theofractal', 'model', [Fractal, FractalViewport]],
		['theofractal', 'util', [FractalStrings, as GridRasterizer()]],
		['base', 'math', as Math()]
	];

	replace Function of String is name(){ FractalStrings:OPT_BARNSLEY_FERN }

	replace Function of Boolean is isYUp(){ true }

	replace Function of FractalViewport is defaultViewport(){
		FractalViewport(centerX: 0.0, centerY: 5.0, baseSpan: 10.8, zoom: 1.0)
	}

	local Function is plotHit([Int] is counts, Int is w, Int is h, Int is sx, Int is sy, Int is weight){
		if({ sx < 0 || sx >= w || sy < 0 || sy >= h }, { return; });
		local Int is idx: sy * w + sx;
		counts:set(index: idx, item: counts:get(index: idx) + weight);
	}

	local Function is drawStemSegment(
		[Int] is counts,
		Int is w,
		Int is h,
		Float is xMin,
		Float is yMax,
		Float is scaleX,
		Float is scaleY,
		Float is y0,
		Float is y1
	){
		local Int is sx: toInt(value: (0.0 - xMin) * scaleX);
		if({ sx < 0 || sx >= w }, { return; });
		local Int is sy0: toInt(value: (yMax - y0) * scaleY);
		local Int is sy1: toInt(value: (yMax - y1) * scaleY);
		local Int is lo: if({ sy0 < sy1 }, { sy0 }, { sy1 });
		local Int is hi: if({ sy0 > sy1 }, { sy0 }, { sy1 });
		if({ hi < 0 || lo >= h }, { return; });
		if({ lo < 0 }, { lo: 0; });
		if({ hi >= h }, { hi: h - 1; });
		local Int is y: lo;
		while({ y <= hi }, {
			local Int is idx: y * w + sx;
			counts:set(index: idx, item: counts:get(index: idx) + 1);
			y: y + 1;
		});
	}

	local Function is subdivideFern(
		[Int] is counts,
		Int is w,
		Int is h,
		Float is xMin,
		Float is xMax,
		Float is yMin,
		Float is yMax,
		Float is scaleX,
		Float is scaleY,
		Float is cx,
		Float is cy,
		Float is ux,
		Float is uy,
		Float is vx,
		Float is vy,
		Int is depth
	){
		local Float is aux: if({ ux < 0.0 }, { -ux }, { ux });
		local Float is avx: if({ vx < 0.0 }, { -vx }, { vx });
		local Float is auy: if({ uy < 0.0 }, { -uy }, { uy });
		local Float is avy: if({ vy < 0.0 }, { -vy }, { vy });
		local Float is halfW: aux + avx;
		local Float is halfH: auy + avy;

		if({ cx + halfW < xMin || cx - halfW > xMax || cy + halfH < yMin || cy - halfH > yMax }, {
			return;
		});

		local Float is pxW: halfW * 2.0 * scaleX;
		local Float is pxH: halfH * 2.0 * scaleY;
		if({ (pxW <= 1.2 && pxH <= 1.2) || depth >= 34 }, {
			local Int is sx: toInt(value: (cx - xMin) * scaleX);
			local Int is sy: toInt(value: (yMax - cy) * scaleY);
			plotHit(counts: counts, w: w, h: h, sx: sx, sy: sy, weight: 1);
			return;
		});

		# T1 (stem): x' = 0, y' = 0.16 * y
		drawStemSegment(
			counts: counts,
			w: w,
			h: h,
			xMin: xMin,
			yMax: yMax,
			scaleX: scaleX,
			scaleY: scaleY,
			y0: 0.16 * (cy - halfH),
			y1: 0.16 * (cy + halfH)
		);

		local Int is nd: depth + 1;

		# T2: (0.85x + 0.04y, -0.04x + 0.85y + 1.6)
		subdivideFern(
			counts: counts, w: w, h: h, xMin: xMin, xMax: xMax, yMin: yMin, yMax: yMax, scaleX: scaleX, scaleY: scaleY,
			cx: 0.85 * cx + 0.04 * cy,
			cy: -0.04 * cx + 0.85 * cy + 1.6,
			ux: 0.85 * ux + 0.04 * uy,
			uy: -0.04 * ux + 0.85 * uy,
			vx: 0.85 * vx + 0.04 * vy,
			vy: -0.04 * vx + 0.85 * vy,
			depth: nd
		);

		# T3: (0.20x - 0.26y, 0.23x + 0.22y + 1.6)
		subdivideFern(
			counts: counts, w: w, h: h, xMin: xMin, xMax: xMax, yMin: yMin, yMax: yMax, scaleX: scaleX, scaleY: scaleY,
			cx: 0.20 * cx - 0.26 * cy,
			cy: 0.23 * cx + 0.22 * cy + 1.6,
			ux: 0.20 * ux - 0.26 * uy,
			uy: 0.23 * ux + 0.22 * uy,
			vx: 0.20 * vx - 0.26 * vy,
			vy: 0.23 * vx + 0.22 * vy,
			depth: nd
		);

		# T4: (-0.15x + 0.28y, 0.26x + 0.24y + 0.44)
		subdivideFern(
			counts: counts, w: w, h: h, xMin: xMin, xMax: xMax, yMin: yMin, yMax: yMax, scaleX: scaleX, scaleY: scaleY,
			cx: -0.15 * cx + 0.28 * cy,
			cy: 0.26 * cx + 0.24 * cy + 0.44,
			ux: -0.15 * ux + 0.28 * uy,
			uy: 0.26 * ux + 0.24 * uy,
			vx: -0.15 * vx + 0.28 * vy,
			vy: 0.26 * vx + 0.24 * vy,
			depth: nd
		);
	}

	replace Function of [Float] is sampleGrid(FractalViewport is viewport, Int is w, Int is h){
		local [Float] is grid: newGrid(w: w, h: h);
		local Int is totalPixels: w * h;
		if({ totalPixels <= 0 }, { return grid; });

		local [Int] is counts: [];
		local Int is ci: 0;
		while({ ci < totalPixels }, {
			counts:push(item: 0);
			ci: ci + 1;
		});

		local Float is spanY: viewport:spanY();
		local Float is spanX: spanY * (toFloat(value: w) / toFloat(value: h));
		local Float is xMin: viewport:centerX - spanX * 0.5;
		local Float is xMax: viewport:centerX + spanX * 0.5;
		local Float is yMin: viewport:centerY - spanY * 0.5;
		local Float is yMax: viewport:centerY + spanY * 0.5;
		local Float is scaleX: toFloat(value: w) / spanX;
		local Float is scaleY: toFloat(value: h) / spanY;

		subdivideFern(
			counts: counts,
			w: w,
			h: h,
			xMin: xMin,
			xMax: xMax,
			yMin: yMin,
			yMax: yMax,
			scaleX: scaleX,
			scaleY: scaleY,
			cx: 0.25,
			cy: 5.0,
			ux: 2.45,
			uy: 0.0,
			vx: 0.0,
			vy: 5.0,
			depth: 0
		);

		local Int is maxCount: 1;
		local Int is mi: 0;
		while({ mi < totalPixels }, {
			local Int is c: counts:get(index: mi);
			if({ c > maxCount }, { maxCount: c; });
			mi: mi + 1;
		});

		local Float is denom: log(value: 1.0 + toFloat(value: maxCount));
		if({ denom <= 0.0 }, { denom: 1.0; });
		local Int is pi: 0;
		while({ pi < totalPixels }, {
			local Int is cnt: counts:get(index: pi);
			if({ cnt > 0 }, {
				local Float is density: log(value: 1.0 + toFloat(value: cnt)) / denom;
				grid:set(index: pi, item: clamp01(v: 0.2 + 0.8 * density));
			});
			pi: pi + 1;
		});
		return grid;
	}
}
