#! Package theofractal:model:fractals
#! Koch Snowflake fractal implementation using exact KIFS signed-distance interior & edge shading.

Class of Fractal is SnowflakeFractal{
	replace [String] is namespace: ['theofractal', 'model', 'fractals'];

	merge [[String]] is using: [
		['theofractal', 'model', [Fractal, FractalViewport]],
		['theofractal', 'util', [FractalStrings, as GridRasterizer()]],
		['base', 'math', as Math()]
	];

	replace Function of String is name(){ FractalStrings:OPT_SNOWFLAKE }

	replace Function of Boolean is isYUp(){ true }

	replace Function of FractalViewport is defaultViewport(){
		FractalViewport(centerX: 0.0, centerY: 0.0, baseSpan: 2.4, zoom: 1.0)
	}

	local Function of Float is evaluateSnowflake(Float is wx, Float is wy){
		local Float is halfSqrt3: 0.86602540378;
		local Float is sqrt3: 1.73205080757;

		local Float is x: if({ wx < 0.0 }, { -wx }, { wx });
		local Float is y: wy;

		# Fold into the bottom-edge 60-degree sector (outward normal = -Y)
		local Float is fold: 0.5 * x + halfSqrt3 * y;
		if({ fold > 0.0 }, {
			x: x - fold;
			y: y - sqrt3 * fold;
			if({ x < 0.0 }, { x: -x; });
		});

		# Map bottom edge [-halfSqrt3, +halfSqrt3] at y = -0.5 to [-1, 1] at py = 0 (py > 0 is outside)
		local Float is px: x / halfSqrt3;
		local Float is py: (-0.5 - y) / halfSqrt3;

		local Float is scale: 1.0;
		local Int is k: 0;
		while({ k < 7 }, {
			if({ px < 0.0 }, { px: -px; });
			local Float is dx: px - 0.33333333333;
			local Float is dot: -halfSqrt3 * dx + 0.5 * py;
			if({ dot > 0.0 }, {
				px: px - 2.0 * dot * (-halfSqrt3);
				py: py - 2.0 * dot * 0.5;
			});
			px: 3.0 * (px - 0.66666666667);
			py: 3.0 * py;
			scale: scale * 3.0;
			k: k + 1;
		});

		local Float is cx: px;
		if({ cx < -1.0 }, { cx: -1.0; });
		if({ cx > 1.0 }, { cx: 1.0; });
		local Float is ex: px - cx;
		local Float is dist: sqrt(value: ex * ex + py * py) / scale;

		if({ py > 0.0 }, {
			return -1.0;
		});

		# Interior shading: glowing crystalline rim along the Koch boundary, softening toward the core
		local Float is glow: exp(value: -dist * 3.4);
		return clamp01(v: 0.18 + 0.82 * glow);
	}

	replace Function of [Float] is sampleGrid(FractalViewport is viewport, Int is w, Int is h){
		local [Float] is grid: [];
		if({ w <= 0 || h <= 0 }, { return grid; });

		local Float is spanY: viewport:spanY();
		local Float is spanX: spanY * (toFloat(value: w) / toFloat(value: h));
		local Float is xMin: viewport:centerX - spanX * 0.5;
		local Float is yMax: viewport:centerY + spanY * 0.5;

		local Int is py: 0;
		while({ py < h }, {
			local Float is wy: yMax - ((toFloat(value: py) + 0.5) / toFloat(value: h)) * spanY;
			local Int is px: 0;
			while({ px < w }, {
				local Float is wx: xMin + ((toFloat(value: px) + 0.5) / toFloat(value: w)) * spanX;
				grid:push(item: evaluateSnowflake(wx: wx, wy: wy));
				px: px + 1;
			});
			py: py + 1;
		});
		return grid;
	}
}
