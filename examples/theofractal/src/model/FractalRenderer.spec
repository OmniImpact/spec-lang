#! Package theofractal:model
#! Renders any [Fractal] implementation through [ColorPalette] into a flat packed [Color32] pixel list.

Class is FractalRenderer{
	replace [String] is namespace: ['theofractal', 'model'];

	merge [[String]] is using: [
		['theofractal', 'model', [Fractal, ColorTheme, FractalViewport, SampleGrid]],
		['theofractal', 'util', as ColorPalette()]
	];

	## Samples [fractal] into a `w * h` [SampleGrid] for [viewport], with coverage-weighted 2x2 SSAA.
	Function of SampleGrid is sampleFractal(
		Fractal is fractal,
		FractalViewport is viewport,
		Int is w,
		Int is h,
		Boolean is antialiasing: false
	){
		if({ w <= 0 || h <= 0 }, { return SampleGrid(); });
		if({ !antialiasing }, {
			return fractal:sampleGridChannels(viewport: viewport, w: w, h: h);
		});

		local Int is sw: w * 2;
		local Int is sh: h * 2;
		local SampleGrid is sub: fractal:sampleGridChannels(viewport: viewport, w: sw, h: sh);
		local [Float] is pal: [];
		local [Float] is cov: [];
		local [Float] is glow: [];
		local Int is py: 0;
		while({ py < h }, {
			local Int is row0: (py * 2) * sw;
			local Int is row1: (py * 2 + 1) * sw;
			local Int is px: 0;
			while({ px < w }, {
				local Int is sx: px * 2;
				local Int is i00: row0 + sx;
				local Int is i10: row0 + sx + 1;
				local Int is i01: row1 + sx;
				local Int is i11: row1 + sx + 1;

				local Float is c00: sub:coverage:get(index: i00);
				local Float is c10: sub:coverage:get(index: i10);
				local Float is c01: sub:coverage:get(index: i01);
				local Float is c11: sub:coverage:get(index: i11);
				local Float is cSum: c00 + c10 + c01 + c11;

				if({ cSum <= 0.0 }, {
					pal:push(item: -1.0);
					cov:push(item: 0.0);
					glow:push(item: 0.0);
				}, {
					local Float is p00: if({ c00 > 0.0 }, { sub:paletteT:get(index: i00) }, { 0.0 });
					local Float is p10: if({ c10 > 0.0 }, { sub:paletteT:get(index: i10) }, { 0.0 });
					local Float is p01: if({ c01 > 0.0 }, { sub:paletteT:get(index: i01) }, { 0.0 });
					local Float is p11: if({ c11 > 0.0 }, { sub:paletteT:get(index: i11) }, { 0.0 });
					local Float is g00: if({ c00 > 0.0 }, { sub:edgeGlow:get(index: i00) }, { 0.0 });
					local Float is g10: if({ c10 > 0.0 }, { sub:edgeGlow:get(index: i10) }, { 0.0 });
					local Float is g01: if({ c01 > 0.0 }, { sub:edgeGlow:get(index: i01) }, { 0.0 });
					local Float is g11: if({ c11 > 0.0 }, { sub:edgeGlow:get(index: i11) }, { 0.0 });

					pal:push(item: (p00 * c00 + p10 * c10 + p01 * c01 + p11 * c11) / cSum);
					cov:push(item: cSum * 0.25);
					glow:push(item: (g00 * c00 + g10 * c10 + g01 * c01 + g11 * c11) / cSum);
				});
				px: px + 1;
			});
			py: py + 1;
		});
		return SampleGrid(paletteT: pal, coverage: cov, edgeGlow: glow);
	}

	## Maps precomputed [samples] through [ColorPalette] combining base color, edge glow, and AA coverage.
	Function of [Int] is colorizeSamples(SampleGrid is samples, ColorTheme is theme, Float is offset: 0.0){
		local [Int] is pixels: [];
		local Int is n: samples:length();
		local Int is i: 0;
		while({ i < n }, {
			pixels:push(item: color32ForSample(
				paletteT: samples:paletteT:get(index: i),
				coverage: samples:coverage:get(index: i),
				edgeGlow: samples:edgeGlow:get(index: i),
				theme: theme,
				offset: offset
			));
			i: i + 1;
		});
		return pixels;
	}

	## Renders [fractal] into a flat packed [Color32] pixel list of size `w * h` for [viewport] and [theme], with optional 2x2 SSAA.
	Function of [Int] is renderPixels(
		Fractal is fractal,
		ColorTheme is theme,
		FractalViewport is viewport,
		Int is w,
		Int is h,
		Boolean is antialiasing: false,
		Float is offset: 0.0
	){
		local SampleGrid is samples: sampleFractal(fractal: fractal, viewport: viewport, w: w, h: h, antialiasing: antialiasing);
		return colorizeSamples(samples: samples, theme: theme, offset: offset);
	}
}
