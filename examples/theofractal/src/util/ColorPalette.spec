#! Package theofractal:util
#! Color theme lookup and palette mapping from normalized `[0.0, 1.0]` values to 24-bit RGB [TheoColor]s.

Class is ColorPalette{
	replace [String] is namespace: ['theofractal', 'util'];

	merge [[String]] is using: [
		['theofractal', 'model', ColorTheme],
		['theofractal', 'util', [FractalStrings, as GridRasterizer()]],
		['base', 'theo', [TheoColor, Color32]],
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

	## Maps a normalized value [t] in `[0.0, 1.0]` (or `< 0.0` for background) to a packed [Color32] under [theme] with optional cyclic palette [offset] in `[0.0, 1.0)`.
	Function of Int is color32ForValue(Float is t, ColorTheme is theme, Float is offset: 0.0){
		if({ t < 0.0 }, {
			return Color32:pack(r: 10, g: 12, b: 18);
		});
		local Float is rawU: clamp01(v: t);
		local Float is phase: rawU;
		local Float is u: rawU;
		if({ offset != 0.0 }, {
			phase: rawU + offset;
			phase: phase - floor(value: phase);
			u: 1.0 - abs(value: 2.0 * phase - 1.0);
		});
		return match(when: [
			{ theme == ColorTheme:GRAYSCALE }: {
				local Int is v: toByte(v: 0.12 + 0.88 * u);
				Color32:pack(r: v, g: v, b: v);
			},
			{ theme == ColorTheme:COOL }: {
				local Int is r: toByte(v: 0.05 + 0.65 * (u * u));
				local Int is g: toByte(v: 0.18 + 0.78 * u);
				local Int is b: toByte(v: 0.45 + 0.55 * sqrt(value: u));
				Color32:pack(r: r, g: g, b: b);
			},
			{ theme == ColorTheme:WARM }: {
				local Int is r: toByte(v: 0.35 + 0.65 * sqrt(value: u));
				local Int is g: toByte(v: 0.06 + 0.82 * (u * u));
				local Int is b: toByte(v: 0.04 + 0.46 * (u * u * u));
				Color32:pack(r: r, g: g, b: b);
			},
			else: {
				local Float is angle: phase * 6.2831853;
				local Int is r: toByte(v: 0.5 + 0.5 * cos(value: angle));
				local Int is g: toByte(v: 0.5 + 0.5 * cos(value: angle + 2.0943951));
				local Int is b: toByte(v: 0.5 + 0.5 * cos(value: angle + 4.1887902));
				Color32:pack(r: r, g: g, b: b);
			}
		]);
	}

	## Maps a normalized value [t] in `[0.0, 1.0]` (or `< 0.0` for background) to a [TheoColor] under [theme].
	Function of TheoColor is colorForValue(Float is t, ColorTheme is theme, Float is offset: 0.0){
		return Color32:toTheoColor(color: color32ForValue(t: t, theme: theme, offset: offset));
	}
}
