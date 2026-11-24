#! Package theofractal:model
#! Renders any [Fractal] implementation through [ColorPalette] into a flat packed [Color32] pixel list.

Class is FractalRenderer{
	replace [String] is namespace: ['theofractal', 'model'];

	merge [[String]] is using: [
		['theofractal', 'model', [Fractal, ColorTheme, FractalViewport]],
		['theofractal', 'util', as ColorPalette()]
	];

	## Samples [fractal] into a `w * h` normalized intensity list for [viewport], with optional 2x2 SSAA.
	Function of [Float] is sampleFractal(
		Fractal is fractal,
		FractalViewport is viewport,
		Int is w,
		Int is h,
		Boolean is antialiasing: false
	){
		if({ w <= 0 || h <= 0 }, { return []; });
		if({ !antialiasing }, {
			return fractal:sampleGrid(viewport: viewport, w: w, h: h);
		});

		local Int is sw: w * 2;
		local Int is sh: h * 2;
		local [Float] is sub: fractal:sampleGrid(viewport: viewport, w: sw, h: sh);
		local [Float] is samples: [];
		local Int is py: 0;
		while({ py < h }, {
			local Int is row0: (py * 2) * sw;
			local Int is row1: (py * 2 + 1) * sw;
			local Int is px: 0;
			while({ px < w }, {
				local Int is sx: px * 2;
				local Float is s00: sub:get(index: row0 + sx);
				local Float is s10: sub:get(index: row0 + sx + 1);
				local Float is s01: sub:get(index: row1 + sx);
				local Float is s11: sub:get(index: row1 + sx + 1);
				if({ s00 < 0.0 && s10 < 0.0 && s01 < 0.0 && s11 < 0.0 }, {
					samples:push(item: -1.0);
				}, {
					local Float is f00: if({ s00 < 0.0 }, { 0.0 }, { s00 });
					local Float is f10: if({ s10 < 0.0 }, { 0.0 }, { s10 });
					local Float is f01: if({ s01 < 0.0 }, { 0.0 }, { s01 });
					local Float is f11: if({ s11 < 0.0 }, { 0.0 }, { s11 });
					samples:push(item: (f00 + f10 + f01 + f11) * 0.25);
				});
				px: px + 1;
			});
			py: py + 1;
		});
		return samples;
	}

	## Maps precomputed [samples] through [ColorPalette] with optional cyclic [offset].
	Function of [Int] is colorizeSamples([Float] is samples, ColorTheme is theme, Float is offset: 0.0){
		local [Int] is pixels: [];
		local Int is n: samples:length();
		local Int is i: 0;
		while({ i < n }, {
			pixels:push(item: color32ForValue(t: samples:get(index: i), theme: theme, offset: offset));
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
		local [Float] is samples: sampleFractal(fractal: fractal, viewport: viewport, w: w, h: h, antialiasing: antialiasing);
		return colorizeSamples(samples: samples, theme: theme, offset: offset);
	}
}
