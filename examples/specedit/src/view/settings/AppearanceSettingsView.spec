#! Package specedit:view:settings
#! Appearance settings category view using Grid, NumberInput, SectionH, and Frame.

Class is AppearanceSettingsView{
	replace [String] is namespace: ['specedit', 'view', 'settings'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Column],
		['base', 'sew', Row],
		['base', 'sew', Grid],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['base', 'scrap', NumberInput],
		['base', 'fabric', Theme],
		['base', 'fabric', ThemePreset],
		['base', 'fabric', TextStyle],
		['specedit', 'viewmodel', SettingsViewModel]
	];

	SettingsViewModel is vm: SettingsViewModel();
	SectionH is themeSection: SectionH();
	NumberInput is docDeltaInput: NumberInput();
	NumberInput is baseTextInput: NumberInput();
	Array of Int is zoomValues: Array([70, 100, 115, 130]);
	SectionH is zoomSection: SectionH();

	replace Function is init(SettingsViewModel is vm){
		:vm: vm;
		:themeSection: SectionH();
		:zoomSection: SectionH();
	}

	local Function of Int is presetIndex(ThemePreset is preset){
		local Array of ThemePreset is presets: Theme:presets();
		local Int is i: 0;
		while({ i < presets:length() }, {
			if({ presets:get(index: i) == preset }, { return i; });
			i: i + 1;
		});
		return 0;
	}

	local Function of Int is zoomIndex(Int is pct){
		local Int is i: 0;
		while({ i < zoomValues:length() }, {
			if({ zoomValues:get(index: i) == pct }, { return i; });
			i: i + 1;
		});
		return 1;
	}

	Function of SewNode is build(){
		local Array of ThemePreset is presets: Theme:presets();
		local Array of String is themeLabels: Array();
		local Int is ti: 0;
		while({ ti < presets:length() }, {
			themeLabels:add(item: Theme:presetLabel(preset: presets:get(index: ti)));
			ti: ti + 1;
		});
		:themeSection: SectionH(
			segmented: true,
			options: themeLabels,
			selectedIndex: :presetIndex(preset: vm:model:themePreset),
			itemMinWidthPt: 64.0,
			onSelect: local Function(Int is idx){
				local Array of ThemePreset is ps: Theme:presets();
				if({ idx >= 0 && idx < ps:length() }, {
					vm:selectTheme(preset: ps:get(index: idx));
				});
			}
		);

		:docDeltaInput: NumberInput(
			value: vm:model:docTextDeltaPt,
			minVal: -6.0,
			maxVal: 16.0,
			step: 1.0,
			decimals: 0,
			suffix: ' pt',
			minWidthPt: 100.0,
			tooltip: 'Adjust editor font size offset (-6 to +16 pt)',
			onChange: local Function(Float is nextVal){ vm:setDocTextDelta(nextVal: nextVal); }
		);

		:baseTextInput: NumberInput(
			value: vm:model:baseTextPt,
			minVal: 8.0,
			maxVal: 20.0,
			step: 1.0,
			decimals: 0,
			suffix: ' pt',
			minWidthPt: 100.0,
			tooltip: 'Set base UI font size in points (8 to 20 pt)',
			onChange: local Function(Float is nextVal){ vm:setBaseTextPt(nextVal: nextVal); }
		);

		local Row is docSizeRow: Row(
			gapPt: 6.0,
			children: Array([
				docDeltaInput,
				ScrapButton(
					label: 'Reset',
					minWidthPt: 48.0,
					tooltip: 'Reset document font offset to 0 pt',
					onClick: local Function(){ vm:resetDocTextDelta(); }
				)
			])
		);

		local Row is baseTextRow: Row(
			gapPt: 6.0,
			children: Array([
				baseTextInput,
				ScrapButton(
					label: 'Reset',
					minWidthPt: 48.0,
					tooltip: 'Reset default theme text size to 10 pt',
					onClick: local Function(){ vm:resetBaseTextPt(); }
				)
			])
		);

		local Array of String is zoomLabels: Array();
		local Int is zi: 0;
		while({ zi < zoomValues:length() }, {
			zoomLabels:add(item: (zoomValues:get(index: zi) as String) . '%');
			zi: zi + 1;
		});
		:zoomSection: SectionH(
			segmented: true,
			options: zoomLabels,
			selectedIndex: :zoomIndex(pct: vm:model:uiZoomPct),
			itemMinWidthPt: 46.0,
			onSelect: local Function(Int is idx){
				if({ idx >= 0 && idx < zoomValues:length() }, {
					vm:selectZoomPct(pct: zoomValues:get(index: idx));
				});
			}
		);

		:sync();

		local Grid is themeGrid: Grid(
			columns: 2,
			colGapPt: 12.0,
			rowGapPt: 8.0,
			flexCols: Array([true, false]),
			children: Array([
				Column(
					gapPt: 1.0,
					children: Array([
						Label(text: 'Color Theme'),
						Label(text: 'Switch between light and dark palettes', style: TextStyle:CAPTION, muted: true)
					])
				),
				themeSection,
				Column(
					gapPt: 1.0,
					children: Array([
						Label(text: 'UI Zoom'),
						Label(text: 'Scale interface controls and spacing', style: TextStyle:CAPTION, muted: true)
					])
				),
				zoomSection
			])
		);

		local Grid is textGrid: Grid(
			columns: 2,
			colGapPt: 12.0,
			rowGapPt: 8.0,
			flexCols: Array([true, false]),
			children: Array([
				Column(
					gapPt: 1.0,
					children: Array([
						Label(text: 'Document Font Offset'),
						Label(text: 'Relative to default editor font size', style: TextStyle:CAPTION, muted: true)
					])
				),
				docSizeRow,
				Column(
					gapPt: 1.0,
					children: Array([
						Label(text: 'Interface Font Size'),
						Label(text: 'Default theme text size in points', style: TextStyle:CAPTION, muted: true)
					])
				),
				baseTextRow
			])
		);

		return Column(
			gapPt: 10.0,
			children: Array([
				Row(
					gapPt: 8.0,
					flexFlags: Array([true, false]),
					children: Array([
						Label(text: 'Appearance', heading: true),
						ScrapButton(
							label: 'Reset All',
							minWidthPt: 68.0,
							tooltip: 'Restore all appearance settings to defaults',
							onClick: local Function(){ vm:resetAppearance(); }
						)
					])
				),
				Frame(
					title: 'Theme & Scale',
					fillBg: true,
					child: themeGrid
				),
				Frame(
					title: 'Typography',
					fillBg: true,
					child: textGrid
				)
			])
		);
	}

	Function is sync(){
		themeSection:setSelectedIndex(index: :presetIndex(preset: vm:model:themePreset));
		docDeltaInput:setValue(next: vm:model:docTextDeltaPt);
		baseTextInput:setValue(next: vm:model:baseTextPt);
		zoomSection:setSelectedIndex(index: :zoomIndex(pct: vm:model:uiZoomPct));
	}
}