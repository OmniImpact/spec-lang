#! Smooth escape-time fractal math and palette mapping for Mandelbrot.

## Computes smooth Mandelbrot escape values and maps them to 256-color palette indices and shading glyphs.
Class is FractalMath{

	replace Array of Array of String is using: [
		['base', 'sys', as Ansi()],
		['base', 'math', as Math()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	## Total complex-plane points evaluated across calls to [smoothEscape].
	Int is pointsRendered: 0;

	## Computes the smooth escape-time value for `(cr, ci)` up to [maxIter], or `-1.0` if inside the set.
	Function of Float is smoothEscape(Float is cr, Float is ci, Int is maxIter){
		pointsRendered: pointsRendered + 1;

		local Float is q: ((cr - 0.25) * (cr - 0.25)) + (ci * ci);
		if({ (q * (q + (cr - 0.25))) <= (0.25 * ci * ci) }, {
			return -1.0;
		});
		if({ ((cr + 1.0) * (cr + 1.0)) + (ci * ci) <= 0.0625 }, {
			return -1.0;
		});

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

		if({ iter >= maxIter }, {
			return -1.0;
		});

		local Float is mag: sqrt(value: zr2 + zi2);
		local Float is logMag: log(value: mag);
		local Float is nu: 0.0;
		if({ logMag > 0.0 }, {
			nu: log2(value: logMag);
		});
		return (toFloat(value: iter) + 1.0) - nu;
	}

	## Maps a smooth escape value [mu] to an xterm 256-color cube index (16 for interior points).
	Function of Int is palette256(Float is mu){
		if({ mu < 0.0 }, {
			return 16;
		});
		local Float is t: mu * 0.18;
		local Float is rf: (0.5 + (0.5 * cos(value: t + 0.0))) * 5.0;
		local Float is gf: (0.5 + (0.5 * cos(value: t + 2.094))) * 5.0;
		local Float is bf: (0.5 + (0.5 * cos(value: t + 4.188))) * 5.0;

		local Int is r: toInt(value: round(value: clampFloat(v: rf, lo: 0.0, hi: 5.0)));
		local Int is g: toInt(value: round(value: clampFloat(v: gf, lo: 0.0, hi: 5.0)));
		local Int is b: toInt(value: round(value: clampFloat(v: bf, lo: 0.0, hi: 5.0)));
		return cubeIndex(r: r, g: g, b: b);
	}

	## Selects a shading glyph (`░`, `▒`, `▓`, `█`, or `' '` for interior) from [mu].
	Function of String is shadeGlyph(Float is mu){
		if({ mu < 0.0 }, {
			return ' ';
		});
		local Int is band: toInt(value: mu * 2.0) % 4;
		return match(when: [
			{ band == 0 }: { '░' },
			{ band == 1 }: { '▒' },
			{ band == 2 }: { '▓' },
			else:          { '█' }
		]);
	}

	## Clamps [v] to the closed interval `[lo, hi]`.
	Function of Float is clampFloat(Float is v, Float is lo, Float is hi){
		return match(when: [
			{ v < lo }: { lo },
			{ v > hi }: { hi },
			else:       { v }
		]);
	}

}
