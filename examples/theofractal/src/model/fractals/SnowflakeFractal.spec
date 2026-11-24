#! Package theofractal:model:fractals
#! Koch Snowflake fractal implementation with viewport-culled recursive edge subdivision.

Class of Fractal is SnowflakeFractal{
	replace [String] is namespace: ['theofractal', 'model', 'fractals'];

	replace [[String]] is using: [
		['theofractal', 'model', [Fractal, FractalViewport]],
		['theofractal', 'util', [FractalStrings, as GridRasterizer()]],
		['base', 'math', as Math()],
		['base', 'sys', as Conditional()]
	];

	replace Function of String is name(){ FractalStrings:OPT_SNOWFLAKE }

	replace Function of Boolean is isYUp(){ true }

	replace Function of FractalViewport is defaultViewport(){
		FractalViewport(centerX: 0.0, centerY: 0.0, baseSpan: 2.4, zoom: 1.0)
	}

	local Function is drawEdge(
		Array of Float is grid,
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
		Int is depth,
		Float is colorT
	){
		local Float is sx1: worldToScreenX(wx: x1, xMin: xMin, invSpanX: invSpanX, w: w);
		local Float is sy1: worldToScreenYUp(wy: y1, yMax: yMax, invSpanY: invSpanY, h: h);
		local Float is sx2: worldToScreenX(wx: x2, xMin: xMin, invSpanX: invSpanX, w: w);
		local Float is sy2: worldToScreenYUp(wy: y2, yMax: yMax, invSpanY: invSpanY, h: h);

		local Float is dx: sx2 - sx1;
		local Float is dy: sy2 - sy1;
		local Float is len: sqrt(value: dx * dx + dy * dy);
		local Float is pad: len * 0.4 + 2.0;
		local Float is minX: if({ sx1 < sx2 }, { sx1 }, { sx2 }) - pad;
		local Float is maxX: if({ sx1 > sx2 }, { sx1 }, { sx2 }) + pad;
		local Float is minY: if({ sy1 < sy2 }, { sy1 }, { sy2 }) - pad;
		local Float is maxY: if({ sy1 > sy2 }, { sy1 }, { sy2 }) + pad;

		if({ maxX < 0.0 || minX >= toFloat(value: w) || maxY < 0.0 || minY >= toFloat(value: h) }, {
			return;
		});

		if({ len < 2.2 || depth >= 7 }, {
			drawLine(
				grid: grid,
				w: w,
				h: h,
				x0: toInt(value: round(value: sx1)),
				y0: toInt(value: round(value: sy1)),
				x1: toInt(value: round(value: sx2)),
				y1: toInt(value: round(value: sy2)),
				val: clamp01(v: colorT)
			);
			return;
		});

		local Float is vx: (x2 - x1) / 3.0;
		local Float is vy: (y2 - y1) / 3.0;
		local Float is ax: x1 + vx;
		local Float is ay: y1 + vy;
		local Float is bx: x1 + vx * 2.0;
		local Float is by: y1 + vy * 2.0;
		local Float is cos60: 0.5;
		local Float is sin60: 0.8660254;
		local Float is px: ax + (vx * cos60 - vy * sin60);
		local Float is py: ay + (vx * sin60 + vy * cos60);

		local Int is nd: depth + 1;
		drawEdge(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: x1, y1: y1, x2: ax, y2: ay, depth: nd, colorT: colorT);
		drawEdge(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: ax, y1: ay, x2: px, y2: py, depth: nd, colorT: colorT + 0.08);
		drawEdge(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: px, y1: py, x2: bx, y2: by, depth: nd, colorT: colorT + 0.08);
		drawEdge(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: bx, y1: by, x2: x2, y2: y2, depth: nd, colorT: colorT);
	}

	replace Function of Array of Float is sampleGrid(FractalViewport is viewport, Int is w, Int is h){
		local Array of Float is grid: newGrid(w: w, h: h);
		local Float is spanY: viewport:spanY();
		local Float is spanX: spanY * (toFloat(value: w) / toFloat(value: h));
		local Float is xMin: viewport:centerX - spanX * 0.5;
		local Float is yMax: viewport:centerY + spanY * 0.5;
		local Float is invSpanX: 1.0 / spanX;
		local Float is invSpanY: 1.0 / spanY;
		local Float is ax: 0.0;
		local Float is ay: 1.0;
		local Float is bx: 0.8660254;
		local Float is by: -0.5;
		local Float is cx: -0.8660254;
		local Float is cy: -0.5;
		drawEdge(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: ax, y1: ay, x2: bx, y2: by, depth: 0, colorT: 0.35);
		drawEdge(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: bx, y1: by, x2: cx, y2: cy, depth: 0, colorT: 0.55);
		drawEdge(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: cx, y1: cy, x2: ax, y2: ay, depth: 0, colorT: 0.75);
		return grid;
	}
}
