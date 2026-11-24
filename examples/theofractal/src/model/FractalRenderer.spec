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

	## Renders [fractal] into a flat [TheoColor] pixel array of size `w * h` for [viewport] and [theme].
	Function of Array of TheoColor is renderPixels(Fractal is fractal, ColorTheme is theme, FractalViewport is viewport, Int is w, Int is h){
		local Array of TheoColor is pixels: Array();
		if({ w <= 0 || h <= 0 }, { return pixels; });

		local Array of Float is values: fractal:sampleGrid(viewport: viewport, w: w, h: h);
		local Int is n: values:length();
		local Int is i: 0;
		while({ i < n }, {
			pixels:add(item: colorForValue(t: values:get(index: i), theme: theme));
			i: i + 1;
		});
		return pixels;
	}
}
