#! Package base:fabric
#! Theme tokens derived from 8 base [Color]s (primary, secondary, accent, highlight, detail, positive, negative, neutral).

Class is Theme{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', Conditional],
		['base', 'struct', Array],
		['base', 'fabric', Color],
		['base', 'fabric', ThemePreset]
	];

	## Baseline 8 theme colors
	Color is primary: Color(r: 20, g: 23, b: 33);
	Color is secondary: Color(r: 32, g: 37, b: 50);
	Color is accent: Color(r: 100, g: 210, b: 255);
	Color is highlight: Color(r: 68, g: 82, b: 110);
	Color is detail: Color(r: 242, g: 245, b: 250);
	Color is positive: Color(r: 76, g: 175, b: 80);
	Color is negative: Color(r: 239, g: 83, b: 80);
	Color is neutral: Color(r: 160, g: 170, b: 190);

	## Derived ARGB surface/foreground/syntax tokens (populated by deriveTokens)
	Int is windowBg: 0;
	Int is toolbarBg: 0;
	Int is tabBarBg: 0;
	Int is toolbarBorder: 0;
	Int is menuBg: 0;
	Int is menuBorder: 0;
	Int is hoverBg: 0;
	Int is activeBg: 0;
	Int is panelBg: 0;
	Int is panelBorder: 0;
	Int is buttonBorder: 0;
	Int is textPrimary: 0;
	Int is textMuted: 0;
	Int is textAccent: 0;
	Int is positiveColor: 0;
	Int is negativeColor: 0;
	Int is synKeyword: 0;
	Int is synType: 0;
	Int is synString: 0;
	Int is synNumber: 0;
	Int is synComment: 0;
	Int is synPunct: 0;
	Int is synHeading: 0;
	Float is toolbarHeightPt: 19.0;
	Float is menuItemHeightPt: 18.0;
	Float is basePaddingPt: 4.0;
	Float is paddingPt: 4.0;
	Float is sectionPaddingPt: 6.0;
	Float is dialogPaddingPt: 8.0;
	Float is borderThicknessPt: 1.0;
	Float is lineThicknessPt: 1.0;
	String is borderStyle: 'solid';
	Float is uiScaleFactor: 1.0;
	Float is baseTextPt: 11.0;

	replace Function is init(String is preset: 'dark'){
		:applyPreset(preset: Theme:presetFromString(name: preset));
	}

	held Function of Array of ThemePreset is presets(){
		return Array([ThemePreset:LIGHT, ThemePreset:DARK]);
	}

	held Function of String is presetLabel(ThemePreset is preset){
		return Conditional:match(on: preset, when: [
			ThemePreset:LIGHT: { 'Light' },
			ThemePreset:DARK: { 'Dark' }
		]);
	}

	held Function of String is presetId(ThemePreset is preset){
		return Conditional:match(on: preset, when: [
			ThemePreset:LIGHT: { 'light' },
			ThemePreset:DARK: { 'dark' }
		]);
	}

	held Function of ThemePreset is presetFromString(String is name){
		local String is low: name:toLower();
		return Conditional:if(
			check: { low == 'light' || low == 'light_grayscale' },
			then: { ThemePreset:LIGHT },
			else: { ThemePreset:DARK }
		);
	}

	held Function of Theme is forPreset(ThemePreset is preset, Float is baseTextPt: 11.0){
		local Theme is t: Theme();
		t:setBaseTextPt(pt: baseTextPt);
		t:applyPreset(preset: preset);
		return t;
	}

	Function is setBaseTextPt(Float is pt){
		local Float is clamped: if({ pt < 8.0 }, { 8.0 }, { if({ pt > 20.0 }, { 20.0 }, { pt }) });
		:baseTextPt: clamped;
		:deriveTokens();
	}

	Function is setUiScaleFactor(Float is factor){
		:uiScaleFactor: if({ factor > 0.0 }, { factor }, { 1.0 });
	}

	Function is setBorderThicknessPt(Float is pt){
		:borderThicknessPt: if({ pt < 0.0 }, { 0.0 }, { pt });
	}

	Function is setBorderStyle(String is style){
		:borderStyle: style;
		if({ style == 'none' }, {
			:borderThicknessPt: 0.0;
		}, {
		if({ style == 'bold' }, {
			:borderThicknessPt: 2.0;
		}, {
			:borderThicknessPt: 1.0;
		}); });
		:deriveTokens();
	}

	Function of Int is borderPx(Float is scaleFactor: 1.0){
		if({ borderStyle == 'none' || borderThicknessPt <= 0.0 }, { return 0; });
		local Float is sf: if({ scaleFactor > 0.0 }, { scaleFactor }, { 1.0 });
		local Int is px: ((borderThicknessPt * uiScaleFactor * sf) + 0.5) as Int;
		return if({ px < 1 }, { 1 }, { px });
	}

	Function of Int is linePx(Float is scaleFactor: 1.0){
		if({ lineThicknessPt <= 0.0 }, { return 0; });
		local Float is sf: if({ scaleFactor > 0.0 }, { scaleFactor }, { 1.0 });
		local Int is px: ((lineThicknessPt * uiScaleFactor * sf) + 0.5) as Int;
		return if({ px < 1 }, { 1 }, { px });
	}

	Function of Float is scaledTextPt(Float is defaultPt){
		local Float is v: defaultPt * (baseTextPt / 14.0);
		return if({ v < 7.0 }, { 7.0 }, { v });
	}

	## Context-sensitive padding in points, computed as [pct] of [basePaddingPt] (e.g. 0.5 = 50%, 1.0 = 100%, 1.5 = 150%).
	Function of Float is padPt(Float is pct: 1.0){
		return basePaddingPt * pct;
	}

	Function is applyPreset(ThemePreset is preset){
		if({ preset == ThemePreset:LIGHT }, {
			:primary: Color(r: 255, g: 255, b: 255, a: 255);
			:secondary: Color(r: 230, g: 230, b: 230, a: 255);
			:accent: Color(r: 40, g: 40, b: 40, a: 255);
			:highlight: Color(r: 190, g: 190, b: 190, a: 255);
			:detail: Color(r: 28, g: 28, b: 28, a: 255);
			:positive: Color(r: 46, g: 125, b: 50, a: 255);
			:negative: Color(r: 198, g: 40, b: 40, a: 255);
			:neutral: Color(r: 96, g: 96, b: 96, a: 255);
		}, {
			:primary: Color(r: 26, g: 28, b: 34, a: 255);
			:secondary: Color(r: 38, g: 41, b: 49, a: 255);
			:accent: Color(r: 180, g: 190, b: 210, a: 255);
			:highlight: Color(r: 64, g: 70, b: 84, a: 255);
			:detail: Color(r: 232, g: 235, b: 240, a: 255);
			:positive: Color(r: 76, g: 175, b: 80, a: 255);
			:negative: Color(r: 239, g: 83, b: 80, a: 255);
			:neutral: Color(r: 146, g: 152, b: 166, a: 255);
		});
		:deriveTokens();
	}

	held Function of Theme is fromPalette(
		Color is primary,
		Color is secondary,
		Color is accent,
		Color is highlight,
		Color is detail,
		Color is positive: Color(r: 76, g: 175, b: 80),
		Color is negative: Color(r: 239, g: 83, b: 80),
		Color is neutral: Color(r: 140, g: 148, b: 164)
	){
		local Theme is t: Theme();
		t:primary: primary;
		t:secondary: secondary;
		t:accent: accent;
		t:highlight: highlight;
		t:detail: detail;
		t:positive: positive;
		t:negative: negative;
		t:neutral: neutral;
		t:deriveTokens();
		return t;
	}

	Function is deriveTokens(){
		local Boolean is light: primary:isLight();
		windowBg: primary:toArgb();
		toolbarBg: secondary:toArgb();
		tabBarBg: if({ light }, { secondary:darken(amount: 0.07):toArgb() }, { primary:mix(other: secondary, t: 0.35):toArgb() });
		toolbarBorder: if({ light }, { secondary:darken(amount: 0.15):toArgb() }, { highlight:mix(other: secondary, t: 0.25):toArgb() });
		menuBg: if({ light }, { primary:mix(other: secondary, t: 0.40):toArgb() }, { secondary:lighten(amount: 0.04):toArgb() });
		menuBorder: if({ light }, { secondary:darken(amount: 0.23):toArgb() }, { highlight:lighten(amount: 0.08):toArgb() });
		hoverBg: if({ light }, { secondary:mix(other: highlight, t: 0.50):toArgb() }, { secondary:mix(other: highlight, t: 0.65):toArgb() });
		activeBg: highlight:toArgb();
		panelBg: if({ light }, { primary:mix(other: secondary, t: 0.52):toArgb() }, { primary:darken(amount: 0.08):withAlphaByte(a: 210):toArgb() });
		panelBorder: if({ light }, { toolbarBorder }, { highlight:lighten(amount: 0.08):withAlphaByte(a: 235):toArgb() });
		buttonBorder: if({ light }, { secondary:darken(amount: 0.26):toArgb() }, { highlight:lighten(amount: 0.16):toArgb() });
		if({ borderStyle == 'subtle' }, {
			toolbarBorder: Color:fromArgb(argb: toolbarBorder):withAlphaByte(a: 110):toArgb();
			menuBorder: Color:fromArgb(argb: menuBorder):withAlphaByte(a: 120):toArgb();
			panelBorder: Color:fromArgb(argb: panelBorder):withAlphaByte(a: 110):toArgb();
			buttonBorder: Color:fromArgb(argb: buttonBorder):withAlphaByte(a: 120):toArgb();
		});

		textPrimary: detail:toArgb();
		textMuted: neutral:toArgb();
		textAccent: accent:toArgb();
		positiveColor: positive:toArgb();
		negativeColor: negative:toArgb();

		basePaddingPt: 4.0 * (baseTextPt / 11.0);
		paddingPt: basePaddingPt;
		sectionPaddingPt: basePaddingPt * 1.5;
		dialogPaddingPt: basePaddingPt * 2.0;
		local Float is baseBorder: 1.0 * (baseTextPt / 11.0);
		if({ borderStyle == 'none' }, {
			borderThicknessPt: 0.0;
		}, {
		if({ borderStyle == 'bold' }, {
			borderThicknessPt: baseBorder * 2.0;
		}, {
			borderThicknessPt: baseBorder;
		}); });
		lineThicknessPt: baseBorder;

		synKeyword: if({ light }, { detail:darken(amount: 0.35):toArgb() }, { detail:lighten(amount: 0.50):toArgb() });
		synType: if({ light }, { detail:mix(other: neutral, t: 0.20):toArgb() }, { detail:mix(other: neutral, t: 0.32):toArgb() });
		synString: detail:mix(other: neutral, t: 0.76):toArgb();
		synNumber: detail:mix(other: neutral, t: 0.54):toArgb();
		synComment: neutral:mix(other: primary, t: 0.16):toArgb();
		synPunct: neutral:mix(other: primary, t: 0.08):toArgb();
		synHeading: if({ light }, { detail:darken(amount: 0.45):toArgb() }, { detail:lighten(amount: 0.65):toArgb() });
	}

	## Context-sensitive surface elevation helper
	Function of Int is surface(Float is elevation){
		if({ elevation <= 0.0 }, { return primary:toArgb(); });
		local Float is k: if({ elevation > 1.0 }, { 1.0 }, { elevation });
		return if({ primary:isLight() }, { primary:mix(other: secondary, t: k):toArgb() }, { primary:lighten(amount: k * 0.16):toArgb() });
	}

	## Context-sensitive hover color for any surface [base]
	Function of Int is hoverOn(Color is base){
		return if({ primary:isLight() }, { base:darken(amount: 0.08):toArgb() }, { base:lighten(amount: 0.12):toArgb() });
	}

	## Context-sensitive active/pressed color for any surface [base]
	Function of Int is activeOn(Color is base){
		return if({ primary:isLight() }, { base:darken(amount: 0.16):toArgb() }, { base:lighten(amount: 0.22):toArgb() });
	}

	## Context-sensitive border color for any surface [base]
	Function of Int is borderFor(Color is base){
		return base:mix(other: neutral, t: 0.35):toArgb();
	}

	## High-contrast foreground color on top of [bg]
	Function of Int is textOn(Color is bg){
		return if({ bg:isLight() }, { Color(r: 24, g: 24, b: 28):toArgb() }, { Color(r: 244, g: 246, b: 250):toArgb() });
	}

	## Translucent semantic tint surfaces (alpha-channel derived)
	Function of Int is accentSubtle(Float is alpha: 0.18){
		return accent:withAlpha(a: alpha):toArgb();
	}

	Function of Int is highlightSubtle(Float is alpha: 0.22){
		return highlight:withAlpha(a: alpha):toArgb();
	}

	Function of Int is positiveSubtle(Float is alpha: 0.18){
		return positive:withAlpha(a: alpha):toArgb();
	}

	Function of Int is negativeSubtle(Float is alpha: 0.18){
		return negative:withAlpha(a: alpha):toArgb();
	}
}
