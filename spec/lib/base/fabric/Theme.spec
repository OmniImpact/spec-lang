#! Package base:fabric
#! Theme tokens derived from base [Color]s (background, surface, primary, secondary, accent, highlight, detail, positive, negative, neutral).

Class is Theme{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', Conditional],
		['base', 'struct', Array],
		['base', 'fabric', Color],
		['base', 'fabric', ThemePreset]
	];

	## Baseline theme colors
	Color is background: Color(r: 26, g: 28, b: 34);
	Color is surface: Color(r: 38, g: 41, b: 49);
	Color is primary: Color(r: 232, g: 235, b: 240);
	Color is secondary: Color(r: 152, g: 158, b: 172);
	Color is accent: Color(r: 100, g: 210, b: 255);
	Color is highlight: Color(r: 68, g: 82, b: 110);
	Color is detail: Color(r: 78, g: 84, b: 98);
	Color is positive: Color(r: 76, g: 175, b: 80);
	Color is negative: Color(r: 239, g: 83, b: 80);
	Color is neutral: Color(r: 146, g: 152, b: 166);

	## Derived ARGB surface/foreground/syntax tokens (populated by deriveTokens)
	Int is windowBg: 0;
	Int is surfaceBg: 0;
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
	Float is paddingTinyPt: 1.0;
	Float is paddingSmallPt: 2.0;
	Float is paddingPt: 4.0;
	Float is paddingMediumPt: 6.0;
	Float is paddingLargePt: 8.0;
	Float is sectionPaddingPt: 6.0;
	Float is dialogPaddingPt: 8.0;
	Float is buttonMinWidthPt: 56.0;
	Float is buttonHeightPt: 20.0;
	Float is inputMinWidthPt: 110.0;
	Float is inputHeightPt: 20.0;
	Float is tabBarHeightPt: 19.0;
	Float is tabMinWidthPt: 80.0;
	Float is tabMaxWidthPt: 180.0;
	Float is barHeightPt: 18.0;
	Float is scrollbarWidthPt: 10.0;
	Float is splitterSpacingPt: 4.0;
	Float is panelMinSizePt: 36.0;
	Float is iconSizePt: 12.0;
	Float is lineGapPt: 3.0;
	Float is editorPadPt: 8.0;
	Float is borderThicknessPt: 1.0;
	Float is lineThicknessPt: 1.0;
	String is borderStyle: 'solid';
	String is panelBorderStyle: 'single';
	Float is panelBorderThicknessPt: 1.0;
	Float is panelCornerRadiusPt: 0.0;
	Float is panelShadowBlurPt: 0.0;
	String is dividerStyle: 'single';
	Float is dividerThicknessPt: 1.0;
	String is buttonBorderStyle: 'single';
	Float is buttonBorderThicknessPt: 1.0;
	Float is buttonCornerRadiusPt: 0.0;
	Float is buttonShadowBlurPt: 0.0;
	Float is uiScaleFactor: 1.0;
	Float is baseTextPt: 10.0;
	Boolean is customMetrics: false;

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

	held Function of Theme is forPreset(ThemePreset is preset, Float is baseTextPt: 10.0){
		local Theme is t: Theme();
		t:setBaseTextPt(pt: baseTextPt);
		t:applyPreset(preset: preset);
		return t;
	}

	Function is setBaseTextPt(Float is pt){
		local Float is clamped: if({ pt < 8.0 }, { 8.0 }, { if({ pt > 20.0 }, { 20.0 }, { pt }) });
		if({ clamped != baseTextPt }, {
			:baseTextPt: clamped;
			if({ !customMetrics }, { :deriveMetrics(); });
		});
		:deriveColors();
	}

	Function is setBasePaddingPt(Float is pt){
		local Float is clamped: if({ pt < 1.0 }, { 1.0 }, { if({ pt > 24.0 }, { 24.0 }, { pt }) });
		:customMetrics: true;
		:basePaddingPt: clamped;
		:paddingTinyPt: clamped * 0.25;
		:paddingSmallPt: clamped * 0.50;
		:paddingPt: clamped;
		:paddingMediumPt: clamped * 1.50;
		:paddingLargePt: clamped * 2.00;
	}

	Function is setSectionPaddingPt(Float is pt){
		:customMetrics: true;
		:sectionPaddingPt: if({ pt < 0.0 }, { 0.0 }, { if({ pt > 32.0 }, { 32.0 }, { pt }) });
	}

	Function is setDialogPaddingPt(Float is pt){
		:customMetrics: true;
		:dialogPaddingPt: if({ pt < 0.0 }, { 0.0 }, { if({ pt > 32.0 }, { 32.0 }, { pt }) });
	}

	Function is setSplitterSpacingPt(Float is pt){
		:customMetrics: true;
		:splitterSpacingPt: if({ pt < 1.0 }, { 1.0 }, { if({ pt > 24.0 }, { 24.0 }, { pt }) });
	}

	Function is setLineGapPt(Float is pt){
		:customMetrics: true;
		:lineGapPt: if({ pt < 0.0 }, { 0.0 }, { if({ pt > 24.0 }, { 24.0 }, { pt }) });
	}

	Function is setEditorPadPt(Float is pt){
		:customMetrics: true;
		:editorPadPt: if({ pt < 0.0 }, { 0.0 }, { if({ pt > 32.0 }, { 32.0 }, { pt }) });
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
		if({ !customMetrics }, {
			:panelBorderThicknessPt: borderThicknessPt;
			:dividerThicknessPt: borderThicknessPt;
			:buttonBorderThicknessPt: borderThicknessPt;
		});
		:deriveColors();
	}

	Function is setPanelBorderStyle(String is style){
		:customMetrics: true;
		:panelBorderStyle: style;
		if({ style == 'none' }, {
			:panelBorderThicknessPt: 0.0;
		}, {
		if({ panelBorderThicknessPt <= 0.0 }, {
			:panelBorderThicknessPt: 1.0;
		}); });
	}

	Function is setPanelBorderThicknessPt(Float is pt){
		:customMetrics: true;
		:panelBorderThicknessPt: if({ pt < 0.0 }, { 0.0 }, { if({ pt > 12.0 }, { 12.0 }, { pt }) });
	}

	Function is setPanelCornerRadiusPt(Float is pt){
		:customMetrics: true;
		:panelCornerRadiusPt: if({ pt < 0.0 }, { 0.0 }, { if({ pt > 24.0 }, { 24.0 }, { pt }) });
	}

	Function is setPanelShadowBlurPt(Float is pt){
		:customMetrics: true;
		:panelShadowBlurPt: if({ pt < 0.0 }, { 0.0 }, { if({ pt > 24.0 }, { 24.0 }, { pt }) });
	}

	Function is setDividerStyle(String is style){
		:customMetrics: true;
		:dividerStyle: style;
		if({ style == 'none' }, {
			:dividerThicknessPt: 0.0;
		}, {
		if({ dividerThicknessPt <= 0.0 }, {
			:dividerThicknessPt: 1.0;
		}); });
	}

	Function is setDividerThicknessPt(Float is pt){
		:customMetrics: true;
		:dividerThicknessPt: if({ pt < 0.0 }, { 0.0 }, { if({ pt > 12.0 }, { 12.0 }, { pt }) });
	}

	Function is setButtonBorderStyle(String is style){
		:customMetrics: true;
		:buttonBorderStyle: style;
		if({ style == 'none' }, {
			:buttonBorderThicknessPt: 0.0;
		}, {
		if({ buttonBorderThicknessPt <= 0.0 }, {
			:buttonBorderThicknessPt: 1.0;
		}); });
	}

	Function is setButtonBorderThicknessPt(Float is pt){
		:customMetrics: true;
		:buttonBorderThicknessPt: if({ pt < 0.0 }, { 0.0 }, { if({ pt > 12.0 }, { 12.0 }, { pt }) });
	}

	Function is setButtonCornerRadiusPt(Float is pt){
		:customMetrics: true;
		:buttonCornerRadiusPt: if({ pt < 0.0 }, { 0.0 }, { if({ pt > 20.0 }, { 20.0 }, { pt }) });
	}

	Function is setButtonShadowBlurPt(Float is pt){
		:customMetrics: true;
		:buttonShadowBlurPt: if({ pt < 0.0 }, { 0.0 }, { if({ pt > 20.0 }, { 20.0 }, { pt }) });
	}

	Function of Int is borderPx(Float is scaleFactor: 1.0){
		if({ borderStyle == 'none' || borderThicknessPt <= 0.0 }, { return 0; });
		local Float is sf: if({ scaleFactor > 0.0 }, { scaleFactor }, { 1.0 });
		local Int is px: ((borderThicknessPt * uiScaleFactor * sf) + 0.5) as Int;
		return if({ px < 1 }, { 1 }, { px });
	}

	Function of Int is panelBorderPx(Float is scaleFactor: 1.0){
		if({ panelBorderStyle == 'none' || panelBorderThicknessPt <= 0.0 }, { return 0; });
		local Float is sf: if({ scaleFactor > 0.0 }, { scaleFactor }, { 1.0 });
		local Int is px: ((panelBorderThicknessPt * uiScaleFactor * sf) + 0.5) as Int;
		return if({ px < 1 }, { 1 }, { px });
	}

	Function of Int is dividerPx(Float is scaleFactor: 1.0){
		if({ dividerStyle == 'none' || dividerThicknessPt <= 0.0 }, { return 0; });
		local Float is sf: if({ scaleFactor > 0.0 }, { scaleFactor }, { 1.0 });
		local Int is px: ((dividerThicknessPt * uiScaleFactor * sf) + 0.5) as Int;
		return if({ px < 1 }, { 1 }, { px });
	}

	Function of Int is buttonBorderPx(Float is scaleFactor: 1.0){
		if({ buttonBorderStyle == 'none' || buttonBorderThicknessPt <= 0.0 }, { return 0; });
		local Float is sf: if({ scaleFactor > 0.0 }, { scaleFactor }, { 1.0 });
		local Int is px: ((buttonBorderThicknessPt * uiScaleFactor * sf) + 0.5) as Int;
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
			:background: Color(r: 255, g: 255, b: 255, a: 255);
			:surface: Color(r: 236, g: 238, b: 242, a: 255);
			:primary: Color(r: 28, g: 28, b: 28, a: 255);
			:secondary: Color(r: 96, g: 96, b: 96, a: 255);
			:accent: Color(r: 40, g: 40, b: 40, a: 255);
			:highlight: Color(r: 190, g: 190, b: 190, a: 255);
			:detail: Color(r: 176, g: 180, b: 188, a: 255);
			:positive: Color(r: 46, g: 125, b: 50, a: 255);
			:negative: Color(r: 198, g: 40, b: 40, a: 255);
			:neutral: Color(r: 115, g: 115, b: 115, a: 255);
		}, {
			:background: Color(r: 26, g: 28, b: 34, a: 255);
			:surface: Color(r: 38, g: 41, b: 49, a: 255);
			:primary: Color(r: 232, g: 235, b: 240, a: 255);
			:secondary: Color(r: 152, g: 158, b: 172, a: 255);
			:accent: Color(r: 180, g: 190, b: 210, a: 255);
			:highlight: Color(r: 64, g: 70, b: 84, a: 255);
			:detail: Color(r: 78, g: 84, b: 98, a: 255);
			:positive: Color(r: 76, g: 175, b: 80, a: 255);
			:negative: Color(r: 239, g: 83, b: 80, a: 255);
			:neutral: Color(r: 146, g: 152, b: 166, a: 255);
		});
		:customMetrics: false;
		:panelBorderStyle: 'single';
		:panelCornerRadiusPt: 0.0;
		:panelShadowBlurPt: 0.0;
		:dividerStyle: 'single';
		:buttonBorderStyle: 'single';
		:buttonCornerRadiusPt: 0.0;
		:buttonShadowBlurPt: 0.0;
		:deriveTokens();
	}

	held Function of Theme is fromPalette(
		Color is background,
		Color is surface,
		Color is primary,
		Color is secondary,
		Color is accent,
		Color is highlight,
		Color is detail: Color(r: 78, g: 84, b: 98),
		Color is positive: Color(r: 76, g: 175, b: 80),
		Color is negative: Color(r: 239, g: 83, b: 80),
		Color is neutral: Color(r: 140, g: 148, b: 164)
	){
		local Theme is t: Theme();
		t:background: background;
		t:surface: surface;
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

	Function is deriveColors(){
		local Boolean is light: background:isLight();
		windowBg: background:toArgb();
		surfaceBg: surface:toArgb();
		toolbarBg: surface:toArgb();
		tabBarBg: if({ light }, { surface:darken(amount: 0.07):toArgb() }, { background:mix(other: surface, t: 0.45):toArgb() });
		toolbarBorder: if({ light }, { detail:toArgb() }, { detail:mix(other: surface, t: 0.25):toArgb() });
		menuBg: if({ light }, { background:mix(other: surface, t: 0.65):toArgb() }, { surface:lighten(amount: 0.04):toArgb() });
		menuBorder: if({ light }, { surface:darken(amount: 0.23):toArgb() }, { highlight:lighten(amount: 0.08):toArgb() });
		hoverBg: if({ light }, { surface:mix(other: highlight, t: 0.50):toArgb() }, { surface:mix(other: highlight, t: 0.65):toArgb() });
		activeBg: highlight:toArgb();
		panelBg: surface:toArgb();
		panelBorder: if({ light }, { toolbarBorder }, { detail:lighten(amount: 0.08):withAlphaByte(a: 235):toArgb() });
		buttonBorder: if({ light }, { surface:darken(amount: 0.26):toArgb() }, { highlight:lighten(amount: 0.16):toArgb() });
		if({ borderStyle == 'subtle' }, {
			toolbarBorder: Color:fromArgb(argb: toolbarBorder):withAlphaByte(a: 110):toArgb();
			menuBorder: Color:fromArgb(argb: menuBorder):withAlphaByte(a: 120):toArgb();
			panelBorder: Color:fromArgb(argb: panelBorder):withAlphaByte(a: 110):toArgb();
			buttonBorder: Color:fromArgb(argb: buttonBorder):withAlphaByte(a: 120):toArgb();
		});

		textPrimary: primary:toArgb();
		textMuted: secondary:toArgb();
		textAccent: accent:toArgb();
		positiveColor: positive:toArgb();
		negativeColor: negative:toArgb();

		synKeyword: if({ light }, { primary:darken(amount: 0.35):toArgb() }, { primary:lighten(amount: 0.50):toArgb() });
		synType: if({ light }, { primary:mix(other: neutral, t: 0.20):toArgb() }, { primary:mix(other: neutral, t: 0.32):toArgb() });
		synString: primary:mix(other: neutral, t: 0.76):toArgb();
		synNumber: primary:mix(other: neutral, t: 0.54):toArgb();
		synComment: neutral:mix(other: background, t: 0.16):toArgb();
		synPunct: neutral:mix(other: background, t: 0.08):toArgb();
		synHeading: if({ light }, { primary:darken(amount: 0.45):toArgb() }, { primary:lighten(amount: 0.65):toArgb() });
	}

	Function is deriveMetrics(){
		basePaddingPt: 4.0 * (baseTextPt / 11.0);
		paddingTinyPt: basePaddingPt * 0.25;
		paddingSmallPt: basePaddingPt * 0.50;
		paddingPt: basePaddingPt;
		paddingMediumPt: basePaddingPt * 1.50;
		paddingLargePt: basePaddingPt * 2.00;
		sectionPaddingPt: paddingMediumPt;
		dialogPaddingPt: paddingLargePt;

		toolbarHeightPt: baseTextPt + basePaddingPt * 1.75;
		menuItemHeightPt: baseTextPt + basePaddingPt * 1.75;
		buttonMinWidthPt: baseTextPt * 5.0;
		buttonHeightPt: baseTextPt + basePaddingPt * 2.25;
		inputMinWidthPt: baseTextPt * 10.0;
		inputHeightPt: baseTextPt + basePaddingPt * 2.25;
		tabBarHeightPt: baseTextPt + basePaddingPt * 1.25;
		tabMinWidthPt: baseTextPt * 7.25;
		tabMaxWidthPt: baseTextPt * 16.0;
		barHeightPt: baseTextPt + basePaddingPt * 1.50;
		scrollbarWidthPt: basePaddingPt * 2.5;
		splitterSpacingPt: basePaddingPt;
		panelMinSizePt: baseTextPt * 3.25;
		iconSizePt: baseTextPt * 1.1;
		lineGapPt: basePaddingPt * 0.75;
		editorPadPt: paddingLargePt;
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
		panelBorderThicknessPt: borderThicknessPt;
		dividerThicknessPt: borderThicknessPt;
		buttonBorderThicknessPt: borderThicknessPt;
	}

	Function is deriveTokens(){
		:deriveColors();
		if({ !customMetrics }, { :deriveMetrics(); });
	}

	## Context-sensitive surface elevation helper
	Function of Int is surfaceAt(Float is elevation){
		if({ elevation <= 0.0 }, { return background:toArgb(); });
		local Float is k: if({ elevation > 1.0 }, { 1.0 }, { elevation });
		return if({ background:isLight() }, { background:mix(other: surface, t: k):toArgb() }, { background:mix(other: surface, t: k):toArgb() });
	}

	## Context-sensitive hover color for any surface [base]
	Function of Int is hoverOn(Color is base){
		return if({ background:isLight() }, { base:darken(amount: 0.08):toArgb() }, { base:lighten(amount: 0.12):toArgb() });
	}

	## Context-sensitive active/pressed color for any surface [base]
	Function of Int is activeOn(Color is base){
		return if({ background:isLight() }, { base:darken(amount: 0.16):toArgb() }, { base:lighten(amount: 0.22):toArgb() });
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
