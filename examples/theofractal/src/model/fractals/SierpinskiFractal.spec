#! Package theofractal:model:fractals
#! Sierpinski Triangle fractal implementation with viewport-culled recursive subdivision.

Class of Fractal is SierpinskiFractal{
	replace [String] is namespace: ['theofractal', 'model', 'fractals'];

	merge [[String]] is using: [
		['theofractal', 'model', [Fractal, FractalViewport]],
		['theofractal', 'util', [FractalStrings, as GridRasterizer()]],
		['base', 'math', as Math()]
	];

	replace Function of String is name(){ FractalStrings:OPT_SIERPINSKI }

	replace Function of Boolean is isYUp(){ true }

	replace Function of FractalViewport is defaultViewport(){
		FractalViewport(centerX: 0.0, centerY: -0.05, baseSpan: 2.1, zoom: 1.0)
	}

	local Function is subdivide(
		[Float] is grid,
		Int is w,
		Int is h,
		Float is xMin,
		Float is yMax,
		Float is invSpanX,
		Float is invSpanY,
		Float is ax,
		Float is ay,
		Float is bx,
		Float is by,
		Float is cx,
		Float is cy,
		Int is depth
	){
		local Float is sax: worldToScreenX(wx: ax, xMin: xMin, invSpanX: invSpanX, w: w);
		local Float is say: worldToScreenYUp(wy: ay, yMax: yMax, invSpanY: invSpanY, h: h);
		local Float is sbx: worldToScreenX(wx: bx, xMin: xMin, invSpanX: invSpanX, w: w);
		local Float is sby: worldToScreenYUp(wy: by, yMax: yMax, invSpanY: invSpanY, h: h);
		local Float is scx: worldToScreenX(wx: cx, xMin: xMin, invSpanX: invSpanX, w: w);
		local Float is scy: worldToScreenYUp(wy: cy, yMax: yMax, invSpanY: invSpanY, h: h);

		local Float is minX: sax;
		if({ sbx < minX }, { minX: sbx; });
		if({ scx < minX }, { minX: scx; });
		local Float is maxX: sax;
		if({ sbx > maxX }, { maxX: sbx; });
		if({ scx > maxX }, { maxX: scx; });
		local Float is minY: say;
		if({ sby < minY }, { minY: sby; });
		if({ scy < minY }, { minY: scy; });
		local Float is maxY: say;
		if({ sby > maxY }, { maxY: sby; });
		if({ scy > maxY }, { maxY: scy; });

		if({ maxX < -1.0 || minX >= toFloat(value: w) + 1.0 || maxY < -1.0 || minY >= toFloat(value: h) + 1.0 }, {
			return;
		});

		local Float is bw: maxX - minX;
		local Float is bh: maxY - minY;
		if({ (bw <= 1.5 && bh <= 1.5) || depth >= 13 }, {
			local Float is t: clamp01(v: 0.25 + 0.75 * ((ay + 0.5) / 1.5));
			local Int is ix0: toInt(value: round(value: sax));
			local Int is iy0: toInt(value: round(value: say));
			local Int is ix1: toInt(value: round(value: sbx));
			local Int is iy1: toInt(value: round(value: sby));
			local Int is ix2: toInt(value: round(value: scx));
			local Int is iy2: toInt(value: round(value: scy));
			drawLine(grid: grid, w: w, h: h, x0: ix0, y0: iy0, x1: ix1, y1: iy1, val: t);
			drawLine(grid: grid, w: w, h: h, x0: ix1, y0: iy1, x1: ix2, y1: iy2, val: t);
			drawLine(grid: grid, w: w, h: h, x0: ix2, y0: iy2, x1: ix0, y1: iy0, val: t);
			return;
		});

		local Float is abx: (ax + bx) * 0.5;
		local Float is aby: (ay + by) * 0.5;
		local Float is bcx: (bx + cx) * 0.5;
		local Float is bcy: (by + cy) * 0.5;
		local Float is cax: (cx + ax) * 0.5;
		local Float is cay: (cy + ay) * 0.5;

		subdivide(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, ax: ax, ay: ay, bx: abx, by: aby, cx: cax, cy: cay, depth: depth + 1);
		subdivide(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, ax: abx, ay: aby, bx: bx, by: by, cx: bcx, cy: bcy, depth: depth + 1);
		subdivide(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, ax: cax, ay: cay, bx: bcx, by: bcy, cx: cx, cy: cy, depth: depth + 1);
	}

	replace Function of [Float] is sampleGrid(FractalViewport is viewport, Int is w, Int is h){
		local [Float] is grid: newGrid(w: w, h: h);
		local Float is spanY: viewport:spanY();
		local Float is spanX: spanY * (toFloat(value: w) / toFloat(value: h));
		local Float is xMin: viewport:centerX - spanX * 0.5;
		local Float is yMax: viewport:centerY + spanY * 0.5;
		subdivide(
			grid: grid,
			w: w,
			h: h,
			xMin: xMin,
			yMax: yMax,
			invSpanX: 1.0 / spanX,
			invSpanY: 1.0 / spanY,
			ax: -0.8660254,
			ay: -0.5,
			bx: 0.8660254,
			by: -0.5,
			cx: 0.0,
			cy: 1.0,
			depth: 0
		);
		return grid;
	}
}
