#! Package theofractal:model:fractals
#! Barnsley Fern IFS fractal using viewport-culled sub-fern collection and invariant-measure chaos sampling.

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

	# Collects visible sub-fern affine transforms `(a, b, e, c, d, f, weight)` (7 floats per entry).
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
		if({ fullyInside || (pxW <= 8.0 && pxH <= 8.0) || depth >= 32 }, {
			branches:push(item: a);
			branches:push(item: b);
			branches:push(item: e);
			branches:push(item: c);
			branches:push(item: d);
			branches:push(item: f);
			branches:push(item: weight);
			return;
		});

		# Draw this branch's stem segment (0, 0) -> (0, 1.6) directly so stems stay solid at high zoom
		incrementLine(
			counts: counts,
			w: w,
			h: h,
			x0: toInt(value: (e - xMin) * scaleX),
			y0: toInt(value: (yMax - f) * scaleY),
			x1: toInt(value: ((b * 1.6 + e) - xMin) * scaleX),
			y1: toInt(value: (yMax - (d * 1.6 + f)) * scaleY)
		);

		local Int is nd: depth + 1;

		# Compose M * T2: (0.85x + 0.04y, -0.04x + 0.85y + 1.6)
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

		# Compose M * T3: (0.20x - 0.26y, 0.23x + 0.22y + 1.6)
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

		# Compose M * T4: (-0.15x + 0.28y, 0.26x + 0.24y + 0.44)
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

	local Function is sampleChaos(
		[Float] is branches,
		[Int] is counts,
		Int is w,
		Int is h,
		Float is xMin,
		Float is xMax,
		Float is yMin,
		Float is yMax,
		Float is scaleX,
		Float is scaleY
	){
		local Int is branchCount: branches:length() / 7;
		if({ branchCount <= 0 }, { return; });

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
		local Float is zoomFactor: if({ scaleX > 10.0 }, { log(value: scaleX) }, { 1.0 });
		local Int is samples: 35000 + toInt(value: zoomFactor * 4000.0);
		if({ samples > 90000 }, { samples: 90000; });
		local Int is i: 0;
		while({ i < samples }, {
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
					incrementPoint(counts: counts, w: w, h: h, x: toInt(value: (wx - xMin) * scaleX), y: toInt(value: (yMax - wy) * scaleY));
				});
			});
			i: i + 1;
		});
	}

	replace Function of [Float] is sampleGrid(FractalViewport is viewport, Int is w, Int is h){
		local [Float] is grid: newGrid(w: w, h: h);
		local Int is totalPixels: w * h;
		if({ totalPixels <= 0 }, { return grid; });

		local [Int] is counts: newCountGrid(w: w, h: h);
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
		sampleChaos(
			branches: branches, counts: counts, w: w, h: h,
			xMin: xMin, xMax: xMax, yMin: yMin, yMax: yMax, scaleX: scaleX, scaleY: scaleY
		);
		applyLogDensity(counts: counts, grid: grid, floorVal: 0.2);
		return grid;
	}
}
