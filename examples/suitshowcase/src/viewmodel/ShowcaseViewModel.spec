#! Package suitshowcase:viewmodel
#! ViewModel managing navigation, live Theme Builder state, and interactive widget demos.

Class is ShowcaseViewModel{
	replace [String] is namespace: ['suitshowcase', 'viewmodel'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'signal', BoolEmitter],
		['base', 'signal', TextEmitter],
		['base', 'fabric', Color],
		['base', 'fabric', Theme],
		['base', 'fabric', ThemePreset],
		['base', 'fabric', FillMode],
		['base', 'fabric', GradientBounds],
		['base', 'fabric', FillStyle]
	];

	TextEmitter is selectedRoute: TextEmitter(initial: 'intro');
	TextEmitter is statusText: TextEmitter(initial: 'SuitShowcase ready — press Tab to navigate controls');
	ThemePreset is basePreset: ThemePreset:LIGHT;
	Theme is activeTheme: Theme:forPreset(preset: ThemePreset:LIGHT);
	Float is baseTextPt: 10.0;
	String is borderStyle: 'solid';
	Int is windowAlphaPct: 100;
	Int is surfFillStyleIdx: 0;
	GradientBounds is surfBounds: GradientBounds:INSCRIBE;
	Boolean is useSurfColorB: false;
	Color is surfColorB: Color(r: 90, g: 150, b: 235);
	Int is surfCenterXPct: 50;
	Int is surfCenterYPct: 50;
	Int is surfAngleDeg: 35;
	Int is surfBlendPct: 50;
	Int is btnFillStyleIdx: 0;
	GradientBounds is btnBounds: GradientBounds:INSCRIBE;
	Boolean is useBtnColorB: false;
	Color is btnColorB: Color(r: 90, g: 150, b: 235);
	Int is btnCenterXPct: 50;
	Int is btnCenterYPct: 50;
	Int is btnAngleDeg: 35;
	Int is btnBlendPct: 50;
	Int is hoverBriPct: 12;
	Int is hoverTintDeg: 0;
	Int is hoverSatPct: 0;

	## Interactive demo state
	Int is clickCount: 0;
	Int is stepperVal: 12;
	Int is segHIdx: 0;
	Int is segVIdx: 1;
	TextEmitter is sampleInputText: TextEmitter(initial: 'Editable text with cursor');
	BoolEmitter is switchA: BoolEmitter(initial: true);
	BoolEmitter is switchB: BoolEmitter(initial: false);
	BoolEmitter is demoWrap: BoolEmitter(initial: false);
	BoolEmitter is demoNums: BoolEmitter(initial: true);
	BoolEmitter is demoMono: BoolEmitter(initial: true);
	TextEmitter is demoCodeText: TextEmitter(initial: "Class is Hello {\n\t## Try word wrap, line numbers, or typing here\n\tFunction is greet(String is name) {\n\t\tlocal String is msg: \"Hello, \" . name . \"!\";\n\t\treturn msg;\n\t}\n}\n");

	Function is themeApplyHandler: local Function(Theme is _t){};
	Function is alphaApplyHandler: local Function(Int is _pct){};
	Array of Function is refreshListeners: Array();

	replace Function is init(){
		:activeTheme: Theme:forPreset(preset: ThemePreset:LIGHT, baseTextPt: 10.0);
		:basePreset: ThemePreset:LIGHT;
		:baseTextPt: 10.0;
		:borderStyle: 'solid';
	}

	Function is bindThemeApply(Function is onThemeApply){
		:themeApplyHandler: onThemeApply;
	}

	Function is bindAlphaApply(Function is onAlphaApply){
		:alphaApplyHandler: onAlphaApply;
	}

	Function is setWindowAlphaPct(Int is pct){
		local Int is clamped: pct;
		if({ clamped < 0 }, { clamped: 0; });
		if({ clamped > 100 }, { clamped: 100; });
		:windowAlphaPct: clamped;
		local Function is cb: alphaApplyHandler;
		cb(windowAlphaPct);
		statusText:emit(value: 'Window opacity: ' . (windowAlphaPct as String) . '%');
		:notifyRefresh();
	}

	Function is bindRefresh(Function is onRefresh){
		refreshListeners:add(item: onRefresh);
	}

	local Function is notifyRefresh(){
		local Int is i: 0;
		while({ i < refreshListeners:length() }, {
			local Function is cb: refreshListeners:get(index: i);
			cb();
			i: i + 1;
		});
	}

	local Function is notifyThemeChange(){
		local Function is cb: themeApplyHandler;
		cb(activeTheme);
		:notifyRefresh();
	}

	local Function is applyCurrentTheme(){
		activeTheme:setBorderStyle(style: borderStyle);
		activeTheme:setBaseTextPt(pt: baseTextPt);
		:notifyThemeChange();
	}

	Function is setPanelBorderStyle(String is style){
		activeTheme:setPanelBorderStyle(style: style);
		:notifyThemeChange();
		statusText:emit(value: 'Panel border style: ' . style);
	}

	Function is setDividerStyle(String is style){
		activeTheme:setDividerStyle(style: style);
		:notifyThemeChange();
		statusText:emit(value: 'Divider style: ' . style);
	}

	Function is setButtonBorderStyle(String is style){
		activeTheme:setButtonBorderStyle(style: style);
		:notifyThemeChange();
		statusText:emit(value: 'Button border style: ' . style);
	}

	Function of Int is toTenths(Float is pt){
		return ((pt * 10.0) + 0.5) as Int;
	}

	Function of String is tenthsLabel(Int is tenths){
		local Int is t: tenths;
		local String is sign: '';
		if({ t < 0 }, {
			sign: '-';
			t: 0 - t;
		});
		local Int is whole: t / 10;
		local Int is frac: t - (whole * 10);
		return sign . (whole as String) . '.' . (frac as String) . ' pt';
	}

	Function is setPanelBorderThickness(Int is tenths){
		activeTheme:setPanelBorderThicknessPt(pt: (tenths as Float) / 10.0);
		:notifyThemeChange();
	}

	Function is setPanelCornerRadius(Int is tenths){
		activeTheme:setPanelCornerRadiusPt(pt: (tenths as Float) / 10.0);
		:notifyThemeChange();
	}

	Function is setPanelShadowBlur(Int is tenths){
		activeTheme:setPanelShadowBlurPt(pt: (tenths as Float) / 10.0);
		:notifyThemeChange();
	}

	Function is setPanelShadowOffsetX(Int is tenths){
		activeTheme:setPanelShadowOffsetXPt(pt: (tenths as Float) / 10.0);
		:notifyThemeChange();
	}

	Function is setPanelShadowOffsetY(Int is tenths){
		activeTheme:setPanelShadowOffsetYPt(pt: (tenths as Float) / 10.0);
		:notifyThemeChange();
	}

	Function is setPanelInnerShadowBlur(Int is tenths){
		activeTheme:setPanelInnerShadowBlurPt(pt: (tenths as Float) / 10.0);
		:notifyThemeChange();
	}

	Function is setPanelInnerShadowOffsetX(Int is tenths){
		activeTheme:setPanelInnerShadowOffsetXPt(pt: (tenths as Float) / 10.0);
		:notifyThemeChange();
	}

	Function is setPanelInnerShadowOffsetY(Int is tenths){
		activeTheme:setPanelInnerShadowOffsetYPt(pt: (tenths as Float) / 10.0);
		:notifyThemeChange();
	}

	Function is setDividerThickness(Int is tenths){
		activeTheme:setDividerThicknessPt(pt: (tenths as Float) / 10.0);
		:notifyThemeChange();
	}

	Function is setButtonBorderThickness(Int is tenths){
		activeTheme:setButtonBorderThicknessPt(pt: (tenths as Float) / 10.0);
		:notifyThemeChange();
	}

	Function is setButtonCornerRadius(Int is tenths){
		activeTheme:setButtonCornerRadiusPt(pt: (tenths as Float) / 10.0);
		:notifyThemeChange();
	}

	Function is setButtonShadowBlur(Int is tenths){
		activeTheme:setButtonShadowBlurPt(pt: (tenths as Float) / 10.0);
		:notifyThemeChange();
	}

	Function is setButtonShadowOffsetX(Int is tenths){
		activeTheme:setButtonShadowOffsetXPt(pt: (tenths as Float) / 10.0);
		:notifyThemeChange();
	}

	Function is setButtonShadowOffsetY(Int is tenths){
		activeTheme:setButtonShadowOffsetYPt(pt: (tenths as Float) / 10.0);
		:notifyThemeChange();
	}

	Function is selectRoute(String is routeName){
		selectedRoute:emit(value: routeName);
		statusText:emit(value: 'Section: ' . routeName);
		:notifyRefresh();
	}

	Function is loadPreset(ThemePreset is preset){
		:basePreset: preset;
		:activeTheme: Theme:forPreset(preset: preset, baseTextPt: baseTextPt);
		:surfFillStyleIdx: 0;
		:useSurfColorB: false;
		:btnFillStyleIdx: 0;
		:useBtnColorB: false;
		:hoverBriPct: if({ preset == ThemePreset:LIGHT }, { -8 }, { 12 });
		:hoverTintDeg: 0;
		:hoverSatPct: 0;
		:applyCurrentTheme();
		statusText:emit(value: 'Loaded ' . Theme:presetLabel(preset: preset) . ' preset');
	}

	local Function is syncSurfaceFill(){
		if({ surfFillStyleIdx == 0 }, {
			activeTheme:customSurfaceFill: false;
			activeTheme:deriveColors();
			:notifyThemeChange();
			return;
		});
		local FillMode is fMode: if({ surfFillStyleIdx == 3 || surfFillStyleIdx == 4 }, { FillMode:RADIAL }, { FillMode:LINEAR });
		local Boolean is fRefl: surfFillStyleIdx == 2 || surfFillStyleIdx == 4;
		local Color is colB: if({ useSurfColorB }, { surfColorB }, { activeTheme:highlight });
		activeTheme:setSurfaceFill(fill: FillStyle(
			mode: fMode, bounds: surfBounds, colorA: activeTheme:background, colorB: colB,
			centerX: (surfCenterXPct as Float) / 100.0,
			centerY: (surfCenterYPct as Float) / 100.0,
			angleDeg: surfAngleDeg as Float,
			blendWidth: (surfBlendPct as Float) / 100.0,
			reflected: fRefl
		));
		:notifyThemeChange();
	}

	local Function is syncButtonFill(){
		if({ btnFillStyleIdx == 0 }, {
			activeTheme:customButtonFill: false;
			activeTheme:deriveColors();
			:notifyThemeChange();
			return;
		});
		local FillMode is fMode: if({ btnFillStyleIdx == 3 || btnFillStyleIdx == 4 }, { FillMode:RADIAL }, { FillMode:LINEAR });
		local Boolean is fRefl: btnFillStyleIdx == 2 || btnFillStyleIdx == 4;
		local Color is btnA: Color:fromArgb(argb: activeTheme:menuBg);
		local Color is colB: if({ useBtnColorB }, { btnColorB }, { activeTheme:highlight });
		activeTheme:setButtonFill(fill: FillStyle(
			mode: fMode, bounds: btnBounds, colorA: btnA, colorB: colB,
			centerX: (btnCenterXPct as Float) / 100.0,
			centerY: (btnCenterYPct as Float) / 100.0,
			angleDeg: btnAngleDeg as Float,
			blendWidth: (btnBlendPct as Float) / 100.0,
			reflected: fRefl
		));
		:notifyThemeChange();
	}

	Function is setSurfFillStyleIndex(Int is idx){ :surfFillStyleIdx: idx; :syncSurfaceFill(); }
	Function is setSurfBounds(GradientBounds is bounds){ :surfBounds: bounds; :syncSurfaceFill(); }
	Function is setUseSurfColorB(Boolean is enabled){ :useSurfColorB: enabled; :syncSurfaceFill(); }
	Function is setSurfColorB(Color is col){ :surfColorB: col; :useSurfColorB: true; :syncSurfaceFill(); }
	Function is setSurfCenterX(Int is pct){ :surfCenterXPct: pct; :syncSurfaceFill(); }
	Function is setSurfCenterY(Int is pct){ :surfCenterYPct: pct; :syncSurfaceFill(); }
	Function is setSurfAngle(Int is deg){ :surfAngleDeg: deg; :syncSurfaceFill(); }
	Function is setSurfBlend(Int is pct){ :surfBlendPct: pct; :syncSurfaceFill(); }

	Function is setBtnFillStyleIndex(Int is idx){ :btnFillStyleIdx: idx; :syncButtonFill(); }
	Function is setBtnBounds(GradientBounds is bounds){ :btnBounds: bounds; :syncButtonFill(); }
	Function is setUseBtnColorB(Boolean is enabled){ :useBtnColorB: enabled; :syncButtonFill(); }
	Function is setBtnColorB(Color is col){ :btnColorB: col; :useBtnColorB: true; :syncButtonFill(); }
	Function is setBtnCenterX(Int is pct){ :btnCenterXPct: pct; :syncButtonFill(); }
	Function is setBtnCenterY(Int is pct){ :btnCenterYPct: pct; :syncButtonFill(); }
	Function is setBtnAngle(Int is deg){ :btnAngleDeg: deg; :syncButtonFill(); }
	Function is setBtnBlend(Int is pct){ :btnBlendPct: pct; :syncButtonFill(); }

	local Function is syncHoverEffects(){
		activeTheme:setHoverEffects(
			brightness: (hoverBriPct as Float) / 100.0,
			tintShiftDeg: hoverTintDeg as Float,
			saturationShift: (hoverSatPct as Float) / 100.0
		);
		:notifyThemeChange();
	}

	Function is setHoverBrightness(Int is pct){ :hoverBriPct: pct; :syncHoverEffects(); }
	Function is setHoverTint(Int is deg){ :hoverTintDeg: deg; :syncHoverEffects(); }
	Function is setHoverSaturation(Int is pct){ :hoverSatPct: pct; :syncHoverEffects(); }

	Function is setBorderStyle(String is style){
		:borderStyle: style;
		:applyCurrentTheme();
		statusText:emit(value: 'Border style: ' . style);
	}

	Function is adjustBaseTextPt(Float is delta){
		local Float is next: baseTextPt + delta;
		if({ next < 8.0 }, { next: 8.0; });
		if({ next > 20.0 }, { next: 20.0; });
		:baseTextPt: next;
		:applyCurrentTheme();
		statusText:emit(value: 'Base text size: ' . :baseTextLabel());
	}

	Function is setBaseTextPtFromText(String is raw){
		local Int is parsed: raw:trim():parseInt(base: 10, default: (baseTextPt as Int));
		local Float is next: parsed as Float;
		if({ next < 8.0 }, { next: 8.0; });
		if({ next > 20.0 }, { next: 20.0; });
		:baseTextPt: next;
		:applyCurrentTheme();
		statusText:emit(value: 'Base text size: ' . :baseTextLabel());
	}

	Function of String is baseTextLabel(){
		return ((baseTextPt as Int) as String) . ' pt';
	}

	local Function of String is byteToHex(Int is v){
		local String is digits: '0123456789ABCDEF';
		local Int is hi: (v >> 4) & 15;
		local Int is lo: v & 15;
		return digits:substring(start: hi, end: hi + 1) . digits:substring(start: lo, end: lo + 1);
	}

	Function of String is colorToHex(Color is c){
		return '#' . :byteToHex(v: c:red()) . :byteToHex(v: c:green()) . :byteToHex(v: c:blue());
	}

	local Function of Int is hexDigit(Int is b){
		if({ b >= 48 && b <= 57 }, { return b - 48; });
		if({ b >= 65 && b <= 70 }, { return 10 + (b - 65); });
		if({ b >= 97 && b <= 102 }, { return 10 + (b - 97); });
		return -1;
	}

	local Function of Int is parseHexByte(String is s, Int is off){
		local Int is h1: :hexDigit(b: s:byteAt(index: off));
		local Int is h2: :hexDigit(b: s:byteAt(index: off + 1));
		if({ h1 < 0 || h2 < 0 }, { return -1; });
		return (h1 << 4) | h2;
	}

	Function of Color is colorAtSlot(Int is slot){
		if({ slot == 0 }, { return activeTheme:background; });
		if({ slot == 1 }, { return activeTheme:surface; });
		if({ slot == 2 }, { return activeTheme:primary; });
		if({ slot == 3 }, { return activeTheme:secondary; });
		if({ slot == 4 }, { return activeTheme:accent; });
		if({ slot == 5 }, { return activeTheme:highlight; });
		if({ slot == 6 }, { return activeTheme:detail; });
		if({ slot == 7 }, { return activeTheme:positive; });
		if({ slot == 8 }, { return activeTheme:negative; });
		return activeTheme:neutral;
	}

	Function is setColorSlot(Int is slot, Color is nextCol){
		if({ slot == 0 }, { activeTheme:background: nextCol; });
		if({ slot == 1 }, { activeTheme:surface: nextCol; });
		if({ slot == 2 }, { activeTheme:primary: nextCol; });
		if({ slot == 3 }, { activeTheme:secondary: nextCol; });
		if({ slot == 4 }, { activeTheme:accent: nextCol; });
		if({ slot == 5 }, { activeTheme:highlight: nextCol; });
		if({ slot == 6 }, { activeTheme:detail: nextCol; });
		if({ slot == 7 }, { activeTheme:positive: nextCol; });
		if({ slot == 8 }, { activeTheme:negative: nextCol; });
		if({ slot == 9 }, { activeTheme:neutral: nextCol; });
		:applyCurrentTheme();
		statusText:emit(value: 'Updated theme color ' . nextCol:toHex());
	}

	Function of Float is metricAtSlot(Int is slot){
		if({ slot == 0 }, { return activeTheme:basePaddingPt; });
		if({ slot == 1 }, { return activeTheme:sectionPaddingPt; });
		if({ slot == 2 }, { return activeTheme:dialogPaddingPt; });
		if({ slot == 3 }, { return activeTheme:splitterSpacingPt; });
		if({ slot == 4 }, { return activeTheme:lineGapPt; });
		return activeTheme:editorPadPt;
	}

	Function of String is metricLabel(Int is slot){
		local Float is v: :metricAtSlot(slot: slot);
		local Int is tenths: ((v * 10.0) + 0.5) as Int;
		local Int is whole: tenths / 10;
		local Int is frac: tenths - (whole * 10);
		return (whole as String) . '.' . (frac as String) . ' pt';
	}

	Function is setMetricSlot(Int is slot, Float is val){
		if({ slot == 0 }, { activeTheme:setBasePaddingPt(pt: val); });
		if({ slot == 1 }, { activeTheme:setSectionPaddingPt(pt: val); });
		if({ slot == 2 }, { activeTheme:setDialogPaddingPt(pt: val); });
		if({ slot == 3 }, { activeTheme:setSplitterSpacingPt(pt: val); });
		if({ slot == 4 }, { activeTheme:setLineGapPt(pt: val); });
		if({ slot == 5 }, { activeTheme:setEditorPadPt(pt: val); });
		:applyCurrentTheme();
		statusText:emit(value: 'Updated theme spacing: ' . :metricLabel(slot: slot));
	}

	Function is adjustMetricSlot(Int is slot, Float is delta){
		local Float is next: :metricAtSlot(slot: slot) + delta;
		:setMetricSlot(slot: slot, val: next);
	}

	Function is setMetricSlotFromText(Int is slot, String is raw){
		local Float is cur: :metricAtSlot(slot: slot);
		local Int is parsed: raw:trim():parseInt(base: 10, default: ((cur + 0.5) as Int));
		:setMetricSlot(slot: slot, val: parsed as Float);
	}

	Function is setColorSlotFromHex(Int is slot, String is raw){
		local Color is cur: :colorAtSlot(slot: slot);
		local Color is nextCol: Color:fromHex(hex: raw, fallback: cur);
		if({ nextCol:toArgb() == cur:toArgb() }, {
			:notifyRefresh();
			return;
		});
		:setColorSlot(slot: slot, nextCol: nextCol);
	}

	Function is incrementClicks(){
		:clickCount: clickCount + 1;
		statusText:emit(value: 'Button clicked ' . (clickCount as String) . ' time(s)');
		:notifyRefresh();
	}

	Function is adjustStepper(Int is delta){
		:stepperVal: stepperVal + delta;
		statusText:emit(value: 'Stepper value: ' . (stepperVal as String));
		:notifyRefresh();
	}

	Function is setStepperFromText(String is raw){
		:stepperVal: raw:trim():parseInt(base: 10, default: stepperVal);
		statusText:emit(value: 'Stepper value: ' . (stepperVal as String));
		:notifyRefresh();
	}
}
