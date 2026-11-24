#! Package theofractal:util
#! Shared 2D float-grid rasterization and world-to-screen projection helpers for geometric/IFS fractals.

Class is GridRasterizer{
	replace [String] is namespace: ['theofractal', 'util'];

	replace [[String]] is using: [
		['base', 'math', as Math()],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	Function of Float is clamp01(Float is v){
		if({ v < 0.0 }, { return 0.0; });
		if({ v > 1.0 }, { return 1.0; });
		return v;
	}

	Function of Array of Float is newGrid(Int is w, Int is h){
		local Int is total: w * h;
		local Array of Float is grid: Array();
		local Int is i: 0;
		while({ i < total }, {
			grid:add(item: -1.0);
			i: i + 1;
		});
		return grid;
	}

	Function is plotPoint(Array of Float is grid, Int is w, Int is h, Int is x, Int is y, Float is val){
		if({ x < 0 || x >= w || y < 0 || y >= h }, { return; });
		local Int is idx: y * w + x;
		if({ val > grid:get(index: idx) }, {
			grid:set(index: idx, item: val);
		});
	}

	Function is drawLine(Array of Float is grid, Int is w, Int is h, Int is x0, Int is y0, Int is x1, Int is y1, Float is val){
		local Int is dx: x1 - x0;
		local Int is dy: y1 - y0;
		local Int is adx: if({ dx < 0 }, { -dx }, { dx });
		local Int is ady: if({ dy < 0 }, { -dy }, { dy });
		local Int is steps: if({ adx > ady }, { adx }, { ady });
		if({ steps <= 0 }, {
			plotPoint(grid: grid, w: w, h: h, x: x0, y: y0, val: val);
			return;
		});
		local Float is fx: toFloat(value: x0);
		local Float is fy: toFloat(value: y0);
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

	Function of Float is worldToScreenX(Float is wx, Float is xMin, Float is invSpanX, Int is w){
		return (wx - xMin) * invSpanX * toFloat(value: w);
	}

	Function of Float is worldToScreenYUp(Float is wy, Float is yMax, Float is invSpanY, Int is h){
		return (yMax - wy) * invSpanY * toFloat(value: h);
	}
}
