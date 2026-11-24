#! Package theofractal:model
#! Renders any [Fractal] implementation through [ColorPalette] into a flat [TheoColor] pixel array.

Class is FractalRenderer{
	replace [String] is namespace: ['theofractal', 'model'];

	replace [[String]] is using: [
		['theofractal', 'model', [Fractal, ColorTheme, FractalViewport]],
		['theofractal', 'util', as ColorPalette()],
		['base', 'theo', TheoColor],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	## Renders [fractal] into a flat [TheoColor] pixel array of size `w * h` for [viewport] and [theme], with optional 2x2 SSAA.
	Function of Array of TheoColor is renderPixels(
		Fractal is fractal,
		ColorTheme is theme,
		FractalViewport is viewport,
		Int is w,
		Int is h,
		Boolean is antialiasing: false
	){
		local Array of TheoColor is pixels: Array();
		if({ w <= 0 || h <= 0 }, { return pixels; });

		if({ !antialiasing }, {
			local Array of Float is values: fractal:sampleGrid(viewport: viewport, w: w, h: h);
			local Int is n: values:length();
			local Int is i: 0;
			while({ i < n }, {
				pixels:add(item: colorForValue(t: values:get(index: i), theme: theme));
				i: i + 1;
			});
			return pixels;
		});

		local Int is sw: w * 2;
		local Int is sh: h * 2;
		local Array of Float is sub: fractal:sampleGrid(viewport: viewport, w: sw, h: sh);
		local Int is py: 0;
		while({ py < h }, {
			local Int is row0: (py * 2) * sw;
			local Int is row1: (py * 2 + 1) * sw;
			local Int is px: 0;
			while({ px < w }, {
				local Int is sx: px * 2;
				local TheoColor is c00: colorForValue(t: sub:get(index: row0 + sx), theme: theme);
				local TheoColor is c10: colorForValue(t: sub:get(index: row0 + sx + 1), theme: theme);
				local TheoColor is c01: colorForValue(t: sub:get(index: row1 + sx), theme: theme);
				local TheoColor is c11: colorForValue(t: sub:get(index: row1 + sx + 1), theme: theme);
				local Int is r: (c00:c1 + c10:c1 + c01:c1 + c11:c1) / 4;
				local Int is g: (c00:c2 + c10:c2 + c01:c2 + c11:c2) / 4;
				local Int is b: (c00:c3 + c10:c3 + c01:c3 + c11:c3) / 4;
				pixels:add(item: TheoColor:rgb(r: r, g: g, b: b));
				px: px + 1;
			});
			py: py + 1;
		});
		return pixels;
	}
}
