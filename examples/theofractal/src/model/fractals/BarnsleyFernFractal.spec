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

	local Function is plotHit([Int] is counts, Int is w, Int is h, Int is sx, Int is sy){
		if({ sx < 0 || sx >= w || sy < 0 || sy >= h }, { return; });
		local Int is idx: sy * w + sx;
		counts:set(index: idx, item: counts:get(index: idx) + 1);
	}

	local Function is drawStemLine(
		[Int] is counts,
		Int is w,
		Int is h,
		Float is xMin,
		Float is yMax,
		Float is scaleX,
		Float is scaleY,
		Float is wx0,
		Float is wy0,
		Float is wx1,
		Float is wy1
	){
		local Int is x0: toInt(value: (wx0 - xMin) * scaleX);
		local Int is y0: toInt(value: (yMax - wy0) * scaleY);
		local Int is x1: toInt(value: (wx1 - xMin) * scaleX);
		local Int is y1: toInt(value: (yMax - wy1) * scaleY);
		if({ (x0 < 0 && x1 < 0) || (x0 >= w && x1 >= w) || (y0 < 0 && y1 < 0) || (y0 >= h && y1 >= h) }, {
			return;
		});
		local Int is dx: x1 - x0;
		local Int is dy: y1 - y0;
		local Int is adx: if({ dx < 0 }, { -dx }, { dx });
		local Int is ady: if({ dy < 0 }, { -dy }, { dy });
		local Int is steps: if({ adx > ady }, { adx }, { ady });
		if({ steps <= 0 }, {
			plotHit(counts: counts, w: w, h: h, sx: x0, sy: y0);
			return;
		});
		local Float is fx: toFloat(value: x0);
		local Float is fy: toFloat(value: y0);
		local Float is sx: toFloat(value: dx) / toFloat(value: steps);
		local Float is sy: toFloat(value: dy) / toFloat(value: steps);
		local Int is i: 0;
		while({ i <= steps }, {
			plotHit(counts: counts, w: w, h: h, sx: toInt(value: round(value: fx)), sy: toInt(value: round(value: fy)));
			fx: fx + sx;
			fy: fy + sy;
			i: i + 1;
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
		if({ (pxW <= 0.9 && pxH <= 0.9) || depth >= 64 }, {
			local Int is sx: toInt(value: (cx - xMin) * scaleX);
			local Int is sy: toInt(value: (yMax - cy) * scaleY);
			plotHit(counts: counts, w: w, h: h, sx: sx, sy: sy);
			return;
		});

		# Transformed stem T1(root) = segment from (0, 0) to (0, 1.6) in the current parallelogram frame
		local Float is baseX: cx - 0.1020408 * ux;
		local Float is baseY: cy - 0.1020408 * uy;
		drawStemLine(
			counts: counts,
			w: w,
			h: h,
			xMin: xMin,
			yMax: yMax,
			scaleX: scaleX,
			scaleY: scaleY,
			wx0: baseX - vx,
			wy0: baseY - vy,
			wx1: baseX - 0.68 * vx,
			wy1: baseY - 0.68 * vy
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
				local Float is boosted: sqrt(value: clamp01(v: density));
				grid:set(index: pi, item: clamp01(v: 0.30 + 0.70 * boosted));
			});
			pi: pi + 1;
		});
		return grid;
	}
}
