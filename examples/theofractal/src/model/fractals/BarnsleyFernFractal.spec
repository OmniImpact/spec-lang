#! Package theofractal:model:fractals
#! Barnsley Fern IFS fractal using viewport-culled sub-fern collection + invariant-measure chaos sampling.

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
			if({ x0 >= 0 && x0 < w && y0 >= 0 && y0 < h }, {
				local Int is idx0: y0 * w + x0;
				counts:set(index: idx0, item: counts:get(index: idx0) + 1);
			});
			return;
		});
		local Float is fx: toFloat(value: x0);
		local Float is fy: toFloat(value: y0);
		local Float is sx: toFloat(value: dx) / toFloat(value: steps);
		local Float is sy: toFloat(value: dy) / toFloat(value: steps);
		local Int is i: 0;
		while({ i <= steps }, {
			local Int is px: toInt(value: round(value: fx));
			local Int is py: toInt(value: round(value: fy));
			if({ px >= 0 && px < w && py >= 0 && py < h }, {
				local Int is idx: py * w + px;
				counts:set(index: idx, item: counts:get(index: idx) + 1);
			});
			fx: fx + sx;
			fy: fy + sy;
			i: i + 1;
		});
	}

	# Collects visible sub-fern affine transforms `(a, b, e, c, d, f, weight)` stored flat (7 floats per entry).
	local Function is collectVisibleBranches(
		[Float] is branches,
		[Int] is counts,
		Int is w,
		Int is h,
		Float is xMin,
		Float is xMax,
		Float is yMin,
		Float is yMax,
		Float is scaleX,
		Float is scaleY,
		Float is a,
		Float is b,
		Float is e,
		Float is c,
		Float is d,
		Float is f,
		Float is weight,
		Int is depth
	){
		# Transform root parallelogram (cx: 0.25, cy: 5.0, u: (2.45, 0), v: (0, 5.0))
		local Float is cx: a * 0.25 + b * 5.0 + e;
		local Float is cy: c * 0.25 + d * 5.0 + f;
		local Float is ux: a * 2.45;
		local Float is uy: c * 2.45;
		local Float is vx: b * 5.0;
		local Float is vy: d * 5.0;
		local Float is aux: if({ ux < 0.0 }, { -ux }, { ux });
		local Float is avx: if({ vx < 0.0 }, { -vx }, { vx });
		local Float is auy: if({ uy < 0.0 }, { -uy }, { uy });
		local Float is avy: if({ vy < 0.0 }, { -vy }, { vy });
		local Float is halfW: aux + avx;
		local Float is halfH: auy + avy;

		if({ cx + halfW < xMin || cx - halfW > xMax || cy + halfH < yMin || cy - halfH > yMax }, {
			return;
		});

		local Boolean is fullyInside: cx - halfW >= xMin && cx + halfW <= xMax && cy - halfH >= yMin && cy + halfH <= yMax;
		local Float is pxW: halfW * 2.0 * scaleX;
		local Float is pxH: halfH * 2.0 * scaleY;
		if({ fullyInside || (pxW <= 8.0 && pxH <= 8.0) || depth >= 10 }, {
			branches:push(item: a);
			branches:push(item: b);
			branches:push(item: e);
			branches:push(item: c);
			branches:push(item: d);
			branches:push(item: f);
			branches:push(item: weight);
			return;
		});

		# Draw this branch's stem segment (0, 0) -> (0, 1.6) directly so stems never vanish when zoomed
		drawStemLine(
			counts: counts, w: w, h: h, xMin: xMin, yMax: yMax, scaleX: scaleX, scaleY: scaleY,
			wx0: e, wy0: f, wx1: b * 1.6 + e, wy1: d * 1.6 + f
		);

		local Int is nd: depth + 1;

		# Compose M * T2: T2 = (0.85, 0.04, 0.0, -0.04, 0.85, 1.6)
		collectVisibleBranches(
			branches: branches, counts: counts, w: w, h: h,
			xMin: xMin, xMax: xMax, yMin: yMin, yMax: yMax, scaleX: scaleX, scaleY: scaleY,
			a: a * 0.85 + b * (-0.04),
			b: a * 0.04 + b * 0.85,
			e: b * 1.6 + e,
			c: c * 0.85 + d * (-0.04),
			d: c * 0.04 + d * 0.85,
			f: d * 1.6 + f,
			weight: weight * 0.85,
			depth: nd
		);

		# Compose M * T3: T3 = (0.20, -0.26, 0.0, 0.23, 0.22, 1.6)
		collectVisibleBranches(
			branches: branches, counts: counts, w: w, h: h,
			xMin: xMin, xMax: xMax, yMin: yMin, yMax: yMax, scaleX: scaleX, scaleY: scaleY,
			a: a * 0.20 + b * 0.23,
			b: a * (-0.26) + b * 0.22,
			e: b * 1.6 + e,
			c: c * 0.20 + d * 0.23,
			d: c * (-0.26) + d * 0.22,
			f: d * 1.6 + f,
			weight: weight * 0.07,
			depth: nd
		);

		# Compose M * T4: T4 = (-0.15, 0.28, 0.0, 0.26, 0.24, 0.44)
		collectVisibleBranches(
			branches: branches, counts: counts, w: w, h: h,
			xMin: xMin, xMax: xMax, yMin: yMin, yMax: yMax, scaleX: scaleX, scaleY: scaleY,
			a: a * (-0.15) + b * 0.26,
			b: a * 0.28 + b * 0.24,
			e: b * 0.44 + e,
			c: c * (-0.15) + d * 0.26,
			d: c * 0.28 + d * 0.24,
			f: d * 0.44 + f,
			weight: weight * 0.07,
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

		local [Float] is branches: [];
		collectVisibleBranches(
			branches: branches, counts: counts, w: w, h: h,
			xMin: xMin, xMax: xMax, yMin: yMin, yMax: yMax, scaleX: scaleX, scaleY: scaleY,
			a: 1.0, b: 0.0, e: 0.0, c: 0.0, d: 1.0, f: 0.0, weight: 1.0, depth: 0
		);

		local Int is branchCount: branches:length() / 7;
		if({ branchCount > 0 }, {
			local [Float] is cumWeights: [];
			local Float is totalW: 0.0;
			local Int is bi: 0;
			while({ bi < branchCount }, {
				totalW: totalW + branches:get(index: bi * 7 + 6);
				cumWeights:push(item: totalW);
				bi: bi + 1;
			});

			local Float is x: 0.0;
			local Float is y: 0.0;
			local Int is seed: 1337;
			local Int is seed2: 7919;
			local Int is totalSamples: 35000;
			local Int is i: 0;
			while({ i < totalSamples }, {
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
					local Int is pickIdx: 0;
					if({ branchCount > 1 }, {
						seed2: (seed2 * 1103515245 + 12345) % 2147483647;
						if({ seed2 < 0 }, { seed2: -seed2; });
						local Float is target: (toFloat(value: seed2 % 100000) / 100000.0) * totalW;
						while({ pickIdx < branchCount - 1 && cumWeights:get(index: pickIdx) < target }, {
							pickIdx: pickIdx + 1;
						});
					});
					local Int is off: pickIdx * 7;
					local Float is wx: branches:get(index: off) * x + branches:get(index: off + 1) * y + branches:get(index: off + 2);
					local Float is wy: branches:get(index: off + 3) * x + branches:get(index: off + 4) * y + branches:get(index: off + 5);
					if({ wx >= xMin && wx < xMax && wy > yMin && wy <= yMax }, {
						local Int is sx: toInt(value: (wx - xMin) * scaleX);
						local Int is sy: toInt(value: (yMax - wy) * scaleY);
						if({ sx >= 0 && sx < w && sy >= 0 && sy < h }, {
							local Int is idx: sy * w + sx;
							counts:set(index: idx, item: counts:get(index: idx) + 1);
						});
					});
				});
				i: i + 1;
			});
		});

		local Int is maxCount: 1;
		local Int is mi: 0;
		while({ mi < totalPixels }, {
			local Int is cntMax: counts:get(index: mi);
			if({ cntMax > maxCount }, { maxCount: cntMax; });
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
