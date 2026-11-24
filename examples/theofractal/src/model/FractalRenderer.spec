#! Package theofractal:model
#! Renders any [Fractal] implementation through [ColorPalette] into a flat packed [Color32] pixel list.

Class is FractalRenderer{
	replace [String] is namespace: ['theofractal', 'model'];

	merge [[String]] is using: [
		['theofractal', 'model', [Fractal, ColorTheme, FractalViewport]],
		['theofractal', 'util', as ColorPalette()]
	];

	## Renders [fractal] into a flat packed [Color32] pixel list of size `w * h` for [viewport] and [theme], with optional 2x2 SSAA.
	Function of [Int] is renderPixels(
		Fractal is fractal,
		ColorTheme is theme,
		FractalViewport is viewport,
		Int is w,
		Int is h,
		Boolean is antialiasing: false
	){
		local [Int] is pixels: [];
		if({ w <= 0 || h <= 0 }, { return pixels; });

		if({ !antialiasing }, {
			local [Float] is values: fractal:sampleGrid(viewport: viewport, w: w, h: h);
			local Int is n: values:length();
			local Int is i: 0;
			while({ i < n }, {
				pixels:push(item: color32ForValue(t: values:get(index: i), theme: theme));
				i: i + 1;
			});
			return pixels;
		});

		local Int is sw: w * 2;
		local Int is sh: h * 2;
		local [Float] is sub: fractal:sampleGrid(viewport: viewport, w: sw, h: sh);
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
					pixels:push(item: color32ForValue(t: -1.0, theme: theme));
				}, {
					local Float is f00: if({ s00 < 0.0 }, { 0.0 }, { s00 });
					local Float is f10: if({ s10 < 0.0 }, { 0.0 }, { s10 });
					local Float is f01: if({ s01 < 0.0 }, { 0.0 }, { s01 });
					local Float is f11: if({ s11 < 0.0 }, { 0.0 }, { s11 });
					pixels:push(item: color32ForValue(t: (f00 + f10 + f01 + f11) * 0.25, theme: theme));
				});
				px: px + 1;
			});
			py: py + 1;
		});
		return pixels;
	}
}
