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
		['base', 'fabric', ThemePreset]
	];

	TextEmitter is selectedRoute: TextEmitter(initial: 'intro');
	TextEmitter is statusText: TextEmitter(initial: 'SuitShowcase ready — press Tab to navigate controls');
	ThemePreset is basePreset: ThemePreset:LIGHT;
	Theme is activeTheme: Theme:forPreset(preset: ThemePreset:LIGHT);
	Float is baseTextPt: 10.0;
	String is borderStyle: 'solid';
	Int is windowAlphaPct: 100;

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
	TextEmitter is demoCodeText: TextEmitter(initial: 'Class is Hello {\n\t## Try word wrap, line numbers, or typing here\n\tFunction is greet(String is name) {\n\t\tlocal String is msg: "Hello, " . name . "!";\n\t\treturn msg;\n\t}\n}\n');

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

	local Function is applyCurrentTheme(){
		activeTheme:setBorderStyle(style: borderStyle);
		activeTheme:setBaseTextPt(pt: baseTextPt);
		local Function is cb: themeApplyHandler;
		cb(activeTheme);
		:notifyRefresh();
	}

	Function is selectRoute(String is routeName){
		selectedRoute:emit(value: routeName);
		statusText:emit(value: 'Section: ' . routeName);
		:notifyRefresh();
	}

	Function is loadPreset(ThemePreset is preset){
		:basePreset: preset;
		:activeTheme: Theme:forPreset(preset: preset, baseTextPt: baseTextPt);
		:applyCurrentTheme();
		statusText:emit(value: 'Loaded ' . Theme:presetLabel(preset: preset) . ' preset');
	}

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
		if({ slot == 0 }, { return activeTheme:primary; });
		if({ slot == 1 }, { return activeTheme:secondary; });
		if({ slot == 2 }, { return activeTheme:accent; });
		if({ slot == 3 }, { return activeTheme:highlight; });
		if({ slot == 4 }, { return activeTheme:detail; });
		if({ slot == 5 }, { return activeTheme:positive; });
		if({ slot == 6 }, { return activeTheme:negative; });
		return activeTheme:neutral;
	}

	Function is setColorSlotFromHex(Int is slot, String is raw){
		local String is t: raw:trim();
		if({ t:length() > 0 && t:byteAt(index: 0) == 35 }, {
			t: t:substring(start: 1, end: t:length());
		});
		if({ t:length() != 6 }, {
			:notifyRefresh();
			return;
		});
		local Int is r: :parseHexByte(s: t, off: 0);
		local Int is g: :parseHexByte(s: t, off: 2);
		local Int is b: :parseHexByte(s: t, off: 4);
		if({ r < 0 || g < 0 || b < 0 }, {
			:notifyRefresh();
			return;
		});
		local Color is nextCol: Color(r: r, g: g, b: b);
		if({ slot == 0 }, { activeTheme:primary: nextCol; });
		if({ slot == 1 }, { activeTheme:secondary: nextCol; });
		if({ slot == 2 }, { activeTheme:accent: nextCol; });
		if({ slot == 3 }, { activeTheme:highlight: nextCol; });
		if({ slot == 4 }, { activeTheme:detail: nextCol; });
		if({ slot == 5 }, { activeTheme:positive: nextCol; });
		if({ slot == 6 }, { activeTheme:negative: nextCol; });
		if({ slot == 7 }, { activeTheme:neutral: nextCol; });
		:applyCurrentTheme();
		statusText:emit(value: 'Updated theme color #' . t);
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
