#! Package suitshowcase:view
#! Live Theme Builder page allowing preset loading and form overrides of base colors, text size, and border style.

Class is ThemeBuilderPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'signal', BoolEmitter],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'sew', Row],
		['base', 'sew', Column],
		['base', 'sew', Grid],
		['base', 'sew', 'nav', NavStack],
		['base', 'sew', 'nav', NavRoute],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', Badge],
		['base', 'scrap', Checkbox],
		['base', 'scrap', RadioButton],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', Slider],
		['base', 'scrap', Switch],
		['base', 'scrap', ProgressBar],
		['base', 'scrap', NumberInput],
		['base', 'scrap', SelectDropdown],
		['base', 'scrap', Popover],
		['base', 'scrap', ScrollView],
		['base', 'scrap', ColorSwatchDropdown],
		['base', 'scrap', TextInput],
		['base', 'scrap', DecoratedTextInput],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['base', 'scrap', 'tab', TabBar],
		['base', 'scrap', 'tab', TabItemConfig],
		['base', 'scrap', 'text', CodeEditorView],
		['base', 'scrap', 'text', TextScrap],
		['base', 'fabric', Color],
		['base', 'fabric', TextStyle],
		['base', 'fabric', Theme],
		['base', 'fabric', ThemePreset],
		['base', 'fabric', StrokeStyle],
		['base', 'fabric', GradientBounds],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();
	TextEmitter is activeTabRoute: TextEmitter(initial: 'layout');
	TabBar is optionTabs: TabBar();
	SectionH is presetSection: SectionH();
	SectionH is borderSection: SectionH();
	TextEmitter is themeJsonText: TextEmitter(initial: '');
	SelectDropdown is panelStyleDropdown: SelectDropdown();
	SelectDropdown is dividerStyleDropdown: SelectDropdown();
	SelectDropdown is buttonStyleDropdown: SelectDropdown();
	SelectDropdown is surfFillDropdown: SelectDropdown();
	SelectDropdown is surfBoundsDropdown: SelectDropdown();
	ColorSwatchDropdown is surfColorASwatch: ColorSwatchDropdown();
	Switch is useSurfColorBSwitch: Switch();
	ColorSwatchDropdown is surfColorBSwatch: ColorSwatchDropdown();
	Slider is surfCXSlider: Slider();
	Slider is surfCYSlider: Slider();
	Slider is surfAngSlider: Slider();
	Slider is surfBwSlider: Slider();
	TextEmitter is surfCXLabel: TextEmitter(initial: '50%');
	TextEmitter is surfCYLabel: TextEmitter(initial: '50%');
	TextEmitter is surfAngLabel: TextEmitter(initial: '35 deg');
	TextEmitter is surfBwLabel: TextEmitter(initial: '50%');
	SelectDropdown is btnFillDropdown: SelectDropdown();
	SelectDropdown is btnBoundsDropdown: SelectDropdown();
	ColorSwatchDropdown is btnColorASwatch: ColorSwatchDropdown();
	Switch is useBtnColorBSwitch: Switch();
	ColorSwatchDropdown is btnColorBSwatch: ColorSwatchDropdown();
	Slider is btnCXSlider: Slider();
	Slider is btnCYSlider: Slider();
	Slider is btnAngSlider: Slider();
	Slider is btnBwSlider: Slider();
	TextEmitter is btnCXLabel: TextEmitter(initial: '50%');
	TextEmitter is btnCYLabel: TextEmitter(initial: '50%');
	TextEmitter is btnAngLabel: TextEmitter(initial: '35 deg');
	TextEmitter is btnBwLabel: TextEmitter(initial: '50%');
	Slider is hoverBriSlider: Slider();
	Slider is hoverTintSlider: Slider();
	Slider is hoverSatSlider: Slider();
	TextEmitter is hoverBriLabel: TextEmitter(initial: '12%');
	TextEmitter is hoverTintLabel: TextEmitter(initial: '0 deg');
	TextEmitter is hoverSatLabel: TextEmitter(initial: '0%');
	Slider is selectedBriSlider: Slider();
	Slider is selectedTintSlider: Slider();
	Slider is selectedSatSlider: Slider();
	TextEmitter is selectedBriLabel: TextEmitter(initial: '22%');
	TextEmitter is selectedTintLabel: TextEmitter(initial: '0 deg');
	TextEmitter is selectedSatLabel: TextEmitter(initial: '0%');
	Slider is focusBriSlider: Slider();
	Slider is focusTintSlider: Slider();
	Slider is focusSatSlider: Slider();
	TextEmitter is focusBriLabel: TextEmitter(initial: '14%');
	TextEmitter is focusTintLabel: TextEmitter(initial: '0 deg');
	TextEmitter is focusSatLabel: TextEmitter(initial: '0%');
	Slider is panelThickSlider: Slider();
	Slider is panelRadiusSlider: Slider();
	Slider is panelShadowSlider: Slider();
	Slider is panelShadowXSlider: Slider();
	Slider is panelShadowYSlider: Slider();
	Slider is panelInnerShadowSlider: Slider();
	Slider is panelInnerShadowXSlider: Slider();
	Slider is panelInnerShadowYSlider: Slider();
	Slider is dividerThickSlider: Slider();
	Slider is buttonThickSlider: Slider();
	Slider is buttonRadiusSlider: Slider();
	Slider is buttonShadowSlider: Slider();
	Slider is buttonShadowXSlider: Slider();
	Slider is buttonShadowYSlider: Slider();
	TextEmitter is panelThickLabel: TextEmitter(initial: '1.0 pt');
	TextEmitter is panelRadiusLabel: TextEmitter(initial: '0.0 pt');
	TextEmitter is panelShadowLabel: TextEmitter(initial: '0.0 pt');
	TextEmitter is panelShadowXLabel: TextEmitter(initial: '0.0 pt');
	TextEmitter is panelShadowYLabel: TextEmitter(initial: '0.0 pt');
	TextEmitter is panelInnerShadowLabel: TextEmitter(initial: '0.0 pt');
	TextEmitter is panelInnerShadowXLabel: TextEmitter(initial: '0.0 pt');
	TextEmitter is panelInnerShadowYLabel: TextEmitter(initial: '0.0 pt');
	TextEmitter is dividerThickLabel: TextEmitter(initial: '1.0 pt');
	TextEmitter is buttonThickLabel: TextEmitter(initial: '1.0 pt');
	TextEmitter is buttonRadiusLabel: TextEmitter(initial: '0.0 pt');
	TextEmitter is buttonShadowLabel: TextEmitter(initial: '0.0 pt');
	TextEmitter is buttonShadowXLabel: TextEmitter(initial: '0.0 pt');
	TextEmitter is buttonShadowYLabel: TextEmitter(initial: '0.0 pt');
	Slider is alphaSlider: Slider();
	TextEmitter is alphaLabel: TextEmitter(initial: '100%');
	DecoratedTextInput is baseTextInput: DecoratedTextInput();
	Array of TextInput is colorInputs: Array();
	Array of ColorSwatchDropdown is colorSwatches: Array();
	Array of DecoratedTextInput is metricInputs: Array();
	Array of String is colorLabels: Array([
		'Background', 'Surface', 'Primary', 'Secondary', 'Accent',
		'Highlight', 'Detail', 'Positive', 'Negative', 'Neutral'
	]);
	Array of String is metricLabels: Array([
		'Base Padding', 'Section Padding', 'Dialog Padding',
		'Splitter Spacing', 'Line Gap', 'Editor Padding'
	]);
	Array of String is borderStyles: Array(['none', 'solid', 'bold']);
	Array of StrokeStyle is targetBorderStyles: Array([StrokeStyle:NONE, StrokeStyle:SINGLE, StrokeStyle:DOUBLE, StrokeStyle:BEVEL, StrokeStyle:GROOVE, StrokeStyle:INSET, StrokeStyle:OUTSET]);
	Array of String is targetBorderLabels: Array(['None', 'Single', 'Double', 'Bevel', 'Groove', 'Inset', 'Outset']);
	Array of String is fillStyleLabels: Array(['Solid', 'Linear', 'Lin Refl', 'Radial', 'Rad Refl']);
	Array of String is boundsLabels: Array(['Inscribe', 'Circumscribe']);

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
		:colorInputs: Array();
	}

	local Function of Int is presetIndex(ThemePreset is p){
		return if({ p == ThemePreset:DARK }, { 1 }, { 0 });
	}

	local Function of Int is borderIndex(String is style){
		local Int is i: 0;
		while({ i < borderStyles:length() }, {
			if({ borderStyles:get(index: i) == style }, { return i; });
			i: i + 1;
		});
		return 1;
	}

	local Function of Int is targetStyleIndex(StrokeStyle is style){
		local Int is i: 0;
		while({ i < targetBorderStyles:length() }, {
			if({ targetBorderStyles:get(index: i) == style }, { return i; });
			i: i + 1;
		});
		return 1;
	}

	Function of SewNode is build(){
		:colorInputs: Array();
		:colorSwatches: Array();
		:metricInputs: Array();

		:presetSection: SectionH(
			segmented: true,
			options: Array(['Light', 'Dark']),
			selectedIndex: :presetIndex(p: vm:basePreset),
			itemMinWidthPt: 64.0,
			onSelect: local Function(Int is idx){
				vm:loadPreset(preset: if({ idx == 1 }, { ThemePreset:DARK }, { ThemePreset:LIGHT }));
			}
		);

		:borderSection: SectionH(
			segmented: true,
			options: borderStyles,
			selectedIndex: :borderIndex(style: vm:borderStyle),
			itemMinWidthPt: 56.0,
			onSelect: local Function(Int is idx){
				if({ idx >= 0 && idx < borderStyles:length() }, {
					vm:setBorderStyle(style: borderStyles:get(index: idx));
				});
			}
		);

		:panelStyleDropdown: SelectDropdown(
			options: targetBorderLabels,
			selectedIndex: :targetStyleIndex(style: vm:activeTheme:panelBorderStyle),
			minWidthPt: 110.0,
			onSelect: local Function(Int is idx, String is _val){
				if({ idx >= 0 && idx < targetBorderStyles:length() }, {
					vm:setPanelBorderStyle(style: targetBorderStyles:get(index: idx));
				});
			}
		);

		:dividerStyleDropdown: SelectDropdown(
			options: targetBorderLabels,
			selectedIndex: :targetStyleIndex(style: vm:activeTheme:dividerStyle),
			minWidthPt: 110.0,
			onSelect: local Function(Int is idx, String is _val){
				if({ idx >= 0 && idx < targetBorderStyles:length() }, {
					vm:setDividerStyle(style: targetBorderStyles:get(index: idx));
				});
			}
		);

		:buttonStyleDropdown: SelectDropdown(
			options: targetBorderLabels,
			selectedIndex: :targetStyleIndex(style: vm:activeTheme:buttonBorderStyle),
			minWidthPt: 110.0,
			onSelect: local Function(Int is idx, String is _val){
				if({ idx >= 0 && idx < targetBorderStyles:length() }, {
					vm:setButtonBorderStyle(style: targetBorderStyles:get(index: idx));
				});
			}
		);

		:panelThickSlider: Slider(minVal: 0, maxVal: 80, value: vm:toTenths(pt: vm:activeTheme:panelBorderThicknessPt), minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setPanelBorderThickness(tenths: v); });
		:panelRadiusSlider: Slider(minVal: 0, maxVal: 160, value: vm:toTenths(pt: vm:activeTheme:panelCornerRadiusPt), minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setPanelCornerRadius(tenths: v); });
		:panelShadowSlider: Slider(minVal: 0, maxVal: 160, value: vm:toTenths(pt: vm:activeTheme:panelShadowBlurPt), minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setPanelShadowBlur(tenths: v); });
		:panelShadowXSlider: Slider(minVal: -120, maxVal: 120, value: vm:toTenths(pt: vm:activeTheme:panelShadowOffsetXPt), minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setPanelShadowOffsetX(tenths: v); });
		:panelShadowYSlider: Slider(minVal: -120, maxVal: 120, value: vm:toTenths(pt: vm:activeTheme:panelShadowOffsetYPt), minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setPanelShadowOffsetY(tenths: v); });
		:panelInnerShadowSlider: Slider(minVal: 0, maxVal: 160, value: vm:toTenths(pt: vm:activeTheme:panelInnerShadowBlurPt), minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setPanelInnerShadowBlur(tenths: v); });
		:panelInnerShadowXSlider: Slider(minVal: -120, maxVal: 120, value: vm:toTenths(pt: vm:activeTheme:panelInnerShadowOffsetXPt), minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setPanelInnerShadowOffsetX(tenths: v); });
		:panelInnerShadowYSlider: Slider(minVal: -120, maxVal: 120, value: vm:toTenths(pt: vm:activeTheme:panelInnerShadowOffsetYPt), minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setPanelInnerShadowOffsetY(tenths: v); });
		:dividerThickSlider: Slider(minVal: 0, maxVal: 80, value: vm:toTenths(pt: vm:activeTheme:dividerThicknessPt), minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setDividerThickness(tenths: v); });
		:buttonThickSlider: Slider(minVal: 0, maxVal: 80, value: vm:toTenths(pt: vm:activeTheme:buttonBorderThicknessPt), minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setButtonBorderThickness(tenths: v); });
		:buttonRadiusSlider: Slider(minVal: 0, maxVal: 140, value: vm:toTenths(pt: vm:activeTheme:buttonCornerRadiusPt), minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setButtonCornerRadius(tenths: v); });
		:buttonShadowSlider: Slider(minVal: 0, maxVal: 140, value: vm:toTenths(pt: vm:activeTheme:buttonShadowBlurPt), minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setButtonShadowBlur(tenths: v); });
		:buttonShadowXSlider: Slider(minVal: -120, maxVal: 120, value: vm:toTenths(pt: vm:activeTheme:buttonShadowOffsetXPt), minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setButtonShadowOffsetX(tenths: v); });
		:buttonShadowYSlider: Slider(minVal: -120, maxVal: 120, value: vm:toTenths(pt: vm:activeTheme:buttonShadowOffsetYPt), minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setButtonShadowOffsetY(tenths: v); });
		panelThickLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelBorderThicknessPt)));
		panelRadiusLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelCornerRadiusPt)));
		panelShadowLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelShadowBlurPt)));
		panelShadowXLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelShadowOffsetXPt)));
		panelShadowYLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelShadowOffsetYPt)));
		panelInnerShadowLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelInnerShadowBlurPt)));
		panelInnerShadowXLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelInnerShadowOffsetXPt)));
		panelInnerShadowYLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelInnerShadowOffsetYPt)));
		dividerThickLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:dividerThicknessPt)));
		buttonThickLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:buttonBorderThicknessPt)));
		buttonRadiusLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:buttonCornerRadiusPt)));
		buttonShadowLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:buttonShadowBlurPt)));
		buttonShadowXLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:buttonShadowOffsetXPt)));
		buttonShadowYLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:buttonShadowOffsetYPt)));
		surfCXLabel:emit(value: (vm:surfCenterXPct as String) . '%');
		surfCYLabel:emit(value: (vm:surfCenterYPct as String) . '%');
		surfAngLabel:emit(value: (vm:surfAngleDeg as String) . ' deg');
		surfBwLabel:emit(value: (vm:surfBlendPct as String) . '%');
		btnCXLabel:emit(value: (vm:btnCenterXPct as String) . '%');
		btnCYLabel:emit(value: (vm:btnCenterYPct as String) . '%');
		btnAngLabel:emit(value: (vm:btnAngleDeg as String) . ' deg');
		btnBwLabel:emit(value: (vm:btnBlendPct as String) . '%');

		:surfFillDropdown: SelectDropdown(
			options: fillStyleLabels,
			selectedIndex: vm:surfFillStyleIdx,
			minWidthPt: 105.0,
			onSelect: local Function(Int is idx, String is _val){ vm:setSurfFillStyleIndex(idx: idx); }
		);
		:surfBoundsDropdown: SelectDropdown(
			options: boundsLabels,
			selectedIndex: if({ vm:surfBounds == GradientBounds:CIRCUMSCRIBE }, { 1 }, { 0 }),
			minWidthPt: 112.0,
			onSelect: local Function(Int is idx, String is _val){ vm:setSurfBounds(bounds: if({ idx == 1 }, { GradientBounds:CIRCUMSCRIBE }, { GradientBounds:INSCRIBE })); }
		);
		:surfColorASwatch: ColorSwatchDropdown(
			color: vm:colorAtSlot(slot: 0),
			compactPicker: true,
			tooltip: 'Primary surface gradient color (Background)',
			onChange: local Function(Color is c){ vm:setColorSlot(slot: 0, nextCol: c); }
		);
		:useSurfColorBSwitch: Switch(
			checked: vm:useSurfColorB,
			onChange: local Function(Boolean is on){ vm:setUseSurfColorB(enabled: on); }
		);
		:surfColorBSwatch: ColorSwatchDropdown(
			color: vm:surfColorB,
			compactPicker: true,
			tooltip: 'Optional second surface gradient color',
			onChange: local Function(Color is c){ vm:setSurfColorB(col: c); }
		);
		:surfCXSlider: Slider(minVal: 0, maxVal: 100, value: vm:surfCenterXPct, minWidthPt: 105.0, onChange: local Function(Int is v){ vm:setSurfCenterX(pct: v); });
		:surfCYSlider: Slider(minVal: 0, maxVal: 100, value: vm:surfCenterYPct, minWidthPt: 105.0, onChange: local Function(Int is v){ vm:setSurfCenterY(pct: v); });
		:surfAngSlider: Slider(minVal: 0, maxVal: 360, value: vm:surfAngleDeg, minWidthPt: 105.0, onChange: local Function(Int is v){ vm:setSurfAngle(deg: v); });
		:surfBwSlider: Slider(minVal: 0, maxVal: 100, value: vm:surfBlendPct, minWidthPt: 105.0, onChange: local Function(Int is v){ vm:setSurfBlend(pct: v); });

		:btnFillDropdown: SelectDropdown(
			options: fillStyleLabels,
			selectedIndex: vm:btnFillStyleIdx,
			minWidthPt: 105.0,
			onSelect: local Function(Int is idx, String is _val){ vm:setBtnFillStyleIndex(idx: idx); }
		);
		:btnBoundsDropdown: SelectDropdown(
			options: boundsLabels,
			selectedIndex: if({ vm:btnBounds == GradientBounds:CIRCUMSCRIBE }, { 1 }, { 0 }),
			minWidthPt: 112.0,
			onSelect: local Function(Int is idx, String is _val){ vm:setBtnBounds(bounds: if({ idx == 1 }, { GradientBounds:CIRCUMSCRIBE }, { GradientBounds:INSCRIBE })); }
		);
		:btnColorASwatch: ColorSwatchDropdown(
			color: vm:colorAtSlot(slot: 1),
			compactPicker: true,
			tooltip: 'Primary button gradient color (Surface)',
			onChange: local Function(Color is c){ vm:setColorSlot(slot: 1, nextCol: c); }
		);
		:useBtnColorBSwitch: Switch(
			checked: vm:useBtnColorB,
			onChange: local Function(Boolean is on){ vm:setUseBtnColorB(enabled: on); }
		);
		:btnColorBSwatch: ColorSwatchDropdown(
			color: vm:btnColorB,
			compactPicker: true,
			tooltip: 'Optional second button gradient color',
			onChange: local Function(Color is c){ vm:setBtnColorB(col: c); }
		);
		:btnCXSlider: Slider(minVal: 0, maxVal: 100, value: vm:btnCenterXPct, minWidthPt: 105.0, onChange: local Function(Int is v){ vm:setBtnCenterX(pct: v); });
		:btnCYSlider: Slider(minVal: 0, maxVal: 100, value: vm:btnCenterYPct, minWidthPt: 105.0, onChange: local Function(Int is v){ vm:setBtnCenterY(pct: v); });
		:btnAngSlider: Slider(minVal: 0, maxVal: 360, value: vm:btnAngleDeg, minWidthPt: 105.0, onChange: local Function(Int is v){ vm:setBtnAngle(deg: v); });
		:btnBwSlider: Slider(minVal: 0, maxVal: 100, value: vm:btnBlendPct, minWidthPt: 105.0, onChange: local Function(Int is v){ vm:setBtnBlend(pct: v); });

		:hoverBriSlider: Slider(minVal: -60, maxVal: 60, value: vm:hoverBriPct, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setHoverBrightness(pct: v); });
		:hoverTintSlider: Slider(minVal: -180, maxVal: 180, value: vm:hoverTintDeg, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setHoverTint(deg: v); });
		:hoverSatSlider: Slider(minVal: -100, maxVal: 100, value: vm:hoverSatPct, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setHoverSaturation(pct: v); });
		hoverBriLabel:emit(value: (vm:hoverBriPct as String) . '%');
		hoverTintLabel:emit(value: (vm:hoverTintDeg as String) . ' deg');
		hoverSatLabel:emit(value: (vm:hoverSatPct as String) . '%');

		:selectedBriSlider: Slider(minVal: -60, maxVal: 60, value: vm:selectedBriPct, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setSelectedBrightness(pct: v); });
		:selectedTintSlider: Slider(minVal: -180, maxVal: 180, value: vm:selectedTintDeg, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setSelectedTint(deg: v); });
		:selectedSatSlider: Slider(minVal: -100, maxVal: 100, value: vm:selectedSatPct, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setSelectedSaturation(pct: v); });
		selectedBriLabel:emit(value: (vm:selectedBriPct as String) . '%');
		selectedTintLabel:emit(value: (vm:selectedTintDeg as String) . ' deg');
		selectedSatLabel:emit(value: (vm:selectedSatPct as String) . '%');

		:focusBriSlider: Slider(minVal: -60, maxVal: 60, value: vm:focusBriPct, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setFocusBrightness(pct: v); });
		:focusTintSlider: Slider(minVal: -180, maxVal: 180, value: vm:focusTintDeg, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setFocusTint(deg: v); });
		:focusSatSlider: Slider(minVal: -100, maxVal: 100, value: vm:focusSatPct, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setFocusSaturation(pct: v); });
		focusBriLabel:emit(value: (vm:focusBriPct as String) . '%');
		focusTintLabel:emit(value: (vm:focusTintDeg as String) . ' deg');
		focusSatLabel:emit(value: (vm:focusSatPct as String) . '%');

		:baseTextInput: DecoratedTextInput(
			text: vm:baseTextLabel(),
			suffix: ' pt',
			tooltip: 'Override Theme baseTextPt (type number or press Up/Down)',
			onLeftClick: local Function(){ vm:adjustBaseTextPt(delta: -1.0); },
			onRightClick: local Function(){ vm:adjustBaseTextPt(delta: 1.0); },
			onSubmit: local Function(String is v){ vm:setBaseTextPtFromText(raw: v); }
		);

		:alphaSlider: Slider(
			minVal: 0,
			maxVal: 100,
			value: vm:windowAlphaPct,
			minWidthPt: 180.0,
			tooltip: 'Adjust window background opacity (0% - 100%)',
			onChange: local Function(Int is pct){
				vm:setWindowAlphaPct(pct: pct);
			}
		);
		alphaLabel:emit(value: (vm:windowAlphaPct as String) . '%');

		local Array of SewNode is colorCells: Array();
		local Int is ci: 0;
		while({ ci < colorLabels:length() }, {
			local Int is slot: ci;
			local TextInput is inp: TextInput(
				text: vm:colorToHex(c: vm:colorAtSlot(slot: slot)),
				placeholder: '#RRGGBB',
				minWidthPt: 84.0,
				tooltip: 'Enter #RRGGBB hex color and press Enter or Tab',
				onSubmit: local Function(String is v){ vm:setColorSlotFromHex(slot: slot, raw: v); }
			);
			local ColorSwatchDropdown is sw: ColorSwatchDropdown(
				color: vm:colorAtSlot(slot: slot),
				compactPicker: true,
				tooltip: 'Pick color from compact picker or swatch history',
				onChange: local Function(Color is c){ vm:setColorSlot(slot: slot, nextCol: c); }
			);
			colorInputs:add(item: inp);
			colorSwatches:add(item: sw);
			colorCells:add(item: Label(text: colorLabels:get(index: slot)));
			colorCells:add(item: inp);
			colorCells:add(item: sw);
			ci: ci + 1;
		});

		local Grid is colorGrid: Grid(
			columns: 3,
			colGapPt: 10.0,
			rowGapPt: 6.0,
			children: colorCells
		);

		local Array of SewNode is metricCells: Array();
		local Int is mi: 0;
		while({ mi < metricLabels:length() }, {
			local Int is mslot: mi;
			local DecoratedTextInput is mInp: DecoratedTextInput(
				text: vm:metricLabel(slot: mslot),
				suffix: ' pt',
				tooltip: 'Adjust ' . metricLabels:get(index: mslot) . ' (in points)',
				onLeftClick: local Function(){ vm:adjustMetricSlot(slot: mslot, delta: -0.5); },
				onRightClick: local Function(){ vm:adjustMetricSlot(slot: mslot, delta: 0.5); },
				onSubmit: local Function(String is v){ vm:setMetricSlotFromText(slot: mslot, raw: v); }
			);
			metricInputs:add(item: mInp);
			metricCells:add(item: Label(text: metricLabels:get(index: mslot)));
			metricCells:add(item: mInp);
			mi: mi + 1;
		});

		local Grid is metricGrid: Grid(
			columns: 2,
			colGapPt: 12.0,
			rowGapPt: 6.0,
			children: metricCells
		);

		local CodeEditorView is themeJsonEditor: CodeEditorView(
			text: themeJsonText,
			filePath: TextEmitter(initial: 'theme.json'),
			wrap: BoolEmitter(initial: true),
			lineNumbers: BoolEmitter(initial: false),
			monospace: BoolEmitter(initial: true),
			onTextChange: local Function(String is next){
				themeJsonText:emit(value: next);
			},
			onClipboardWrite: local Function(String is clip){
				vm:writeClipboard(text: clip);
			},
			onClipboardRead: local Function of String(){
				return vm:readClipboard();
			}
		);

		local Popover is jsonPopover: Popover(
			anchor: ScrapButton(
				label: 'JSON Import / Export',
				tooltip: 'Open theme JSON export and import tools'
			),
			closeOnOutsideClick: true,
			resizable: true,
			maxWidthPt: 400.0,
			maxHeightPt: 290.0,
			content: Frame(
				title: 'Theme JSON (Export / Import)',
				child: Column(
					gapPt: 6.0,
					flexFlags: Array([false, true]),
					children: Array([
						SectionH(
							children: Array([
								ScrapButton(
									label: 'Export JSON',
									onClick: local Function(){
										local String is outJson: vm:activeTheme:toJson();
										themeJsonText:emit(value: outJson);
										vm:statusText:emit(value: 'Exported theme JSON (' . (outJson:length() as String) . ' bytes)');
									}
								),
								ScrapButton(
									label: 'Import JSON',
									onClick: local Function(){
										vm:importThemeJson(json: themeJsonText:current());
									}
								),
								ScrapButton(
									label: 'Copy',
									tooltip: 'Copy selected JSON (or full theme JSON) to clipboard',
									onClick: local Function(){
										local String is copied: themeJsonEditor:copySelection();
										if({ copied != '' }, {
											vm:statusText:emit(value: 'Copied selection (' . (copied:length() as String) . ' bytes)');
											return;
										});
										local String is cur: themeJsonText:current();
										if({ cur == '' }, {
											cur: vm:activeTheme:toJson();
											themeJsonText:emit(value: cur);
										});
										vm:writeClipboard(text: cur);
										vm:statusText:emit(value: 'Copied theme JSON (' . (cur:length() as String) . ' bytes)');
									}
								),
								ScrapButton(
									label: 'Paste',
									tooltip: 'Paste clipboard JSON into the editor',
									onClick: local Function(){
										local String is clip: vm:readClipboard();
										if({ clip == '' }, {
											vm:statusText:emit(value: 'Clipboard is empty');
											return;
										});
										themeJsonText:emit(value: clip);
										vm:statusText:emit(value: 'Pasted JSON (' . (clip:length() as String) . ' bytes)');
									}
								)
							])
						),
						Frame(
							padPt: 0.0,
							child: ScrollView(heightPt: 180.0, allowHScroll: true, child: themeJsonEditor)
						)
					])
				)
			)
		);

		local Frame is previewFrame: Frame(
			title: 'Live Theme Preview',
			child: Column(
				gapPt: 6.0,
				children: Array([
					SectionH(
						children: Array([
							ScrapButton(label: 'Primary Action', onClick: local Function(){
								vm:statusText:emit(value: 'Theme preview button clicked');
							}),
							ScrapButton(label: 'Disabled', enabled: false),
							Checkbox(checked: true, label: 'Check'),
							RadioButton(selected: true, label: 'Radio'),
							Switch(checked: true),
							Badge(text: 'Accent', accent: true),
							Badge(text: 'Tag', closable: true)
						])
					),
					SectionH(
						children: Array([
							TextInput(text: 'Sample input', minWidthPt: 105.0),
							SelectDropdown(options: Array(['Option A', 'Option B', 'Option C']), selectedIndex: 0, minWidthPt: 100.0),
							NumberInput(value: 42.0, minVal: 0.0, maxVal: 100.0, minWidthPt: 82.0),
							Slider(minVal: 0, maxVal: 100, value: 65, minWidthPt: 90.0),
							ProgressBar(value: 0.68, showLabel: true, minWidthPt: 105.0)
						])
					),
					SectionH(
						children: Array([
							SectionH(segmented: true, options: Array(['One', 'Two', 'Three']), selectedIndex: 1, itemMinWidthPt: 44.0),
							Label(text: 'Heading', style: TextStyle:H3),
							Label(text: 'Muted caption', style: TextStyle:CAPTION),
							Label(text: 'Code', style: TextStyle:CODE, boxed: true)
						])
					)
				])
			)
		);

		local SewNode is colorsTab: Frame(
			title: 'Theme Color Tokens (#RRGGBB)',
			child: colorGrid
		);

		local SewNode is fillsTab: Row(
			gapPt: 8.0,
			children: Array([
				Column(
					gapPt: 8.0,
					children: Array([
						Frame(
							title: 'Surface Fill',
							child: Column(
								gapPt: 6.0,
								children: Array([
									SectionH(children: Array([surfFillDropdown, surfBoundsDropdown])),
									Grid(
										columns: 3,
										colGapPt: 8.0,
										rowGapPt: 6.0,
										children: Array([
											Label(text: 'Colors'), SectionH(children: Array([surfColorASwatch, useSurfColorBSwitch, surfColorBSwatch])), Label(text: ''),
											Label(text: 'Center X'), surfCXSlider, TextScrap(text: surfCXLabel, muted: true),
											Label(text: 'Center Y'), surfCYSlider, TextScrap(text: surfCYLabel, muted: true),
											Label(text: 'Linear Angle'), surfAngSlider, TextScrap(text: surfAngLabel, muted: true),
											Label(text: 'Blend Width'), surfBwSlider, TextScrap(text: surfBwLabel, muted: true)
										])
									)
								])
							)
						),
						Frame(
							title: 'Button Fill',
							child: Column(
								gapPt: 6.0,
								children: Array([
									SectionH(children: Array([btnFillDropdown, btnBoundsDropdown])),
									Grid(
										columns: 3,
										colGapPt: 8.0,
										rowGapPt: 6.0,
										children: Array([
											Label(text: 'Colors'), SectionH(children: Array([btnColorASwatch, useBtnColorBSwitch, btnColorBSwatch])), Label(text: ''),
											Label(text: 'Center X'), btnCXSlider, TextScrap(text: btnCXLabel, muted: true),
											Label(text: 'Center Y'), btnCYSlider, TextScrap(text: btnCYLabel, muted: true),
											Label(text: 'Linear Angle'), btnAngSlider, TextScrap(text: btnAngLabel, muted: true),
											Label(text: 'Blend Width'), btnBwSlider, TextScrap(text: btnBwLabel, muted: true)
										])
									)
								])
							)
						)
					])
				),
				Frame(
					title: 'State Effects (Hover, Selected, Focused)',
					child: Grid(
						columns: 3,
						colGapPt: 8.0,
						rowGapPt: 6.0,
						children: Array([
							Label(text: 'Hover Brightness'), hoverBriSlider, TextScrap(text: hoverBriLabel, muted: true),
							Label(text: 'Hover Tint Shift'), hoverTintSlider, TextScrap(text: hoverTintLabel, muted: true),
							Label(text: 'Hover Saturation'), hoverSatSlider, TextScrap(text: hoverSatLabel, muted: true),
							Label(text: 'Selected Brightness'), selectedBriSlider, TextScrap(text: selectedBriLabel, muted: true),
							Label(text: 'Selected Tint Shift'), selectedTintSlider, TextScrap(text: selectedTintLabel, muted: true),
							Label(text: 'Selected Saturation'), selectedSatSlider, TextScrap(text: selectedSatLabel, muted: true),
							Label(text: 'Focus Brightness'), focusBriSlider, TextScrap(text: focusBriLabel, muted: true),
							Label(text: 'Focus Tint Shift'), focusTintSlider, TextScrap(text: focusTintLabel, muted: true),
							Label(text: 'Focus Saturation'), focusSatSlider, TextScrap(text: focusSatLabel, muted: true)
						])
					)
				)
			])
		);

		local SewNode is bordersTab: Row(
			gapPt: 8.0,
			children: Array([
				Frame(
					title: 'Panel Border & Shadows',
					child: Column(
						gapPt: 6.0,
						children: Array([
							Grid(
								columns: 3,
								colGapPt: 8.0,
								rowGapPt: 6.0,
								children: Array([
									Label(text: 'Panel Style'), panelStyleDropdown, Label(text: ''),
									Label(text: 'Panel Thickness'), panelThickSlider, TextScrap(text: panelThickLabel, muted: true),
									Label(text: 'Panel Radius'), panelRadiusSlider, TextScrap(text: panelRadiusLabel, muted: true),
									Label(text: 'Shadow Blur'), panelShadowSlider, TextScrap(text: panelShadowLabel, muted: true),
									Label(text: 'Shadow X'), panelShadowXSlider, TextScrap(text: panelShadowXLabel, muted: true),
									Label(text: 'Shadow Y'), panelShadowYSlider, TextScrap(text: panelShadowYLabel, muted: true),
									Label(text: 'Inner Blur'), panelInnerShadowSlider, TextScrap(text: panelInnerShadowLabel, muted: true),
									Label(text: 'Inner X'), panelInnerShadowXSlider, TextScrap(text: panelInnerShadowXLabel, muted: true),
									Label(text: 'Inner Y'), panelInnerShadowYSlider, TextScrap(text: panelInnerShadowYLabel, muted: true)
								])
							)
						])
					)
				),
				Column(
					gapPt: 8.0,
					children: Array([
						Frame(
							title: 'Divider',
							child: Grid(
								columns: 3,
								colGapPt: 8.0,
								rowGapPt: 6.0,
								children: Array([
									Label(text: 'Divider Style'), dividerStyleDropdown, Label(text: ''),
									Label(text: 'Thickness'), dividerThickSlider, TextScrap(text: dividerThickLabel, muted: true)
								])
							)
						),
						Frame(
							title: 'Button Border & Shadow',
							child: Grid(
								columns: 3,
								colGapPt: 8.0,
								rowGapPt: 6.0,
								children: Array([
									Label(text: 'Button Style'), buttonStyleDropdown, Label(text: ''),
									Label(text: 'Thickness'), buttonThickSlider, TextScrap(text: buttonThickLabel, muted: true),
									Label(text: 'Radius'), buttonRadiusSlider, TextScrap(text: buttonRadiusLabel, muted: true),
									Label(text: 'Shadow Blur'), buttonShadowSlider, TextScrap(text: buttonShadowLabel, muted: true),
									Label(text: 'Shadow X'), buttonShadowXSlider, TextScrap(text: buttonShadowXLabel, muted: true),
									Label(text: 'Shadow Y'), buttonShadowYSlider, TextScrap(text: buttonShadowYLabel, muted: true)
								])
							)
						)
					])
				)
			])
		);

		local SewNode is layoutTab: Column(
			gapPt: 8.0,
			children: Array([
				Frame(
					title: 'Typography, Borders & Window Translucency',
					child: Grid(
						columns: 2,
						colGapPt: 12.0,
						rowGapPt: 6.0,
						children: Array([
							Label(text: 'Base Text Size'), baseTextInput,
							Label(text: 'Global Border Style'), borderSection,
							Label(text: 'Window Opacity'), SectionH(children: Array([alphaSlider, TextScrap(text: alphaLabel, muted: true)]))
						])
					)
				),
				Frame(
					title: 'Padding & Spacing (pt)',
					child: metricGrid
				)
			])
		);

		local Array of String is tabIds: Array(['layout', 'colors', 'fills', 'borders']);
		:optionTabs: TabBar(
			tabs: Array([
				TabItemConfig(id: 'layout', label: 'Typography & Spacing', closable: false),
				TabItemConfig(id: 'colors', label: 'Colors', closable: false),
				TabItemConfig(id: 'fills', label: 'Fills & Effects', closable: false),
				TabItemConfig(id: 'borders', label: 'Borders & Shadows', closable: false)
			]),
			activeIndex: 0,
			showCloseButton: false,
			reorderable: false,
			onSelectTab: local Function(Int is idx){
				optionTabs:selectTab(index: idx);
				if({ idx >= 0 && idx < tabIds:length() }, {
					activeTabRoute:emit(value: tabIds:get(index: idx));
				});
			}
		);

		local NavStack is tabContent: NavStack(
			route: activeTabRoute,
			routes: Array([
				NavRoute(name: 'layout', child: layoutTab),
				NavRoute(name: 'colors', child: colorsTab),
				NavRoute(name: 'fills', child: fillsTab),
				NavRoute(name: 'borders', child: bordersTab)
			])
		);

		return SectionV(
			children: Array([
				SectionH(
					children: Array([
						Label(text: 'Theme Builder', style: TextStyle:H1),
						presetSection,
						ScrapButton(
							label: 'Reset to Preset',
							tooltip: 'Reload the active Light or Dark preset defaults',
							onClick: local Function(){ vm:loadPreset(preset: vm:basePreset); }
						),
						jsonPopover
					])
				),
				previewFrame,
				Column(
					gapPt: 0.0,
					children: Array([
						optionTabs,
						tabContent
					])
				)
			])
		);
	}

	Function is sync(){
		presetSection:setSelectedIndex(index: :presetIndex(p: vm:basePreset));
		borderSection:setSelectedIndex(index: :borderIndex(style: vm:borderStyle));
		panelStyleDropdown:setSelectedIndex(index: :targetStyleIndex(style: vm:activeTheme:panelBorderStyle));
		dividerStyleDropdown:setSelectedIndex(index: :targetStyleIndex(style: vm:activeTheme:dividerStyle));
		buttonStyleDropdown:setSelectedIndex(index: :targetStyleIndex(style: vm:activeTheme:buttonBorderStyle));
		panelThickSlider:setValue(next: vm:toTenths(pt: vm:activeTheme:panelBorderThicknessPt));
		panelRadiusSlider:setValue(next: vm:toTenths(pt: vm:activeTheme:panelCornerRadiusPt));
		panelShadowSlider:setValue(next: vm:toTenths(pt: vm:activeTheme:panelShadowBlurPt));
		panelShadowXSlider:setValue(next: vm:toTenths(pt: vm:activeTheme:panelShadowOffsetXPt));
		panelShadowYSlider:setValue(next: vm:toTenths(pt: vm:activeTheme:panelShadowOffsetYPt));
		panelInnerShadowSlider:setValue(next: vm:toTenths(pt: vm:activeTheme:panelInnerShadowBlurPt));
		panelInnerShadowXSlider:setValue(next: vm:toTenths(pt: vm:activeTheme:panelInnerShadowOffsetXPt));
		panelInnerShadowYSlider:setValue(next: vm:toTenths(pt: vm:activeTheme:panelInnerShadowOffsetYPt));
		dividerThickSlider:setValue(next: vm:toTenths(pt: vm:activeTheme:dividerThicknessPt));
		buttonThickSlider:setValue(next: vm:toTenths(pt: vm:activeTheme:buttonBorderThicknessPt));
		buttonRadiusSlider:setValue(next: vm:toTenths(pt: vm:activeTheme:buttonCornerRadiusPt));
		buttonShadowSlider:setValue(next: vm:toTenths(pt: vm:activeTheme:buttonShadowBlurPt));
		buttonShadowXSlider:setValue(next: vm:toTenths(pt: vm:activeTheme:buttonShadowOffsetXPt));
		buttonShadowYSlider:setValue(next: vm:toTenths(pt: vm:activeTheme:buttonShadowOffsetYPt));
		panelThickLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelBorderThicknessPt)));
		panelRadiusLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelCornerRadiusPt)));
		panelShadowLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelShadowBlurPt)));
		panelShadowXLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelShadowOffsetXPt)));
		panelShadowYLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelShadowOffsetYPt)));
		panelInnerShadowLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelInnerShadowBlurPt)));
		panelInnerShadowXLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelInnerShadowOffsetXPt)));
		panelInnerShadowYLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:panelInnerShadowOffsetYPt)));
		dividerThickLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:dividerThicknessPt)));
		buttonThickLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:buttonBorderThicknessPt)));
		buttonRadiusLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:buttonCornerRadiusPt)));
		buttonShadowLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:buttonShadowBlurPt)));
		buttonShadowXLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:buttonShadowOffsetXPt)));
		buttonShadowYLabel:emit(value: vm:tenthsLabel(tenths: vm:toTenths(pt: vm:activeTheme:buttonShadowOffsetYPt)));
		surfFillDropdown:setSelectedIndex(index: vm:surfFillStyleIdx);
		surfBoundsDropdown:setSelectedIndex(index: if({ vm:surfBounds == GradientBounds:CIRCUMSCRIBE }, { 1 }, { 0 }));
		surfColorASwatch:setColor(next: vm:colorAtSlot(slot: 0));
		useSurfColorBSwitch:setChecked(next: vm:useSurfColorB);
		surfColorBSwatch:setColor(next: vm:surfColorB);
		surfCXSlider:setValue(next: vm:surfCenterXPct);
		surfCYSlider:setValue(next: vm:surfCenterYPct);
		surfAngSlider:setValue(next: vm:surfAngleDeg);
		surfBwSlider:setValue(next: vm:surfBlendPct);
		surfCXLabel:emit(value: (vm:surfCenterXPct as String) . '%');
		surfCYLabel:emit(value: (vm:surfCenterYPct as String) . '%');
		surfAngLabel:emit(value: (vm:surfAngleDeg as String) . ' deg');
		surfBwLabel:emit(value: (vm:surfBlendPct as String) . '%');
		btnFillDropdown:setSelectedIndex(index: vm:btnFillStyleIdx);
		btnBoundsDropdown:setSelectedIndex(index: if({ vm:btnBounds == GradientBounds:CIRCUMSCRIBE }, { 1 }, { 0 }));
		btnColorASwatch:setColor(next: vm:colorAtSlot(slot: 1));
		useBtnColorBSwitch:setChecked(next: vm:useBtnColorB);
		btnColorBSwatch:setColor(next: vm:btnColorB);
		btnCXSlider:setValue(next: vm:btnCenterXPct);
		btnCYSlider:setValue(next: vm:btnCenterYPct);
		btnAngSlider:setValue(next: vm:btnAngleDeg);
		btnBwSlider:setValue(next: vm:btnBlendPct);
		btnCXLabel:emit(value: (vm:btnCenterXPct as String) . '%');
		btnCYLabel:emit(value: (vm:btnCenterYPct as String) . '%');
		btnAngLabel:emit(value: (vm:btnAngleDeg as String) . ' deg');
		btnBwLabel:emit(value: (vm:btnBlendPct as String) . '%');
		hoverBriSlider:setValue(next: vm:hoverBriPct);
		hoverTintSlider:setValue(next: vm:hoverTintDeg);
		hoverSatSlider:setValue(next: vm:hoverSatPct);
		hoverBriLabel:emit(value: (vm:hoverBriPct as String) . '%');
		hoverTintLabel:emit(value: (vm:hoverTintDeg as String) . ' deg');
		hoverSatLabel:emit(value: (vm:hoverSatPct as String) . '%');
		baseTextInput:setText(next: vm:baseTextLabel());
		alphaSlider:setValue(next: vm:windowAlphaPct);
		alphaLabel:emit(value: (vm:windowAlphaPct as String) . '%');
		local Int is i: 0;
		while({ i < colorInputs:length() }, {
			local Color is colVal: vm:colorAtSlot(slot: i);
			colorInputs:get(index: i):setText(next: vm:colorToHex(c: colVal));
			if({ i < colorSwatches:length() }, {
				colorSwatches:get(index: i):setColor(next: colVal);
			});
			i: i + 1;
		});
		local Int is mi: 0;
		while({ mi < metricInputs:length() }, {
			metricInputs:get(index: mi):setText(next: vm:metricLabel(slot: mi));
			mi: mi + 1;
		});
	}
}
