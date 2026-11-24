#! Package theofractal:model:fractals
#! Heighway Dragon Curve fractal implementation with viewport-culled recursive folding.

Class of Fractal is DragonFractal{
	replace [String] is namespace: ['theofractal', 'model', 'fractals'];

	merge [[String]] is using: [
		['theofractal', 'model', [Fractal, FractalViewport]],
		['theofractal', 'util', [FractalStrings, as GridRasterizer()]],
		['base', 'math', as Math()]
	];

	replace Function of String is name(){ FractalStrings:OPT_DRAGON }

	replace Function of Boolean is isYUp(){ true }

	replace Function of FractalViewport is defaultViewport(){
		FractalViewport(centerX: 0.25, centerY: 0.2, baseSpan: 2.0, zoom: 1.0)
	}

	local Function is drawSegment(
		[Float] is grid,
		Int is w,
		Int is h,
		Float is xMin,
		Float is yMax,
		Float is invSpanX,
		Float is invSpanY,
		Float is x1,
		Float is y1,
		Float is x2,
		Float is y2,
		Float is sign,
		Int is depth,
		Float is tStart,
		Float is tEnd
	){
		local Float is sx1: worldToScreenX(wx: x1, xMin: xMin, invSpanX: invSpanX, w: w);
		local Float is sy1: worldToScreenYUp(wy: y1, yMax: yMax, invSpanY: invSpanY, h: h);
		local Float is sx2: worldToScreenX(wx: x2, xMin: xMin, invSpanX: invSpanX, w: w);
		local Float is sy2: worldToScreenYUp(wy: y2, yMax: yMax, invSpanY: invSpanY, h: h);

		local Float is dx: sx2 - sx1;
		local Float is dy: sy2 - sy1;
		local Float is len: sqrt(value: dx * dx + dy * dy);
		local Float is pad: len * 0.6 + 2.0;
		local Float is minX: if({ sx1 < sx2 }, { sx1 }, { sx2 }) - pad;
		local Float is maxX: if({ sx1 > sx2 }, { sx1 }, { sx2 }) + pad;
		local Float is minY: if({ sy1 < sy2 }, { sy1 }, { sy2 }) - pad;
		local Float is maxY: if({ sy1 > sy2 }, { sy1 }, { sy2 }) + pad;

		if({ maxX < 0.0 || minX >= toFloat(value: w) || maxY < 0.0 || minY >= toFloat(value: h) }, {
			return;
		});

		if({ len < 2.2 || depth >= 14 }, {
			drawLine(
				grid: grid,
				w: w,
				h: h,
				x0: toInt(value: round(value: sx1)),
				y0: toInt(value: round(value: sy1)),
				x1: toInt(value: round(value: sx2)),
				y1: toInt(value: round(value: sy2)),
				val: clamp01(v: (tStart + tEnd) * 0.5)
			);
			return;
		});

		local Float is mx: (x1 + x2) * 0.5 + sign * (y2 - y1) * 0.5;
		local Float is my: (y1 + y2) * 0.5 - sign * (x2 - x1) * 0.5;
		local Float is tMid: (tStart + tEnd) * 0.5;
		local Int is nd: depth + 1;
		drawSegment(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: x1, y1: y1, x2: mx, y2: my, sign: 1.0, depth: nd, tStart: tStart, tEnd: tMid);
		drawSegment(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: mx, y1: my, x2: x2, y2: y2, sign: -1.0, depth: nd, tStart: tMid, tEnd: tEnd);
	}

	replace Function of [Float] is sampleGrid(FractalViewport is viewport, Int is w, Int is h){
		local [Float] is grid: newGrid(w: w, h: h);
		local Float is spanY: viewport:spanY();
		local Float is spanX: spanY * (toFloat(value: w) / toFloat(value: h));
		local Float is xMin: viewport:centerX - spanX * 0.5;
		local Float is yMax: viewport:centerY + spanY * 0.5;
		drawSegment(
			grid: grid,
			w: w,
			h: h,
			xMin: xMin,
			yMax: yMax,
			invSpanX: 1.0 / spanX,
			invSpanY: 1.0 / spanY,
			x1: -0.5,
			y1: 0.0,
			x2: 0.5,
			y2: 0.0,
			sign: 1.0,
			depth: 0,
			tStart: 0.1,
			tEnd: 0.95
		);
		return grid;
	}
}
