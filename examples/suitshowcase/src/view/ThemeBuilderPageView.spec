#! Package suitshowcase:view
#! Live Theme Builder page allowing preset loading and form overrides of base colors, text size, and border style.

Class is ThemeBuilderPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'sew', Grid],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', Slider],
		['base', 'scrap', Switch],
		['base', 'scrap', ColorSwatchDropdown],
		['base', 'scrap', TextInput],
		['base', 'scrap', DecoratedTextInput],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['base', 'scrap', 'text', TextScrap],
		['base', 'fabric', Color],
		['base', 'fabric', Theme],
		['base', 'fabric', ThemePreset],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();
	SectionH is presetSection: SectionH();
	SectionH is borderSection: SectionH();
	SectionH is panelStyleSection: SectionH();
	SectionH is dividerStyleSection: SectionH();
	SectionH is buttonStyleSection: SectionH();
	SectionH is fillStyleSection: SectionH();
	Switch is useColorBSwitch: Switch();
	ColorSwatchDropdown is colorBSwatch: ColorSwatchDropdown();
	Slider is fillCenterXSlider: Slider();
	Slider is fillCenterYSlider: Slider();
	Slider is fillAngleSlider: Slider();
	Slider is fillBlendSlider: Slider();
	TextEmitter is fillCXLabel: TextEmitter(initial: '50%');
	TextEmitter is fillCYLabel: TextEmitter(initial: '50%');
	TextEmitter is fillAngLabel: TextEmitter(initial: '35 deg');
	TextEmitter is fillBwLabel: TextEmitter(initial: '1.00');
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
	Array of String is targetBorderStyles: Array(['none', 'single', 'double', 'bevel', 'groove', 'inset', 'outset']);
	Array of String is targetBorderLabels: Array(['None', 'Single', 'Double', 'Bevel', 'Groove', 'Inset', 'Outset']);
	Array of String is fillStyleLabels: Array(['Solid', 'Linear', 'Lin Refl', 'Radial', 'Rad Refl']);

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

	local Function of Int is targetStyleIndex(String is style){
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

		:panelStyleSection: SectionH(
			segmented: true,
			options: targetBorderLabels,
			selectedIndex: :targetStyleIndex(style: vm:activeTheme:panelBorderStyle),
			itemMinWidthPt: 46.0,
			onSelect: local Function(Int is idx){
				if({ idx >= 0 && idx < targetBorderStyles:length() }, {
					vm:setPanelBorderStyle(style: targetBorderStyles:get(index: idx));
				});
			}
		);

		:dividerStyleSection: SectionH(
			segmented: true,
			options: targetBorderLabels,
			selectedIndex: :targetStyleIndex(style: vm:activeTheme:dividerStyle),
			itemMinWidthPt: 46.0,
			onSelect: local Function(Int is idx){
				if({ idx >= 0 && idx < targetBorderStyles:length() }, {
					vm:setDividerStyle(style: targetBorderStyles:get(index: idx));
				});
			}
		);

		:buttonStyleSection: SectionH(
			segmented: true,
			options: targetBorderLabels,
			selectedIndex: :targetStyleIndex(style: vm:activeTheme:buttonBorderStyle),
			itemMinWidthPt: 46.0,
			onSelect: local Function(Int is idx){
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
		fillCXLabel:emit(value: (vm:fillCenterXPct as String) . '%');
		fillCYLabel:emit(value: (vm:fillCenterYPct as String) . '%');
		fillAngLabel:emit(value: (vm:fillAngleDeg as String) . ' deg');
		fillBwLabel:emit(value: vm:tenthsLabel(tenths: vm:fillBlendPct / 10));

		:fillStyleSection: SectionH(
			segmented: true,
			options: fillStyleLabels,
			selectedIndex: vm:fillStyleIdx,
			itemMinWidthPt: 52.0,
			onSelect: local Function(Int is idx){
				vm:setFillStyleIndex(idx: idx);
			}
		);
		:useColorBSwitch: Switch(
			checked: vm:useFillColorB,
			onChange: local Function(Boolean is on){
				vm:setUseFillColorB(enabled: on);
			}
		);
		:colorBSwatch: ColorSwatchDropdown(
			color: vm:fillColorB,
			compactPicker: true,
			tooltip: 'Optional second gradient color',
			onChange: local Function(Color is c){
				vm:setFillColorB(col: c);
			}
		);
		:fillCenterXSlider: Slider(minVal: 0, maxVal: 100, value: vm:fillCenterXPct, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setFillCenterX(pct: v); });
		:fillCenterYSlider: Slider(minVal: 0, maxVal: 100, value: vm:fillCenterYPct, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setFillCenterY(pct: v); });
		:fillAngleSlider: Slider(minVal: 0, maxVal: 360, value: vm:fillAngleDeg, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setFillAngle(deg: v); });
		:fillBlendSlider: Slider(minVal: 10, maxVal: 200, value: vm:fillBlendPct, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setFillBlend(pct: v); });

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

		return SectionV(
			children: Array([
				SectionH(
					children: Array([
						Label(text: 'Theme Builder', heading: true),
						ScrapButton(
							label: 'Reset to Preset',
							tooltip: 'Reload the active Light or Dark preset defaults',
							onClick: local Function(){ vm:loadPreset(preset: vm:basePreset); }
						)
					])
				),
				Frame(
					title: 'Base Preset',
					child: presetSection
				),
				Frame(
					title: 'Typography & Borders',
					child: SectionV(
						children: Array([
							SectionV(title: 'Base Text Size', children: Array([baseTextInput])),
							SectionV(title: 'Border Style', children: Array([borderSection]))
						])
					)
				),
				Frame(
					title: 'Window Translucency (Separate from Theme)',
					child: SectionH(
						children: Array([
							alphaSlider,
							TextScrap(text: alphaLabel, muted: true)
						])
					)
				),
				Frame(
					title: 'Theme Color Tokens (#RRGGBB)',
					child: colorGrid
				),
				Frame(
					title: 'Surface & Button Fill',
					child: SectionV(
						children: Array([
							SectionV(title: 'Fill Style', children: Array([fillStyleSection])),
							Grid(
								columns: 3,
								colGapPt: 10.0,
								rowGapPt: 6.0,
								children: Array([
									Label(text: 'Use Second Color'), useColorBSwitch, colorBSwatch,
									Label(text: 'Center X'), fillCenterXSlider, TextScrap(text: fillCXLabel, muted: true),
									Label(text: 'Center Y'), fillCenterYSlider, TextScrap(text: fillCYLabel, muted: true),
									Label(text: 'Linear Angle'), fillAngleSlider, TextScrap(text: fillAngLabel, muted: true),
									Label(text: 'Blend Width'), fillBlendSlider, TextScrap(text: fillBwLabel, muted: true)
								])
							)
						])
					)
				),
				Frame(
					title: 'Padding & Spacing (pt)',
					child: metricGrid
				),
				Frame(
					title: 'Panel, Divider & Button Styles',
					child: SectionV(
						children: Array([
							SectionV(title: 'Panel Border Style', children: Array([panelStyleSection])),
							Grid(
								columns: 3,
								colGapPt: 10.0,
								rowGapPt: 6.0,
								children: Array([
									Label(text: 'Panel Thickness'), panelThickSlider, TextScrap(text: panelThickLabel, muted: true),
									Label(text: 'Panel Radius'), panelRadiusSlider, TextScrap(text: panelRadiusLabel, muted: true),
									Label(text: 'Panel Shadow Blur'), panelShadowSlider, TextScrap(text: panelShadowLabel, muted: true),
									Label(text: 'Panel Shadow X'), panelShadowXSlider, TextScrap(text: panelShadowXLabel, muted: true),
									Label(text: 'Panel Shadow Y'), panelShadowYSlider, TextScrap(text: panelShadowYLabel, muted: true),
									Label(text: 'Panel Inner Blur'), panelInnerShadowSlider, TextScrap(text: panelInnerShadowLabel, muted: true),
									Label(text: 'Panel Inner X'), panelInnerShadowXSlider, TextScrap(text: panelInnerShadowXLabel, muted: true),
									Label(text: 'Panel Inner Y'), panelInnerShadowYSlider, TextScrap(text: panelInnerShadowYLabel, muted: true)
								])
							),
							SectionV(title: 'Divider Style', children: Array([dividerStyleSection])),
							Grid(
								columns: 3,
								colGapPt: 10.0,
								rowGapPt: 6.0,
								children: Array([
									Label(text: 'Divider Thickness'), dividerThickSlider, TextScrap(text: dividerThickLabel, muted: true)
								])
							),
							SectionV(title: 'Button Border Style', children: Array([buttonStyleSection])),
							Grid(
								columns: 3,
								colGapPt: 10.0,
								rowGapPt: 6.0,
								children: Array([
									Label(text: 'Button Thickness'), buttonThickSlider, TextScrap(text: buttonThickLabel, muted: true),
									Label(text: 'Button Radius'), buttonRadiusSlider, TextScrap(text: buttonRadiusLabel, muted: true),
									Label(text: 'Button Shadow Blur'), buttonShadowSlider, TextScrap(text: buttonShadowLabel, muted: true),
									Label(text: 'Button Shadow X'), buttonShadowXSlider, TextScrap(text: buttonShadowXLabel, muted: true),
									Label(text: 'Button Shadow Y'), buttonShadowYSlider, TextScrap(text: buttonShadowYLabel, muted: true)
								])
							)
						])
					)
				)
			])
		);
	}

	Function is sync(){
		presetSection:setSelectedIndex(index: :presetIndex(p: vm:basePreset));
		borderSection:setSelectedIndex(index: :borderIndex(style: vm:borderStyle));
		panelStyleSection:setSelectedIndex(index: :targetStyleIndex(style: vm:activeTheme:panelBorderStyle));
		dividerStyleSection:setSelectedIndex(index: :targetStyleIndex(style: vm:activeTheme:dividerStyle));
		buttonStyleSection:setSelectedIndex(index: :targetStyleIndex(style: vm:activeTheme:buttonBorderStyle));
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
		fillStyleSection:setSelectedIndex(index: vm:fillStyleIdx);
		useColorBSwitch:setChecked(next: vm:useFillColorB);
		colorBSwatch:setColor(next: vm:fillColorB);
		fillCenterXSlider:setValue(next: vm:fillCenterXPct);
		fillCenterYSlider:setValue(next: vm:fillCenterYPct);
		fillAngleSlider:setValue(next: vm:fillAngleDeg);
		fillBlendSlider:setValue(next: vm:fillBlendPct);
		fillCXLabel:emit(value: (vm:fillCenterXPct as String) . '%');
		fillCYLabel:emit(value: (vm:fillCenterYPct as String) . '%');
		fillAngLabel:emit(value: (vm:fillAngleDeg as String) . ' deg');
		fillBwLabel:emit(value: vm:tenthsLabel(tenths: vm:fillBlendPct / 10));
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
