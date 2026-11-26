#! Package specedit:view:settings
#! Appearance settings category view using SectionV, SectionH, and DecoratedTextInput.

Class is AppearanceSettingsView{
	replace [String] is namespace: ['specedit', 'view', 'settings'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['base', 'scrap', DecoratedTextInput],
		['base', 'fabric', Theme],
		['base', 'fabric', ThemePreset],
		['specedit', 'viewmodel', SettingsViewModel]
	];

	SettingsViewModel is vm: SettingsViewModel();
	SectionH is themeSection: SectionH();
	DecoratedTextInput is docDeltaInput: DecoratedTextInput();
	DecoratedTextInput is baseTextInput: DecoratedTextInput();
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

		:docDeltaInput: DecoratedTextInput(
			text: vm:docDeltaLabel(),
			onLeftClick: local Function(){ vm:adjustDocTextDelta(delta: -1.0); },
			onRightClick: local Function(){ vm:adjustDocTextDelta(delta: 1.0); },
			onSubmit: local Function(String is v){ vm:setDocTextDeltaFromText(raw: v); }
		);

		:baseTextInput: DecoratedTextInput(
			text: vm:baseTextLabel(),
			onLeftClick: local Function(){ vm:adjustBaseTextPt(delta: -1.0); },
			onRightClick: local Function(){ vm:adjustBaseTextPt(delta: 1.0); },
			onSubmit: local Function(String is v){ vm:setBaseTextPtFromText(raw: v); }
		);

		local SectionH is docSizeRow: SectionH(
			children: Array([
				docDeltaInput,
				ScrapButton(
					label: 'Reset',
					minWidthPt: 50.0,
					onClick: local Function(){ vm:resetDocTextDelta(); }
				)
			])
		);

		local SectionH is baseTextRow: SectionH(
			children: Array([
				baseTextInput,
				ScrapButton(
					label: 'Reset',
					minWidthPt: 50.0,
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
			itemMinWidthPt: 48.0,
			onSelect: local Function(Int is idx){
				if({ idx >= 0 && idx < zoomValues:length() }, {
					vm:selectZoomPct(pct: zoomValues:get(index: idx));
				});
			}
		);

		:sync();

		return SectionV(
			children: Array([
				SectionH(
					children: Array([
						Label(text: 'Appearance', heading: true),
						ScrapButton(
							label: 'Reset All',
							minWidthPt: 64.0,
							onClick: local Function(){ vm:resetAppearance(); }
						)
					])
				),
				Frame(
					title: 'Theme',
					child: themeSection
				),
				Frame(
					title: 'Text Size',
					child: SectionV(
						children: Array([
							SectionV(title: 'Document Text Size (relative to default)', children: Array([docSizeRow])),
							SectionV(title: 'Default Theme Text Size', children: Array([baseTextRow]))
						])
					)
				),
				Frame(
					title: 'UI Zoom',
					child: zoomSection
				)
			])
		);
	}

	Function is sync(){
		themeSection:setSelectedIndex(index: :presetIndex(preset: vm:model:themePreset));
		docDeltaInput:setText(next: vm:docDeltaLabel());
		baseTextInput:setText(next: vm:baseTextLabel());
		zoomSection:setSelectedIndex(index: :zoomIndex(pct: vm:model:uiZoomPct));
	}
}