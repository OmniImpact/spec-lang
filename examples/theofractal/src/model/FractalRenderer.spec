#! Package theofractal:model
#! Renders any [Fractal] implementation through [ColorPalette] into a flat packed [Color32] pixel list.

Class is FractalRenderer{
	replace [String] is namespace: ['theofractal', 'model'];

	merge [[String]] is using: [
		['theofractal', 'model', [Fractal, ColorTheme, FractalViewport]],
		['theofractal', 'util', as ColorPalette()],
		['base', 'theo', Color32]
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
				local Int is c00: color32ForValue(t: sub:get(index: row0 + sx), theme: theme);
				local Int is c10: color32ForValue(t: sub:get(index: row0 + sx + 1), theme: theme);
				local Int is c01: color32ForValue(t: sub:get(index: row1 + sx), theme: theme);
				local Int is c11: color32ForValue(t: sub:get(index: row1 + sx + 1), theme: theme);
				pixels:push(item: Color32:avg4(c00: c00, c10: c10, c01: c01, c11: c11));
				px: px + 1;
			});
			py: py + 1;
		});
		return pixels;
	}
}
