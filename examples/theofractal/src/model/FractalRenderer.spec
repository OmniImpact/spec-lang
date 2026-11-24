#! Package theofractal:model
#! Pure math and 2D pixel-buffer renderer for all TheoFractal fractals and color themes.

Class is FractalRenderer{
	replace [String] is namespace: ['theofractal', 'model'];

	replace [[String]] is using: [
		['theofractal', 'model', [FractalType, ColorTheme, FractalViewport]],
		['base', 'theo', TheoColor],
		['base', 'math', as Math()],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	local Function of Float is clamp01(Float is v){
		if({ v < 0.0 }, { return 0.0; });
		if({ v > 1.0 }, { return 1.0; });
		return v;
	}

	local Function of Int is toByte(Float is v){
		local Int is b: toInt(value: round(value: clamp01(v: v) * 255.0));
		if({ b < 0 }, { return 0; });
		if({ b > 255 }, { return 255; });
		return b;
	}

	## Maps a normalized value [t] in `[0.0, 1.0]` (or `< 0.0` for background) to a [TheoColor] under [theme].
	Function of TheoColor is colorForValue(Float is t, ColorTheme is theme){
		if({ t < 0.0 }, {
			return TheoColor:rgb(r: 10, g: 12, b: 18);
		});
		local Float is u: clamp01(v: t);
		return match(when: [
			{ theme == ColorTheme:GRAYSCALE }: {
				local Int is v: toByte(v: 0.12 + 0.88 * u);
				TheoColor:rgb(r: v, g: v, b: v);
			},
			{ theme == ColorTheme:COOL }: {
				local Int is r: toByte(v: 0.05 + 0.65 * (u * u));
				local Int is g: toByte(v: 0.18 + 0.78 * u);
				local Int is b: toByte(v: 0.45 + 0.55 * sqrt(value: u));
				TheoColor:rgb(r: r, g: g, b: b);
			},
			{ theme == ColorTheme:WARM }: {
				local Int is r: toByte(v: 0.35 + 0.65 * sqrt(value: u));
				local Int is g: toByte(v: 0.06 + 0.82 * (u * u));
				local Int is b: toByte(v: 0.04 + 0.46 * (u * u * u));
				TheoColor:rgb(r: r, g: g, b: b);
			},
			else: {
				local Float is angle: u * 6.2831853;
				local Int is r: toByte(v: 0.5 + 0.5 * cos(value: angle));
				local Int is g: toByte(v: 0.5 + 0.5 * cos(value: angle + 2.0943951));
				local Int is b: toByte(v: 0.5 + 0.5 * cos(value: angle + 4.1887902));
				TheoColor:rgb(r: r, g: g, b: b);
			}
		]);
	}

	local Function of Float is mandelbrotEscape(Float is cr, Float is ci, Int is maxIter){
		local Float is q: ((cr - 0.25) * (cr - 0.25)) + (ci * ci);
		if({ (q * (q + (cr - 0.25))) <= (0.25 * ci * ci) }, { return -1.0; });
		if({ ((cr + 1.0) * (cr + 1.0)) + (ci * ci) <= 0.0625 }, { return -1.0; });
		local Float is zr: 0.0;
		local Float is zi: 0.0;
		local Float is zr2: 0.0;
		local Float is zi2: 0.0;
		local Int is iter: 0;
		while({ (iter < maxIter) && ((zr2 + zi2) <= 16.0) }, {
			zi: (2.0 * zr * zi) + ci;
			zr: (zr2 - zi2) + cr;
			zr2: zr * zr;
			zi2: zi * zi;
			iter: iter + 1;
		});
		if({ iter >= maxIter }, { return -1.0; });
		local Float is mag: sqrt(value: zr2 + zi2);
		local Float is logMag: log(value: mag);
		local Float is nu: if({ logMag > 0.0 }, { log2(value: logMag) }, { 0.0 });
		return (toFloat(value: iter) + 1.0) - nu;
	}

	local Function of Float is juliaEscape(Float is zr0, Float is zi0, Int is maxIter){
		local Float is cr: -0.7;
		local Float is ci: 0.27015;
		local Float is zr: zr0;
		local Float is zi: zi0;
		local Float is zr2: zr * zr;
		local Float is zi2: zi * zi;
		local Int is iter: 0;
		while({ (iter < maxIter) && ((zr2 + zi2) <= 16.0) }, {
			zi: (2.0 * zr * zi) + ci;
			zr: (zr2 - zi2) + cr;
			zr2: zr * zr;
			zi2: zi * zi;
			iter: iter + 1;
		});
		if({ iter >= maxIter }, { return -1.0; });
		local Float is mag: sqrt(value: zr2 + zi2);
		local Float is logMag: log(value: mag);
		local Float is nu: if({ logMag > 0.0 }, { log2(value: logMag) }, { 0.0 });
		return (toFloat(value: iter) + 1.0) - nu;
	}

	local Function of Float is burningShipEscape(Float is cr, Float is ci, Int is maxIter){
		local Float is zr: 0.0;
		local Float is zi: 0.0;
		local Float is zr2: 0.0;
		local Float is zi2: 0.0;
		local Int is iter: 0;
		while({ (iter < maxIter) && ((zr2 + zi2) <= 16.0) }, {
			local Float is azr: if({ zr < 0.0 }, { -zr }, { zr });
			local Float is azi: if({ zi < 0.0 }, { -zi }, { zi });
			zi: (2.0 * azr * azi) + ci;
			zr: (zr2 - zi2) + cr;
			zr2: zr * zr;
			zi2: zi * zi;
			iter: iter + 1;
		});
		if({ iter >= maxIter }, { return -1.0; });
		local Float is mag: sqrt(value: zr2 + zi2);
		local Float is logMag: log(value: mag);
		local Float is nu: if({ logMag > 0.0 }, { log2(value: logMag) }, { 0.0 });
		return (toFloat(value: iter) + 1.0) - nu;
	}

	local Function is plotPoint(Array of Float is grid, Int is w, Int is h, Int is x, Int is y, Float is val){
		if({ x < 0 || x >= w || y < 0 || y >= h }, { return; });
		local Int is idx: y * w + x;
		if({ val > grid:get(index: idx) }, {
			grid:set(index: idx, item: val);
		});
	}

	local Function is drawLine(Array of Float is grid, Int is w, Int is h, Int is x0, Int is y0, Int is x1, Int is y1, Float is val){
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

	local Function of Float is worldToScreenX(Float is wx, Float is xMin, Float is invSpanX, Int is w){
		return (wx - xMin) * invSpanX * toFloat(value: w);
	}

	local Function of Float is worldToScreenYUp(Float is wy, Float is yMax, Float is invSpanY, Int is h){
		return (yMax - wy) * invSpanY * toFloat(value: h);
	}

	local Function is subdivideSierpinski(
		Array of Float is grid,
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
			drawLine(grid: grid, w: w, h: h, x0: toInt(value: round(value: sax)), y0: toInt(value: round(value: say)), x1: toInt(value: round(value: sbx)), y1: toInt(value: round(value: sby)), val: t);
			drawLine(grid: grid, w: w, h: h, x0: toInt(value: round(value: sbx)), y0: toInt(value: round(value: sby)), x1: toInt(value: round(value: scx)), y1: toInt(value: round(value: scy)), val: t);
			drawLine(grid: grid, w: w, h: h, x0: toInt(value: round(value: scx)), y0: toInt(value: round(value: scy)), x1: toInt(value: round(value: sax)), y1: toInt(value: round(value: say)), val: t);
			return;
		});

		local Float is abx: (ax + bx) * 0.5;
		local Float is aby: (ay + by) * 0.5;
		local Float is bcx: (bx + cx) * 0.5;
		local Float is bcy: (by + cy) * 0.5;
		local Float is cax: (cx + ax) * 0.5;
		local Float is cay: (cy + ay) * 0.5;

		subdivideSierpinski(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, ax: ax, ay: ay, bx: abx, by: aby, cx: cax, cy: cay, depth: depth + 1);
		subdivideSierpinski(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, ax: abx, ay: aby, bx: bx, by: by, cx: bcx, cy: bcy, depth: depth + 1);
		subdivideSierpinski(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, ax: cax, ay: cay, bx: bcx, by: bcy, cx: cx, cy: cy, depth: depth + 1);
	}

	local Function is drawKoch(
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
			drawLine(grid: grid, w: w, h: h, x0: toInt(value: round(value: sx1)), y0: toInt(value: round(value: sy1)), x1: toInt(value: round(value: sx2)), y1: toInt(value: round(value: sy2)), val: clamp01(v: colorT));
			return;
		});

		local Float is vx: (x2 - x1) / 3.0;
		local Float is vy: (y2 - y1) / 3.0;
		local Float is ax: x1 + vx;
		local Float is ay: y1 + vy;
		local Float is bx: x1 + vx * 2.0;
		local Float is by: y1 + vy * 2.0;
		# Rotate (vx, vy) by +60 degrees to point outward for clockwise triangle
		local Float is cos60: 0.5;
		local Float is sin60: 0.8660254;
		local Float is px: ax + (vx * cos60 - vy * sin60);
		local Float is py: ay + (vx * sin60 + vy * cos60);

		local Int is nd: depth + 1;
		drawKoch(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: x1, y1: y1, x2: ax, y2: ay, depth: nd, colorT: colorT);
		drawKoch(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: ax, y1: ay, x2: px, y2: py, depth: nd, colorT: colorT + 0.08);
		drawKoch(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: px, y1: py, x2: bx, y2: by, depth: nd, colorT: colorT + 0.08);
		drawKoch(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: bx, y1: by, x2: x2, y2: y2, depth: nd, colorT: colorT);
	}

	local Function is drawDragon(
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
			drawLine(grid: grid, w: w, h: h, x0: toInt(value: round(value: sx1)), y0: toInt(value: round(value: sy1)), x1: toInt(value: round(value: sx2)), y1: toInt(value: round(value: sy2)), val: clamp01(v: (tStart + tEnd) * 0.5));
			return;
		});

		local Float is mx: (x1 + x2) * 0.5 + sign * (y2 - y1) * 0.5;
		local Float is my: (y1 + y2) * 0.5 - sign * (x2 - x1) * 0.5;
		local Float is tMid: (tStart + tEnd) * 0.5;
		local Int is nd: depth + 1;
		drawDragon(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: x1, y1: y1, x2: mx, y2: my, sign: 1.0, depth: nd, tStart: tStart, tEnd: tMid);
		drawDragon(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: mx, y1: my, x2: x2, y2: y2, sign: -1.0, depth: nd, tStart: tMid, tEnd: tEnd);
	}

	local Function is renderBarnsleyFern(
		Array of Float is grid,
		Int is w,
		Int is h,
		Float is xMin,
		Float is yMax,
		Float is invSpanX,
		Float is invSpanY
	){
		local Float is x: 0.0;
		local Float is y: 0.0;
		local Int is seed: 1337;
		local Int is i: 0;
		local Int is total: 45000;
		while({ i < total }, {
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
				local Int is sx: toInt(value: round(value: worldToScreenX(wx: x, xMin: xMin, invSpanX: invSpanX, w: w)));
				local Int is sy: toInt(value: round(value: worldToScreenYUp(wy: y, yMax: yMax, invSpanY: invSpanY, h: h)));
				local Float is val: clamp01(v: 0.25 + 0.75 * (y / 10.0));
				plotPoint(grid: grid, w: w, h: h, x: sx, y: sy, val: val);
			});
			i: i + 1;
		});
	}

	## Renders [kind] into a flat [TheoColor] pixel array of size `w * h` for [viewport] and [theme].
	Function of Array of TheoColor is renderPixels(FractalType is kind, ColorTheme is theme, FractalViewport is viewport, Int is w, Int is h){
		local Array of TheoColor is pixels: Array();
		if({ w <= 0 || h <= 0 || kind == FractalType:NONE }, {
			return pixels;
		});

		local Float is spanY: viewport:spanY();
		local Float is spanX: spanY * (toFloat(value: w) / toFloat(value: h));
		local Float is xMin: viewport:centerX - spanX * 0.5;
		local Float is yMin: viewport:centerY - spanY * 0.5;
		local Float is yMax: viewport:centerY + spanY * 0.5;
		local Float is invSpanX: 1.0 / spanX;
		local Float is invSpanY: 1.0 / spanY;

		local Boolean is isEscape: (kind == FractalType:MANDELBROT || kind == FractalType:JULIA || kind == FractalType:BURNING_SHIP);
		if({ isEscape }, {
			local Float is zoomBoost: if({ viewport:zoom > 1.0 }, { log2(value: viewport:zoom) * 16.0 }, { 0.0 });
			local Int is maxIter: 80 + toInt(value: zoomBoost);
			if({ maxIter > 220 }, { maxIter: 220; });
			local Int is py: 0;
			while({ py < h }, {
				local Float is ci: yMin + ((toFloat(value: py) + 0.5) / toFloat(value: h)) * spanY;
				local Int is px: 0;
				while({ px < w }, {
					local Float is cr: xMin + ((toFloat(value: px) + 0.5) / toFloat(value: w)) * spanX;
					local Float is mu: match(when: [
						{ kind == FractalType:MANDELBROT }: { mandelbrotEscape(cr: cr, ci: ci, maxIter: maxIter) },
						{ kind == FractalType:JULIA }: { juliaEscape(zr0: cr, zi0: ci, maxIter: maxIter) },
						else: { burningShipEscape(cr: cr, ci: ci, maxIter: maxIter) }
					]);
					if({ mu < 0.0 }, {
						pixels:add(item: colorForValue(t: -1.0, theme: theme));
					}, {
						local Float is t: 0.5 - 0.5 * cos(value: mu * 0.25);
						pixels:add(item: colorForValue(t: t, theme: theme));
					});
					px: px + 1;
				});
				py: py + 1;
			});
			return pixels;
		});

		local Int is total: w * h;
		local Array of Float is grid: Array();
		local Int is gi: 0;
		while({ gi < total }, {
			grid:add(item: -1.0);
			gi: gi + 1;
		});

		match(when: [
			{ kind == FractalType:SIERPINSKI }: {
				subdivideSierpinski(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, ax: -0.8660254, ay: -0.5, bx: 0.8660254, by: -0.5, cx: 0.0, cy: 1.0, depth: 0);
			},
			{ kind == FractalType:SNOWFLAKE }: {
				local Float is ax: 0.0;
				local Float is ay: 1.0;
				local Float is bx: 0.8660254;
				local Float is by: -0.5;
				local Float is cx: -0.8660254;
				local Float is cy: -0.5;
				drawKoch(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: ax, y1: ay, x2: bx, y2: by, depth: 0, colorT: 0.35);
				drawKoch(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: bx, y1: by, x2: cx, y2: cy, depth: 0, colorT: 0.55);
				drawKoch(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: cx, y1: cy, x2: ax, y2: ay, depth: 0, colorT: 0.75);
			},
			{ kind == FractalType:BARNSLEY_FERN }: {
				renderBarnsleyFern(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY);
			},
			{ kind == FractalType:DRAGON }: {
				drawDragon(grid: grid, w: w, h: h, xMin: xMin, yMax: yMax, invSpanX: invSpanX, invSpanY: invSpanY, x1: -0.5, y1: 0.0, x2: 0.5, y2: 0.0, sign: 1.0, depth: 0, tStart: 0.1, tEnd: 0.95);
			},
			else: { }
		]);

		local Int is pi: 0;
		while({ pi < total }, {
			pixels:add(item: colorForValue(t: grid:get(index: pi), theme: theme));
			pi: pi + 1;
		});
		return pixels;
	}
}
