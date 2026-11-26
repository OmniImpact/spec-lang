#! Package specedit:view:settings
#! Appearance settings category view using VSection, HSection, and DecoratedTextInput.

Class is AppearanceSettingsView{
	replace [String] is namespace: ['specedit', 'view', 'settings'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', VSection],
		['base', 'scrap', HSection],
		['base', 'scrap', DecoratedTextInput],
		['base', 'fabric', Theme],
		['base', 'fabric', ThemePreset],
		['specedit', 'viewmodel', SettingsViewModel]
	];

	SettingsViewModel is vm: SettingsViewModel();
	Array of ScrapButton is themeBtns: Array();
	DecoratedTextInput is docDeltaInput: DecoratedTextInput();
	DecoratedTextInput is baseTextInput: DecoratedTextInput();
	Array of Int is zoomValues: Array([70, 100, 115, 130]);
	Array of ScrapButton is zoomBtns: Array();

	replace Function is init(SettingsViewModel is vm){
		:vm: vm;
		:themeBtns: Array();
		:zoomBtns: Array();
	}

	Function of SewNode is build(){
		:themeBtns: Array();
		:zoomBtns: Array();

		local HSection is themeRow: HSection();
		local Array of ThemePreset is presets: Theme:presets();
		local Int is ti: 0;
		while({ ti < presets:length() }, {
			local ThemePreset is p: presets:get(index: ti);
			local ScrapButton is btn: ScrapButton(
				label: Theme:presetLabel(preset: p),
				selected: (p == vm:model:themePreset),
				minWidthPt: 64.0,
				onClick: local Function(){ vm:selectTheme(preset: p); }
			);
			themeBtns:add(item: btn);
			themeRow:row:addChild(child: btn);
			ti: ti + 1;
		});

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

		local HSection is docSizeRow: HSection(
			children: Array([
				docDeltaInput,
				ScrapButton(
					label: 'Reset',
					minWidthPt: 50.0,
					onClick: local Function(){ vm:resetDocTextDelta(); }
				)
			])
		);

		local HSection is baseTextRow: HSection(
			children: Array([
				baseTextInput,
				ScrapButton(
					label: 'Reset',
					minWidthPt: 50.0,
					onClick: local Function(){ vm:resetBaseTextPt(); }
				)
			])
		);

		local HSection is zoomRow: HSection();
		local Int is zi: 0;
		while({ zi < zoomValues:length() }, {
			local Int is zp: zoomValues:get(index: zi);
			local ScrapButton is zBtn: ScrapButton(
				label: (zp as String) . '%',
				selected: (zp == vm:model:uiZoomPct),
				minWidthPt: 48.0,
				onClick: local Function(){ vm:selectZoomPct(pct: zp); }
			);
			zoomBtns:add(item: zBtn);
			zoomRow:row:addChild(child: zBtn);
			zi: zi + 1;
		});

		:sync();

		return VSection(
			children: Array([
				HSection(
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
					child: themeRow
				),
				Frame(
					title: 'Text Size',
					child: VSection(
						children: Array([
							VSection(title: 'Document Text Size (relative to default)', children: Array([docSizeRow])),
							VSection(title: 'Default Theme Text Size', children: Array([baseTextRow]))
						])
					)
				),
				Frame(
					title: 'UI Zoom',
					child: zoomRow
				)
			])
		);
	}

	Function is sync(){
		local Array of ThemePreset is presets: Theme:presets();
		local Int is i: 0;
		while({ i < presets:length() && i < themeBtns:length() }, {
			themeBtns:get(index: i):setSelected(next: presets:get(index: i) == vm:model:themePreset);
			i: i + 1;
		});
		docDeltaInput:setText(next: vm:docDeltaLabel());
		baseTextInput:setText(next: vm:baseTextLabel());
		local Int is zi: 0;
		while({ zi < zoomValues:length() && zi < zoomBtns:length() }, {
			zoomBtns:get(index: zi):setSelected(next: zoomValues:get(index: zi) == vm:model:uiZoomPct);
			zi: zi + 1;
		});
	}
}