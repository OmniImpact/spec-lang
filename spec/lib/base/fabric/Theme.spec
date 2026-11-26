#! Package base:fabric
#! Theme tokens derived from 8 base [Color]s (primary, secondary, accent, highlight, detail, positive, negative, neutral).

Class is Theme{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'fabric', Color]
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
	Float is toolbarHeightPt: 30.0;
	Float is menuItemHeightPt: 28.0;
	Float is paddingPt: 8.0;

	replace Function is init(String is preset: 'dark'){
		if({ preset == 'light_grayscale' }, {
			:primary: Color(r: 255, g: 255, b: 255, a: 255);
			:secondary: Color(r: 230, g: 230, b: 230, a: 255);
			:accent: Color(r: 40, g: 40, b: 40, a: 255);
			:highlight: Color(r: 190, g: 190, b: 190, a: 255);
			:detail: Color(r: 28, g: 28, b: 28, a: 255);
			:positive: Color(r: 46, g: 125, b: 50, a: 255);
			:negative: Color(r: 198, g: 40, b: 40, a: 255);
			:neutral: Color(r: 96, g: 96, b: 96, a: 255);
		}, {
			:primary: Color(r: 20, g: 23, b: 33, a: 255);
			:secondary: Color(r: 32, g: 37, b: 50, a: 255);
			:accent: Color(r: 100, g: 210, b: 255, a: 255);
			:highlight: Color(r: 68, g: 82, b: 110, a: 255);
			:detail: Color(r: 242, g: 245, b: 250, a: 255);
			:positive: Color(r: 76, g: 175, b: 80, a: 255);
			:negative: Color(r: 239, g: 83, b: 80, a: 255);
			:neutral: Color(r: 160, g: 170, b: 190, a: 255);
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

		textPrimary: detail:toArgb();
		textMuted: neutral:toArgb();
		textAccent: accent:toArgb();
		positiveColor: positive:toArgb();
		negativeColor: negative:toArgb();

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
