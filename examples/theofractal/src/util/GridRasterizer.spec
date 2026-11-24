#! Package theofractal:util
#! Shared 2D float-grid and integer hit-density rasterization helpers.

Class is GridRasterizer{
	replace [String] is namespace: ['theofractal', 'util'];

	merge [[String]] is using: [
		['base', 'math', as Math()]
	];

	## Clamps [v] to `[0.0, 1.0]`.
	Function of Float is clamp01(Float is v){
		if({ v < 0.0 }, { return 0.0; });
		if({ v > 1.0 }, { return 1.0; });
		return v;
	}

	## Allocates a `w * h` float grid initialized to `-1.0` (background).
	Function of [Float] is newGrid(Int is w, Int is h){
		local Int is total: w * h;
		local [Float] is grid: [];
		local Int is i: 0;
		while({ i < total }, {
			grid:push(item: -1.0);
			i: i + 1;
		});
		return grid;
	}

	## Allocates a `w * h` integer hit-count grid initialized to `0`.
	Function of [Int] is newCountGrid(Int is w, Int is h){
		local Int is total: w * h;
		local [Int] is counts: [];
		local Int is i: 0;
		while({ i < total }, {
			counts:push(item: 0);
			i: i + 1;
		});
		return counts;
	}

	## Writes [val] at `(x, y)` in [grid] if inside bounds and brighter than the existing value.
	Function is plotPoint([Float] is grid, Int is w, Int is h, Int is x, Int is y, Float is val){
		if({ x < 0 || x >= w || y < 0 || y >= h }, { return; });
		local Int is idx: y * w + x;
		if({ val > grid:get(index: idx) }, {
			grid:set(index: idx, item: val);
		});
	}

	## Clips a floating-point segment `(x0, y0)-(x1, y1)` to `[0, w - 1] x [0, h - 1]` (Liang-Barsky), returning `[ok, cx0, cy0, cx1, cy1]`.
	local Function of [Float] is clipSegment(Float is x0, Float is y0, Float is x1, Float is y1, Int is w, Int is h){
		local Float is dx: x1 - x0;
		local Float is dy: y1 - y0;
		local Float is t0: 0.0;
		local Float is t1: 1.0;
		local Float is maxX: toFloat(value: w - 1);
		local Float is maxY: toFloat(value: h - 1);
		local [Float] is p: [-dx, dx, -dy, dy];
		local [Float] is q: [x0, maxX - x0, y0, maxY - y0];
		local Int is k: 0;
		while({ k < 4 }, {
			local Float is pk: p:get(index: k);
			local Float is qk: q:get(index: k);
			if({ pk == 0.0 }, {
				if({ qk < 0.0 }, { return [0.0]; });
			}, {
				local Float is r: qk / pk;
				if({ pk < 0.0 }, {
					if({ r > t1 }, { return [0.0]; });
					if({ r > t0 }, { t0: r; });
				}, {
					if({ r < t0 }, { return [0.0]; });
					if({ r < t1 }, { t1: r; });
				});
			});
			k: k + 1;
		});
		return [1.0, x0 + t0 * dx, y0 + t0 * dy, x0 + t1 * dx, y0 + t1 * dy];
	}

	## Rasterizes a line segment from `(x0, y0)` to `(x1, y1)` into [grid] with intensity [val].
	Function is drawLine([Float] is grid, Int is w, Int is h, Int is x0, Int is y0, Int is x1, Int is y1, Float is val){
		if({ w <= 0 || h <= 0 }, { return; });
		local [Float] is clipped: clipSegment(x0: toFloat(value: x0), y0: toFloat(value: y0), x1: toFloat(value: x1), y1: toFloat(value: y1), w: w, h: h);
		if({ clipped:get(index: 0) < 0.5 }, { return; });
		local Int is cx0: toInt(value: round(value: clipped:get(index: 1)));
		local Int is cy0: toInt(value: round(value: clipped:get(index: 2)));
		local Int is cx1: toInt(value: round(value: clipped:get(index: 3)));
		local Int is cy1: toInt(value: round(value: clipped:get(index: 4)));
		local Int is dx: cx1 - cx0;
		local Int is dy: cy1 - cy0;
		local Int is adx: if({ dx < 0 }, { -dx }, { dx });
		local Int is ady: if({ dy < 0 }, { -dy }, { dy });
		local Int is steps: if({ adx > ady }, { adx }, { ady });
		if({ steps <= 0 }, {
			plotPoint(grid: grid, w: w, h: h, x: cx0, y: cy0, val: val);
			return;
		});
		local Float is fx: toFloat(value: cx0);
		local Float is fy: toFloat(value: cy0);
		local Float is sx: toFloat(value: dx) / toFloat(value: steps);
		local Float is sy: toFloat(value: dy) / toFloat(value: steps);
		local Int is i: 0;
		while({ i <= steps }, {
			plotPoint(grid: grid, w: w, h: h, x: toInt(value: round(value: fx)), y: toInt(value: round(value: fy)), val: val);
			fx: fx + sx;
			fy: fy + sy;
			i: i + 1;
		});
	}

	## Increments the hit counter at `(x, y)` in [counts] if inside bounds.
	Function is incrementPoint([Int] is counts, Int is w, Int is h, Int is x, Int is y){
		if({ x < 0 || x >= w || y < 0 || y >= h }, { return; });
		local Int is idx: y * w + x;
		counts:set(index: idx, item: counts:get(index: idx) + 1);
	}

	## Rasterizes a line segment from `(x0, y0)` to `(x1, y1)` by incrementing hit counters in [counts].
	Function is incrementLine([Int] is counts, Int is w, Int is h, Int is x0, Int is y0, Int is x1, Int is y1){
		if({ w <= 0 || h <= 0 }, { return; });
		local [Float] is clipped: clipSegment(x0: toFloat(value: x0), y0: toFloat(value: y0), x1: toFloat(value: x1), y1: toFloat(value: y1), w: w, h: h);
		if({ clipped:get(index: 0) < 0.5 }, { return; });
		local Int is cx0: toInt(value: round(value: clipped:get(index: 1)));
		local Int is cy0: toInt(value: round(value: clipped:get(index: 2)));
		local Int is cx1: toInt(value: round(value: clipped:get(index: 3)));
		local Int is cy1: toInt(value: round(value: clipped:get(index: 4)));
		local Int is dx: cx1 - cx0;
		local Int is dy: cy1 - cy0;
		local Int is adx: if({ dx < 0 }, { -dx }, { dx });
		local Int is ady: if({ dy < 0 }, { -dy }, { dy });
		local Int is steps: if({ adx > ady }, { adx }, { ady });
		if({ steps <= 0 }, {
			incrementPoint(counts: counts, w: w, h: h, x: cx0, y: cy0);
			return;
		});
		local Float is fx: toFloat(value: cx0);
		local Float is fy: toFloat(value: cy0);
		local Float is sx: toFloat(value: dx) / toFloat(value: steps);
		local Float is sy: toFloat(value: dy) / toFloat(value: steps);
		local Int is i: 0;
		while({ i <= steps }, {
			incrementPoint(counts: counts, w: w, h: h, x: toInt(value: round(value: fx)), y: toInt(value: round(value: fy)));
			fx: fx + sx;
			fy: fy + sy;
			i: i + 1;
		});
	}

	## Converts integer hit [counts] into log-density values in `[floorVal, 1.0]` inside [grid].
	Function is applyLogDensity([Int] is counts, [Float] is grid, Float is floorVal){
		local Int is n: counts:length();
		local Int is maxCount: 1;
		local Int is mi: 0;
		while({ mi < n }, {
			local Int is c: counts:get(index: mi);
			if({ c > maxCount }, { maxCount: c; });
			mi: mi + 1;
		});
		local Float is denom: log(value: 1.0 + toFloat(value: maxCount));
		if({ denom <= 0.0 }, { denom: 1.0; });
		local Float is span: 1.0 - floorVal;
		local Int is pi: 0;
		while({ pi < n }, {
			local Int is cnt: counts:get(index: pi);
			if({ cnt > 0 }, {
				local Float is density: log(value: 1.0 + toFloat(value: cnt)) / denom;
				grid:set(index: pi, item: clamp01(v: floorVal + span * density));
			});
			pi: pi + 1;
		});
	}

	## Projects world X coordinate [wx] to screen pixel X.
	Function of Float is worldToScreenX(Float is wx, Float is xMin, Float is invSpanX, Int is w){
		return (wx - xMin) * invSpanX * toFloat(value: w);
	}

	## Projects Y-up world coordinate [wy] to screen pixel Y.
	Function of Float is worldToScreenYUp(Float is wy, Float is yMax, Float is invSpanY, Int is h){
		return (yMax - wy) * invSpanY * toFloat(value: h);
	}
}
