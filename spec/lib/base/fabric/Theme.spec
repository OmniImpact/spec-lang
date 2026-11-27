#! Package base:fabric
#! Theme tokens derived from base [Color]s (background, surface, primary, secondary, accent, highlight, detail, positive, negative, neutral).

Class is Theme{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', Conditional],
		['base', 'sys', as Introspection()],
		['base', 'core', Result],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'data', Json],
		['base', 'data', JsonNumber],
		['base', 'data', JsonBool],
		['base', 'fabric', Color],
		['base', 'fabric', ThemePreset],
		['base', 'fabric', LineWidthStyle],
		['base', 'fabric', LineColorStyle],
		['base', 'fabric', ShadowStyle],
		['base', 'fabric', LineStyle],
		['base', 'fabric', BoxBorderStyle],
		['base', 'fabric', FillMode],
		['base', 'fabric', GradientBounds],
		['base', 'fabric', FillStyle]
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
	Int is customPanelBorderColor: 0;
	Int is customDividerColor: 0;
	Int is customButtonBorderColor: 0;
	FillStyle is surfaceFill: FillStyle();
	FillStyle is buttonFill: FillStyle();
	Boolean is customSurfaceFill: false;
	Boolean is customButtonFill: false;
	Float is hoverBrightness: 0.08;
	Float is hoverTintShiftDeg: 0.0;
	Float is hoverSaturationShift: 0.0;
	Float is selectedBrightness: 0.22;
	Float is selectedTintShiftDeg: 0.0;
	Float is selectedSaturationShift: 0.0;
	Float is focusBrightness: 0.14;
	Float is focusTintShiftDeg: 0.0;
	Float is focusSaturationShift: 0.0;
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
	Float is borderThicknessPt: 0.7;
	Float is lineThicknessPt: 0.7;
	String is borderStyle: 'solid';
	String is panelBorderStyle: 'single';
	Float is panelBorderThicknessPt: 0.7;
	Float is panelCornerRadiusPt: 0.0;
	Float is panelShadowBlurPt: 0.0;
	Float is panelShadowOffsetXPt: 0.0;
	Float is panelShadowOffsetYPt: 0.0;
	Float is panelInnerShadowBlurPt: 0.0;
	Float is panelInnerShadowOffsetXPt: 0.0;
	Float is panelInnerShadowOffsetYPt: 0.0;
	String is dividerStyle: 'single';
	Float is dividerThicknessPt: 0.5;
	String is buttonBorderStyle: 'single';
	Float is buttonBorderThicknessPt: 0.7;
	Float is buttonCornerRadiusPt: 2.0;
	Float is buttonShadowBlurPt: 0.0;
	Float is buttonShadowOffsetXPt: 0.0;
	Float is buttonShadowOffsetYPt: 0.0;
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
			:borderThicknessPt: 1.4;
		}, {
			:borderThicknessPt: 0.7;
		}); });
		if({ !customMetrics }, {
			:panelBorderThicknessPt: borderThicknessPt;
			:dividerThicknessPt: if({ style == 'none' }, { 0.0 }, { if({ style == 'bold' }, { 1.0 }, { 0.5 }) });
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
			:panelBorderThicknessPt: 0.7;
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

	Function is setPanelShadowOffsetXPt(Float is pt){
		:customMetrics: true;
		:panelShadowOffsetXPt: if({ pt < -16.0 }, { -16.0 }, { if({ pt > 16.0 }, { 16.0 }, { pt }) });
	}

	Function is setPanelShadowOffsetYPt(Float is pt){
		:customMetrics: true;
		:panelShadowOffsetYPt: if({ pt < -16.0 }, { -16.0 }, { if({ pt > 16.0 }, { 16.0 }, { pt }) });
	}

	Function is setPanelInnerShadowBlurPt(Float is pt){
		:customMetrics: true;
		:panelInnerShadowBlurPt: if({ pt < 0.0 }, { 0.0 }, { if({ pt > 24.0 }, { 24.0 }, { pt }) });
	}

	Function is setPanelInnerShadowOffsetXPt(Float is pt){
		:customMetrics: true;
		:panelInnerShadowOffsetXPt: if({ pt < -16.0 }, { -16.0 }, { if({ pt > 16.0 }, { 16.0 }, { pt }) });
	}

	Function is setPanelInnerShadowOffsetYPt(Float is pt){
		:customMetrics: true;
		:panelInnerShadowOffsetYPt: if({ pt < -16.0 }, { -16.0 }, { if({ pt > 16.0 }, { 16.0 }, { pt }) });
	}

	Function is setDividerStyle(String is style){
		:customMetrics: true;
		:dividerStyle: style;
		if({ style == 'none' }, {
			:dividerThicknessPt: 0.0;
		}, {
		if({ dividerThicknessPt <= 0.0 }, {
			:dividerThicknessPt: 0.5;
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
			:buttonBorderThicknessPt: 0.7;
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

	Function is setButtonShadowOffsetXPt(Float is pt){
		:customMetrics: true;
		:buttonShadowOffsetXPt: if({ pt < -16.0 }, { -16.0 }, { if({ pt > 16.0 }, { 16.0 }, { pt }) });
	}

	Function is setButtonShadowOffsetYPt(Float is pt){
		:customMetrics: true;
		:buttonShadowOffsetYPt: if({ pt < -16.0 }, { -16.0 }, { if({ pt > 16.0 }, { 16.0 }, { pt }) });
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

	Function of Int is panelBorderColorArgb(){
		return if({ customPanelBorderColor != 0 }, { customPanelBorderColor }, { textAccent });
	}

	Function of Int is dividerColorArgb(){
		return if({ customDividerColor != 0 }, { customDividerColor }, { toolbarBorder });
	}

	Function of Int is buttonBorderColorArgb(){
		return if({ customButtonBorderColor != 0 }, { customButtonBorderColor }, { buttonBorder });
	}

	Function of BoxBorderStyle is panelBorderConfig(){
		return BoxBorderStyle(
			widthPt: panelBorderThicknessPt,
			color: Color:fromArgb(argb: :panelBorderColorArgb()),
			style: panelBorderStyle,
			radiusPt: panelCornerRadiusPt,
			shadow: ShadowStyle(blurPt: panelShadowBlurPt, offsetXPt: panelShadowOffsetXPt, offsetYPt: panelShadowOffsetYPt),
			innerShadow: ShadowStyle(blurPt: panelInnerShadowBlurPt, offsetXPt: panelInnerShadowOffsetXPt, offsetYPt: panelInnerShadowOffsetYPt, inset: true)
		);
	}

	Function of LineStyle is dividerConfig(){
		return LineStyle(
			widthPt: dividerThicknessPt,
			color: Color:fromArgb(argb: :dividerColorArgb()),
			style: dividerStyle
		);
	}

	Function of BoxBorderStyle is buttonBorderConfig(){
		return BoxBorderStyle(
			widthPt: buttonBorderThicknessPt,
			color: Color:fromArgb(argb: :buttonBorderColorArgb()),
			style: buttonBorderStyle,
			radiusPt: buttonCornerRadiusPt,
			shadow: ShadowStyle(blurPt: buttonShadowBlurPt, offsetXPt: buttonShadowOffsetXPt, offsetYPt: buttonShadowOffsetYPt)
		);
	}

	Function is setPanelBorder(BoxBorderStyle is border){
		:customMetrics: true;
		if({ border:hasStyle }, { :setPanelBorderStyle(style: border:style); });
		if({ border:hasWidth }, { :setPanelBorderThicknessPt(pt: border:widthPt); });
		if({ border:hasColor }, { :customPanelBorderColor: border:lineColor:toArgb(); });
		if({ border:hasRadius }, { :setPanelCornerRadiusPt(pt: border:radiusPt); });
		if({ border:hasShadow }, {
			:setPanelShadowBlurPt(pt: border:shadow:blurPt);
			:setPanelShadowOffsetXPt(pt: border:shadow:offsetXPt);
			:setPanelShadowOffsetYPt(pt: border:shadow:offsetYPt);
		});
		if({ border:hasInnerShadow }, {
			:setPanelInnerShadowBlurPt(pt: border:innerShadow:blurPt);
			:setPanelInnerShadowOffsetXPt(pt: border:innerShadow:offsetXPt);
			:setPanelInnerShadowOffsetYPt(pt: border:innerShadow:offsetYPt);
		});
	}

	Function is setPanelBorder(LineStyle is line){
		:customMetrics: true;
		if({ line:hasStyle }, { :setPanelBorderStyle(style: line:style); });
		if({ line:hasWidth }, { :setPanelBorderThicknessPt(pt: line:widthPt); });
		if({ line:hasColor }, { :customPanelBorderColor: line:lineColor:toArgb(); });
	}

	Function is setPanelBorder(LineWidthStyle is width){
		if({ width:hasWidth }, { :setPanelBorderThicknessPt(pt: width:widthPt); });
	}

	Function is setPanelBorder(LineColorStyle is col){
		if({ col:hasColor }, { :customPanelBorderColor: col:lineColor:toArgb(); });
	}

	Function is setPanelBorder(Float is thicknessPt){
		:setPanelBorderThicknessPt(pt: thicknessPt);
	}

	Function is setPanelBorder(Int is thicknessPt){
		:setPanelBorderThicknessPt(pt: thicknessPt as Float);
	}

	Function is setPanelBorder(Color is color){
		:customPanelBorderColor: color:toArgb();
	}

	Function is setDivider(LineStyle is line){
		:customMetrics: true;
		if({ line:hasStyle }, { :setDividerStyle(style: line:style); });
		if({ line:hasWidth }, { :setDividerThicknessPt(pt: line:widthPt); });
		if({ line:hasColor }, { :customDividerColor: line:lineColor:toArgb(); });
	}

	Function is setDivider(LineWidthStyle is width){
		if({ width:hasWidth }, { :setDividerThicknessPt(pt: width:widthPt); });
	}

	Function is setDivider(LineColorStyle is col){
		if({ col:hasColor }, { :customDividerColor: col:lineColor:toArgb(); });
	}

	Function is setDivider(Float is thicknessPt){
		:setDividerThicknessPt(pt: thicknessPt);
	}

	Function is setDivider(Int is thicknessPt){
		:setDividerThicknessPt(pt: thicknessPt as Float);
	}

	Function is setDivider(Color is color){
		:customDividerColor: color:toArgb();
	}

	Function is setButtonBorder(BoxBorderStyle is border){
		:customMetrics: true;
		if({ border:hasStyle }, { :setButtonBorderStyle(style: border:style); });
		if({ border:hasWidth }, { :setButtonBorderThicknessPt(pt: border:widthPt); });
		if({ border:hasColor }, { :customButtonBorderColor: border:lineColor:toArgb(); });
		if({ border:hasRadius }, { :setButtonCornerRadiusPt(pt: border:radiusPt); });
		if({ border:hasShadow }, {
			:setButtonShadowBlurPt(pt: border:shadow:blurPt);
			:setButtonShadowOffsetXPt(pt: border:shadow:offsetXPt);
			:setButtonShadowOffsetYPt(pt: border:shadow:offsetYPt);
		});
	}

	Function is setButtonBorder(LineStyle is line){
		:customMetrics: true;
		if({ line:hasStyle }, { :setButtonBorderStyle(style: line:style); });
		if({ line:hasWidth }, { :setButtonBorderThicknessPt(pt: line:widthPt); });
		if({ line:hasColor }, { :customButtonBorderColor: line:lineColor:toArgb(); });
	}

	Function is setButtonBorder(LineWidthStyle is width){
		if({ width:hasWidth }, { :setButtonBorderThicknessPt(pt: width:widthPt); });
	}

	Function is setButtonBorder(LineColorStyle is col){
		if({ col:hasColor }, { :customButtonBorderColor: col:lineColor:toArgb(); });
	}

	Function is setButtonBorder(Float is thicknessPt){
		:setButtonBorderThicknessPt(pt: thicknessPt);
	}

	Function is setButtonBorder(Int is thicknessPt){
		:setButtonBorderThicknessPt(pt: thicknessPt as Float);
	}

	Function is setButtonBorder(Color is color){
		:customButtonBorderColor: color:toArgb();
	}

	Function is setSurfaceFill(FillStyle is fill){
		:customSurfaceFill: true;
		:surfaceFill: fill;
	}

	Function is setButtonFill(FillStyle is fill){
		:customButtonFill: true;
		:buttonFill: fill;
	}

	Function is setHoverEffects(Float is brightness: 0.08, Float is tintShiftDeg: 0.0, Float is saturationShift: 0.0){
		:customMetrics: true;
		:hoverBrightness: brightness;
		:hoverTintShiftDeg: tintShiftDeg;
		:hoverSaturationShift: saturationShift;
		:deriveColors();
	}

	Function is setSelectedEffects(Float is brightness: 0.22, Float is tintShiftDeg: 0.0, Float is saturationShift: 0.0){
		:customMetrics: true;
		:selectedBrightness: brightness;
		:selectedTintShiftDeg: tintShiftDeg;
		:selectedSaturationShift: saturationShift;
		:deriveColors();
	}

	Function is setFocusEffects(Float is brightness: 0.14, Float is tintShiftDeg: 0.0, Float is saturationShift: 0.0){
		:customMetrics: true;
		:focusBrightness: brightness;
		:focusTintShiftDeg: tintShiftDeg;
		:focusSaturationShift: saturationShift;
		:deriveColors();
	}

	Function of FillStyle is resolveButtonFill(Boolean is enabled, Boolean is selected, Boolean is hovered, Boolean is focused: false){
		if({ !enabled }, {
			return FillStyle(mode: FillMode:SOLID, colorA: Color:fromArgb(argb: toolbarBg));
		});
		local FillStyle is baseFill: if({ customButtonFill }, { buttonFill }, {
			FillStyle(mode: FillMode:SOLID, colorA: Color:fromArgb(argb: menuBg))
		});
		if({ !selected && !hovered && !focused }, {
			return baseFill;
		});
		local Float is bri: baseFill:brightness;
		local Float is tint: baseFill:tintShiftDeg;
		local Float is sat: baseFill:saturationShift;
		if({ selected }, {
			bri: bri + selectedBrightness;
			tint: tint + selectedTintShiftDeg;
			sat: sat + selectedSaturationShift;
		});
		if({ focused }, {
			bri: bri + focusBrightness;
			tint: tint + focusTintShiftDeg;
			sat: sat + focusSaturationShift;
		});
		if({ hovered }, {
			bri: bri + hoverBrightness;
			tint: tint + hoverTintShiftDeg;
			sat: sat + hoverSaturationShift;
		});
		return FillStyle(
			mode: baseFill:mode,
			bounds: baseFill:bounds,
			colorA: baseFill:colorA,
			colorB: baseFill:colorB,
			centerX: baseFill:centerX,
			centerY: baseFill:centerY,
			angleDeg: baseFill:angleDeg,
			blendWidth: baseFill:blendWidth,
			reflected: baseFill:reflected,
			brightness: bri,
			tintShiftDeg: tint,
			saturationShift: sat
		);
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
			:surface: Color(r: 238, g: 238, b: 238, a: 255);
			:primary: Color(r: 28, g: 28, b: 28, a: 255);
			:secondary: Color(r: 96, g: 96, b: 96, a: 255);
			:accent: Color(r: 40, g: 40, b: 40, a: 255);
			:highlight: Color(r: 156, g: 156, b: 156, a: 255);
			:detail: Color(r: 201, g: 201, b: 201, a: 255);
			:positive: Color(r: 46, g: 125, b: 50, a: 255);
			:negative: Color(r: 198, g: 40, b: 40, a: 255);
			:neutral: Color(r: 115, g: 115, b: 115, a: 255);
		}, {
			:background: Color(r: 28, g: 28, b: 28, a: 255);
			:surface: Color(r: 41, g: 41, b: 41, a: 255);
			:primary: Color(r: 235, g: 235, b: 235, a: 255);
			:secondary: Color(r: 158, g: 158, b: 158, a: 255);
			:accent: Color(r: 189, g: 189, b: 189, a: 255);
			:highlight: Color(r: 103, g: 103, b: 103, a: 255);
			:detail: Color(r: 58, g: 58, b: 58, a: 255);
			:positive: Color(r: 76, g: 175, b: 80, a: 255);
			:negative: Color(r: 239, g: 83, b: 80, a: 255);
			:neutral: Color(r: 146, g: 152, b: 166, a: 255);
		});
		:customMetrics: false;
		:customPanelBorderColor: 0;
		:customDividerColor: 0;
		:customButtonBorderColor: 0;
		:customSurfaceFill: false;
		:customButtonFill: false;
		:hoverBrightness: if({ preset == ThemePreset:LIGHT }, { -0.08 }, { 0.12 });
		:hoverTintShiftDeg: 0.0;
		:hoverSaturationShift: 0.0;
		:selectedBrightness: if({ preset == ThemePreset:LIGHT }, { -0.16 }, { 0.22 });
		:selectedTintShiftDeg: 0.0;
		:selectedSaturationShift: 0.0;
		:focusBrightness: if({ preset == ThemePreset:LIGHT }, { -0.10 }, { 0.14 });
		:focusTintShiftDeg: 0.0;
		:focusSaturationShift: 0.0;
		:panelBorderStyle: 'single';
		:panelCornerRadiusPt: 0.0;
		:panelShadowBlurPt: 0.0;
		:panelShadowOffsetXPt: 0.0;
		:panelShadowOffsetYPt: 0.0;
		:panelInnerShadowBlurPt: 0.0;
		:panelInnerShadowOffsetXPt: 0.0;
		:panelInnerShadowOffsetYPt: 0.0;
		:dividerStyle: 'single';
		:buttonBorderStyle: 'single';
		:buttonCornerRadiusPt: 2.0;
		:buttonShadowBlurPt: 0.0;
		:buttonShadowOffsetXPt: 0.0;
		:buttonShadowOffsetYPt: 0.0;
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
		local Color is menuColor: Color:fromArgb(argb: menuBg);
		local FillStyle is hoverFx: FillStyle(brightness: hoverBrightness, tintShiftDeg: hoverTintShiftDeg, saturationShift: hoverSaturationShift);
		local FillStyle is selectedFx: FillStyle(brightness: selectedBrightness, tintShiftDeg: selectedTintShiftDeg, saturationShift: selectedSaturationShift);
		hoverBg: hoverFx:applyEffects(c: menuColor):toArgb();
		if({ !customSurfaceFill }, {
			:surfaceFill: FillStyle(mode: FillMode:SOLID, colorA: surface);
		});
		if({ !customButtonFill }, {
			:buttonFill: FillStyle(mode: FillMode:SOLID, colorA: menuColor);
		});
		activeBg: selectedFx:applyEffects(c: menuColor):toArgb();
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
		tabBarHeightPt: baseTextPt + basePaddingPt * 2.75;
		tabMinWidthPt: baseTextPt * 7.25;
		tabMaxWidthPt: baseTextPt * 16.0;
		barHeightPt: baseTextPt + basePaddingPt * 1.50;
		scrollbarWidthPt: basePaddingPt * 2.5;
		splitterSpacingPt: basePaddingPt;
		panelMinSizePt: baseTextPt * 3.25;
		iconSizePt: baseTextPt * 1.1;
		lineGapPt: basePaddingPt * 0.75;
		editorPadPt: paddingLargePt;
		local Float is baseBorder: 0.7 * (baseTextPt / 10.0);
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
		dividerThicknessPt: if({ borderStyle == 'none' }, { 0.0 }, { if({ borderStyle == 'bold' }, { 1.0 }, { 0.5 }) }) * (baseTextPt / 10.0);
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
		return background:mix(other: surface, t: k):toArgb();
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

	local Function of Map of String to Any is colorToMap(Color is c){
		local Map of String to Any is m: Map:init();
		m:set(key: 'r', value: JsonNumber(rawText: c:red() as String, isFloating: false));
		m:set(key: 'g', value: JsonNumber(rawText: c:green() as String, isFloating: false));
		m:set(key: 'b', value: JsonNumber(rawText: c:blue() as String, isFloating: false));
		m:set(key: 'a', value: JsonNumber(rawText: c:alpha() as String, isFloating: false));
		return m;
	}

	local Function of Color is colorFromMap(Json is j, Map of String to Any is obj, String is key, Color is fallback){
		if({ !obj:has(key: key) }, { return fallback; });
		local Any is raw: obj:get(key: key, default: '');
		if({ Introspection:typeIdentity(obj: raw) != 'Map' }, { return fallback; });
		local Map of String to Any is m: raw as Map;
		local Int is r: j:getInt(obj: m, key: 'r', default: fallback:red());
		local Int is g: j:getInt(obj: m, key: 'g', default: fallback:green());
		local Int is b: j:getInt(obj: m, key: 'b', default: fallback:blue());
		local Int is a: j:getInt(obj: m, key: 'a', default: fallback:alpha());
		return Color(r: r, g: g, b: b, a: a);
	}

	local Function of Map of String to Any is fillToMap(FillStyle is fs){
		local Map of String to Any is m: Map:init();
		local String is modeStr: Conditional:match(on: fs:mode, when: [
			FillMode:SOLID: { 'solid' },
			FillMode:LINEAR: { 'linear' },
			FillMode:RADIAL: { 'radial' }
		]);
		local String is boundsStr: Conditional:match(on: fs:bounds, when: [
			GradientBounds:INSCRIBE: { 'inscribe' },
			GradientBounds:CIRCUMSCRIBE: { 'circumscribe' }
		]);
		m:set(key: 'mode', value: modeStr);
		m:set(key: 'bounds', value: boundsStr);
		m:set(key: 'colorA', value: :colorToMap(c: fs:colorA));
		m:set(key: 'colorB', value: :colorToMap(c: fs:colorB));
		m:set(key: 'centerX', value: JsonNumber(rawText: fs:centerX as String, isFloating: true));
		m:set(key: 'centerY', value: JsonNumber(rawText: fs:centerY as String, isFloating: true));
		m:set(key: 'angleDeg', value: JsonNumber(rawText: fs:angleDeg as String, isFloating: true));
		m:set(key: 'blendWidth', value: JsonNumber(rawText: fs:blendWidth as String, isFloating: true));
		m:set(key: 'reflected', value: JsonBool(value: fs:reflected));
		m:set(key: 'brightness', value: JsonNumber(rawText: fs:brightness as String, isFloating: true));
		m:set(key: 'tintShiftDeg', value: JsonNumber(rawText: fs:tintShiftDeg as String, isFloating: true));
		m:set(key: 'saturationShift', value: JsonNumber(rawText: fs:saturationShift as String, isFloating: true));
		return m;
	}

	local Function of FillStyle is fillFromMap(Json is j, Map of String to Any is obj, String is key, FillStyle is fallback){
		if({ !obj:has(key: key) }, { return fallback; });
		local Any is raw: obj:get(key: key, default: '');
		if({ Introspection:typeIdentity(obj: raw) != 'Map' }, { return fallback; });
		local Map of String to Any is m: raw as Map;
		local String is modeStr: j:getString(obj: m, key: 'mode', default: 'solid');
		local FillMode is fm: if({ modeStr == 'linear' }, { FillMode:LINEAR }, {
			if({ modeStr == 'radial' }, { FillMode:RADIAL }, { FillMode:SOLID })
		});
		local String is boundsStr: j:getString(obj: m, key: 'bounds', default: 'inscribe');
		local GradientBounds is gb: if({ boundsStr == 'circumscribe' }, { GradientBounds:CIRCUMSCRIBE }, { GradientBounds:INSCRIBE });
		return FillStyle(
			mode: fm,
			bounds: gb,
			colorA: :colorFromMap(j: j, obj: m, key: 'colorA', fallback: fallback:colorA),
			colorB: :colorFromMap(j: j, obj: m, key: 'colorB', fallback: fallback:colorB),
			centerX: j:getFloat(obj: m, key: 'centerX', default: fallback:centerX),
			centerY: j:getFloat(obj: m, key: 'centerY', default: fallback:centerY),
			angleDeg: j:getFloat(obj: m, key: 'angleDeg', default: fallback:angleDeg),
			blendWidth: j:getFloat(obj: m, key: 'blendWidth', default: fallback:blendWidth),
			reflected: j:getBool(obj: m, key: 'reflected', default: fallback:reflected),
			brightness: j:getFloat(obj: m, key: 'brightness', default: fallback:brightness),
			tintShiftDeg: j:getFloat(obj: m, key: 'tintShiftDeg', default: fallback:tintShiftDeg),
			saturationShift: j:getFloat(obj: m, key: 'saturationShift', default: fallback:saturationShift)
		);
	}

	## Serializes this theme (colors, fills, state effects, borders, shadows, metrics) to a formatted JSON string.
	Function of String is toJson(){
		local Map of String to Any is obj: Map:init();
		obj:set(key: 'background', value: :colorToMap(c: background));
		obj:set(key: 'surface', value: :colorToMap(c: surface));
		obj:set(key: 'primary', value: :colorToMap(c: primary));
		obj:set(key: 'secondary', value: :colorToMap(c: secondary));
		obj:set(key: 'accent', value: :colorToMap(c: accent));
		obj:set(key: 'highlight', value: :colorToMap(c: highlight));
		obj:set(key: 'detail', value: :colorToMap(c: detail));
		obj:set(key: 'positive', value: :colorToMap(c: positive));
		obj:set(key: 'negative', value: :colorToMap(c: negative));
		obj:set(key: 'neutral', value: :colorToMap(c: neutral));

		obj:set(key: 'customSurfaceFill', value: JsonBool(value: customSurfaceFill));
		obj:set(key: 'customButtonFill', value: JsonBool(value: customButtonFill));
		obj:set(key: 'surfaceFill', value: :fillToMap(fs: surfaceFill));
		obj:set(key: 'buttonFill', value: :fillToMap(fs: buttonFill));

		obj:set(key: 'hoverBrightness', value: JsonNumber(rawText: hoverBrightness as String, isFloating: true));
		obj:set(key: 'hoverTintShiftDeg', value: JsonNumber(rawText: hoverTintShiftDeg as String, isFloating: true));
		obj:set(key: 'hoverSaturationShift', value: JsonNumber(rawText: hoverSaturationShift as String, isFloating: true));
		obj:set(key: 'selectedBrightness', value: JsonNumber(rawText: selectedBrightness as String, isFloating: true));
		obj:set(key: 'selectedTintShiftDeg', value: JsonNumber(rawText: selectedTintShiftDeg as String, isFloating: true));
		obj:set(key: 'selectedSaturationShift', value: JsonNumber(rawText: selectedSaturationShift as String, isFloating: true));
		obj:set(key: 'focusBrightness', value: JsonNumber(rawText: focusBrightness as String, isFloating: true));
		obj:set(key: 'focusTintShiftDeg', value: JsonNumber(rawText: focusTintShiftDeg as String, isFloating: true));
		obj:set(key: 'focusSaturationShift', value: JsonNumber(rawText: focusSaturationShift as String, isFloating: true));

		obj:set(key: 'customPanelBorderColor', value: JsonNumber(rawText: customPanelBorderColor as String, isFloating: false));
		obj:set(key: 'customDividerColor', value: JsonNumber(rawText: customDividerColor as String, isFloating: false));
		obj:set(key: 'customButtonBorderColor', value: JsonNumber(rawText: customButtonBorderColor as String, isFloating: false));
		obj:set(key: 'borderStyle', value: borderStyle);
		obj:set(key: 'panelBorderStyle', value: panelBorderStyle);
		obj:set(key: 'panelBorderThicknessPt', value: JsonNumber(rawText: panelBorderThicknessPt as String, isFloating: true));
		obj:set(key: 'panelCornerRadiusPt', value: JsonNumber(rawText: panelCornerRadiusPt as String, isFloating: true));
		obj:set(key: 'panelShadowBlurPt', value: JsonNumber(rawText: panelShadowBlurPt as String, isFloating: true));
		obj:set(key: 'panelShadowOffsetXPt', value: JsonNumber(rawText: panelShadowOffsetXPt as String, isFloating: true));
		obj:set(key: 'panelShadowOffsetYPt', value: JsonNumber(rawText: panelShadowOffsetYPt as String, isFloating: true));
		obj:set(key: 'panelInnerShadowBlurPt', value: JsonNumber(rawText: panelInnerShadowBlurPt as String, isFloating: true));
		obj:set(key: 'panelInnerShadowOffsetXPt', value: JsonNumber(rawText: panelInnerShadowOffsetXPt as String, isFloating: true));
		obj:set(key: 'panelInnerShadowOffsetYPt', value: JsonNumber(rawText: panelInnerShadowOffsetYPt as String, isFloating: true));
		obj:set(key: 'dividerStyle', value: dividerStyle);
		obj:set(key: 'dividerThicknessPt', value: JsonNumber(rawText: dividerThicknessPt as String, isFloating: true));
		obj:set(key: 'buttonBorderStyle', value: buttonBorderStyle);
		obj:set(key: 'buttonBorderThicknessPt', value: JsonNumber(rawText: buttonBorderThicknessPt as String, isFloating: true));
		obj:set(key: 'buttonCornerRadiusPt', value: JsonNumber(rawText: buttonCornerRadiusPt as String, isFloating: true));
		obj:set(key: 'buttonShadowBlurPt', value: JsonNumber(rawText: buttonShadowBlurPt as String, isFloating: true));
		obj:set(key: 'buttonShadowOffsetXPt', value: JsonNumber(rawText: buttonShadowOffsetXPt as String, isFloating: true));
		obj:set(key: 'buttonShadowOffsetYPt', value: JsonNumber(rawText: buttonShadowOffsetYPt as String, isFloating: true));
		obj:set(key: 'baseTextPt', value: JsonNumber(rawText: baseTextPt as String, isFloating: true));
		obj:set(key: 'uiScaleFactor', value: JsonNumber(rawText: uiScaleFactor as String, isFloating: true));
		obj:set(key: 'customMetrics', value: JsonBool(value: customMetrics));
		return Json():format(value: obj, indent: 2);
	}

	## Restores theme properties from a JSON string produced by [toJson], returning true on valid JSON object.
	Function of Boolean is fromJson(String is json){
		local Json is j: Json();
		local Map of String to Any is obj: Map:init();
		local Boolean is ok: false;
		Conditional:match(on: j:parseMapResult(text: json), when: [
			Result:Ok: local Function(Map of String to Any is m){
				obj: m;
				ok: true;
			}
		], default: {});
		if({ !ok }, { return false; });

		:background: :colorFromMap(j: j, obj: obj, key: 'background', fallback: background);
		:surface: :colorFromMap(j: j, obj: obj, key: 'surface', fallback: surface);
		:primary: :colorFromMap(j: j, obj: obj, key: 'primary', fallback: primary);
		:secondary: :colorFromMap(j: j, obj: obj, key: 'secondary', fallback: secondary);
		:accent: :colorFromMap(j: j, obj: obj, key: 'accent', fallback: accent);
		:highlight: :colorFromMap(j: j, obj: obj, key: 'highlight', fallback: highlight);
		:detail: :colorFromMap(j: j, obj: obj, key: 'detail', fallback: detail);
		:positive: :colorFromMap(j: j, obj: obj, key: 'positive', fallback: positive);
		:negative: :colorFromMap(j: j, obj: obj, key: 'negative', fallback: negative);
		:neutral: :colorFromMap(j: j, obj: obj, key: 'neutral', fallback: neutral);

		:customSurfaceFill: j:getBool(obj: obj, key: 'customSurfaceFill', default: customSurfaceFill);
		:customButtonFill: j:getBool(obj: obj, key: 'customButtonFill', default: customButtonFill);
		:surfaceFill: :fillFromMap(j: j, obj: obj, key: 'surfaceFill', fallback: surfaceFill);
		:buttonFill: :fillFromMap(j: j, obj: obj, key: 'buttonFill', fallback: buttonFill);

		:hoverBrightness: j:getFloat(obj: obj, key: 'hoverBrightness', default: hoverBrightness);
		:hoverTintShiftDeg: j:getFloat(obj: obj, key: 'hoverTintShiftDeg', default: hoverTintShiftDeg);
		:hoverSaturationShift: j:getFloat(obj: obj, key: 'hoverSaturationShift', default: hoverSaturationShift);
		:selectedBrightness: j:getFloat(obj: obj, key: 'selectedBrightness', default: selectedBrightness);
		:selectedTintShiftDeg: j:getFloat(obj: obj, key: 'selectedTintShiftDeg', default: selectedTintShiftDeg);
		:selectedSaturationShift: j:getFloat(obj: obj, key: 'selectedSaturationShift', default: selectedSaturationShift);
		:focusBrightness: j:getFloat(obj: obj, key: 'focusBrightness', default: focusBrightness);
		:focusTintShiftDeg: j:getFloat(obj: obj, key: 'focusTintShiftDeg', default: focusTintShiftDeg);
		:focusSaturationShift: j:getFloat(obj: obj, key: 'focusSaturationShift', default: focusSaturationShift);

		:customPanelBorderColor: j:getInt(obj: obj, key: 'customPanelBorderColor', default: customPanelBorderColor);
		:customDividerColor: j:getInt(obj: obj, key: 'customDividerColor', default: customDividerColor);
		:customButtonBorderColor: j:getInt(obj: obj, key: 'customButtonBorderColor', default: customButtonBorderColor);
		:borderStyle: j:getString(obj: obj, key: 'borderStyle', default: borderStyle);
		:panelBorderStyle: j:getString(obj: obj, key: 'panelBorderStyle', default: panelBorderStyle);
		:panelBorderThicknessPt: j:getFloat(obj: obj, key: 'panelBorderThicknessPt', default: panelBorderThicknessPt);
		:panelCornerRadiusPt: j:getFloat(obj: obj, key: 'panelCornerRadiusPt', default: panelCornerRadiusPt);
		:panelShadowBlurPt: j:getFloat(obj: obj, key: 'panelShadowBlurPt', default: panelShadowBlurPt);
		:panelShadowOffsetXPt: j:getFloat(obj: obj, key: 'panelShadowOffsetXPt', default: panelShadowOffsetXPt);
		:panelShadowOffsetYPt: j:getFloat(obj: obj, key: 'panelShadowOffsetYPt', default: panelShadowOffsetYPt);
		:panelInnerShadowBlurPt: j:getFloat(obj: obj, key: 'panelInnerShadowBlurPt', default: panelInnerShadowBlurPt);
		:panelInnerShadowOffsetXPt: j:getFloat(obj: obj, key: 'panelInnerShadowOffsetXPt', default: panelInnerShadowOffsetXPt);
		:panelInnerShadowOffsetYPt: j:getFloat(obj: obj, key: 'panelInnerShadowOffsetYPt', default: panelInnerShadowOffsetYPt);
		:dividerStyle: j:getString(obj: obj, key: 'dividerStyle', default: dividerStyle);
		:dividerThicknessPt: j:getFloat(obj: obj, key: 'dividerThicknessPt', default: dividerThicknessPt);
		:buttonBorderStyle: j:getString(obj: obj, key: 'buttonBorderStyle', default: buttonBorderStyle);
		:buttonBorderThicknessPt: j:getFloat(obj: obj, key: 'buttonBorderThicknessPt', default: buttonBorderThicknessPt);
		:buttonCornerRadiusPt: j:getFloat(obj: obj, key: 'buttonCornerRadiusPt', default: buttonCornerRadiusPt);
		:buttonShadowBlurPt: j:getFloat(obj: obj, key: 'buttonShadowBlurPt', default: buttonShadowBlurPt);
		:buttonShadowOffsetXPt: j:getFloat(obj: obj, key: 'buttonShadowOffsetXPt', default: buttonShadowOffsetXPt);
		:buttonShadowOffsetYPt: j:getFloat(obj: obj, key: 'buttonShadowOffsetYPt', default: buttonShadowOffsetYPt);
		:baseTextPt: j:getFloat(obj: obj, key: 'baseTextPt', default: baseTextPt);
		:uiScaleFactor: j:getFloat(obj: obj, key: 'uiScaleFactor', default: uiScaleFactor);
		:customMetrics: j:getBool(obj: obj, key: 'customMetrics', default: customMetrics);

		:deriveTokens();
		return true;
	}
}
