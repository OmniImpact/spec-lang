#! Package theofractal:util
#! Color theme lookup and palette mapping from normalized `[0.0, 1.0]` values to 24-bit RGB [TheoColor]s.

Class is ColorPalette{
	replace [String] is namespace: ['theofractal', 'util'];

	merge [[String]] is using: [
		['theofractal', 'model', ColorTheme],
		['theofractal', 'util', [FractalStrings, as GridRasterizer()]],
		['base', 'theo', TheoColor],
		['base', 'math', as Math()]
	];

	Function of Int is toByte(Float is v){
		local Int is b: toInt(value: round(value: clamp01(v: v) * 255.0));
		if({ b < 0 }, { return 0; });
		if({ b > 255 }, { return 255; });
		return b;
	}

	Function of ColorTheme is themeFromName(String is name){
		return match(when: [
			{ name == FractalStrings:THEME_COOL }: { ColorTheme:COOL },
			{ name == FractalStrings:THEME_WARM }: { ColorTheme:WARM },
			{ name == FractalStrings:THEME_RAINBOW }: { ColorTheme:RAINBOW },
			else: { ColorTheme:GRAYSCALE }
		]);
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
}
