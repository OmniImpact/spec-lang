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
	Slider is panelThickSlider: Slider();
	Slider is panelRadiusSlider: Slider();
	Slider is panelShadowSlider: Slider();
	Slider is dividerThickSlider: Slider();
	Slider is buttonThickSlider: Slider();
	Slider is buttonRadiusSlider: Slider();
	Slider is buttonShadowSlider: Slider();
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

		:panelThickSlider: Slider(minVal: 0, maxVal: 8, value: vm:activeTheme:panelBorderThicknessPt as Int, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setPanelBorderThickness(pt: v); });
		:panelRadiusSlider: Slider(minVal: 0, maxVal: 16, value: vm:activeTheme:panelCornerRadiusPt as Int, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setPanelCornerRadius(pt: v); });
		:panelShadowSlider: Slider(minVal: 0, maxVal: 16, value: vm:activeTheme:panelShadowBlurPt as Int, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setPanelShadowBlur(pt: v); });
		:dividerThickSlider: Slider(minVal: 0, maxVal: 8, value: vm:activeTheme:dividerThicknessPt as Int, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setDividerThickness(pt: v); });
		:buttonThickSlider: Slider(minVal: 0, maxVal: 8, value: vm:activeTheme:buttonBorderThicknessPt as Int, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setButtonBorderThickness(pt: v); });
		:buttonRadiusSlider: Slider(minVal: 0, maxVal: 14, value: vm:activeTheme:buttonCornerRadiusPt as Int, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setButtonCornerRadius(pt: v); });
		:buttonShadowSlider: Slider(minVal: 0, maxVal: 14, value: vm:activeTheme:buttonShadowBlurPt as Int, minWidthPt: 110.0, onChange: local Function(Int is v){ vm:setButtonShadowBlur(pt: v); });

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
					title: 'Padding & Spacing (pt)',
					child: metricGrid
				),
				Frame(
					title: 'Panel, Divider & Button Styles',
					child: SectionV(
						children: Array([
							SectionV(title: 'Panel Border Style', children: Array([panelStyleSection])),
							Grid(
								columns: 2,
								colGapPt: 10.0,
								rowGapPt: 6.0,
								children: Array([
									Label(text: 'Panel Thickness'), panelThickSlider,
									Label(text: 'Panel Radius'), panelRadiusSlider,
									Label(text: 'Panel Shadow Blur'), panelShadowSlider
								])
							),
							SectionV(title: 'Divider Style', children: Array([dividerStyleSection])),
							Grid(
								columns: 2,
								colGapPt: 10.0,
								rowGapPt: 6.0,
								children: Array([
									Label(text: 'Divider Thickness'), dividerThickSlider
								])
							),
							SectionV(title: 'Button Border Style', children: Array([buttonStyleSection])),
							Grid(
								columns: 2,
								colGapPt: 10.0,
								rowGapPt: 6.0,
								children: Array([
									Label(text: 'Button Thickness'), buttonThickSlider,
									Label(text: 'Button Radius'), buttonRadiusSlider,
									Label(text: 'Button Shadow Blur'), buttonShadowSlider
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
		panelThickSlider:setValue(next: vm:activeTheme:panelBorderThicknessPt as Int);
		panelRadiusSlider:setValue(next: vm:activeTheme:panelCornerRadiusPt as Int);
		panelShadowSlider:setValue(next: vm:activeTheme:panelShadowBlurPt as Int);
		dividerThickSlider:setValue(next: vm:activeTheme:dividerThicknessPt as Int);
		buttonThickSlider:setValue(next: vm:activeTheme:buttonBorderThicknessPt as Int);
		buttonRadiusSlider:setValue(next: vm:activeTheme:buttonCornerRadiusPt as Int);
		buttonShadowSlider:setValue(next: vm:activeTheme:buttonShadowBlurPt as Int);
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
