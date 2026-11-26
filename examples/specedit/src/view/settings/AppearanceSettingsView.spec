#! Package specedit:view:settings
#! Appearance settings category view (Theme, Document Text Size, Default Theme Text Size, UI Zoom).

Class is AppearanceSettingsView{
	replace [String] is namespace: ['specedit', 'view', 'settings'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Column],
		['base', 'sew', Row],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', ScrapButton],
		['base', 'fabric', Theme],
		['base', 'fabric', ThemePreset],
		['specedit', 'viewmodel', SettingsViewModel]
	];

	SettingsViewModel is vm: SettingsViewModel();
	Array of ScrapButton is themeBtns: Array();
	Label is docDeltaVal: Label(text: '0 pt', minWidthPt: 52.0);
	Label is baseTextVal: Label(text: '12 pt', minWidthPt: 52.0);
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

		local Row is themeRow: Row(gapPt: 8.0);
		local Array of ThemePreset is presets: Theme:presets();
		local Int is ti: 0;
		while({ ti < presets:length() }, {
			local ThemePreset is p: presets:get(index: ti);
			local ScrapButton is btn: ScrapButton(
				label: Theme:presetLabel(preset: p),
				selected: (p == vm:model:themePreset),
				minWidthPt: 72.0,
				heightPt: 26.0,
				onClick: local Function(){ vm:selectTheme(preset: p); }
			);
			themeBtns:add(item: btn);
			themeRow:addChild(child: btn);
			ti: ti + 1;
		});

		local Row is docSizeRow: Row(
			gapPt: 8.0,
			children: Array([
				ScrapButton(
					label: '-',
					minWidthPt: 32.0,
					heightPt: 26.0,
					onClick: local Function(){ vm:adjustDocTextDelta(delta: -1.0); }
				),
				docDeltaVal,
				ScrapButton(
					label: '+',
					minWidthPt: 32.0,
					heightPt: 26.0,
					onClick: local Function(){ vm:adjustDocTextDelta(delta: 1.0); }
				),
				ScrapButton(
					label: 'Reset',
					minWidthPt: 56.0,
					heightPt: 26.0,
					onClick: local Function(){ vm:resetDocTextDelta(); }
				)
			])
		);

		local Row is baseTextRow: Row(
			gapPt: 8.0,
			children: Array([
				ScrapButton(
					label: '-',
					minWidthPt: 32.0,
					heightPt: 26.0,
					onClick: local Function(){ vm:adjustBaseTextPt(delta: -1.0); }
				),
				baseTextVal,
				ScrapButton(
					label: '+',
					minWidthPt: 32.0,
					heightPt: 26.0,
					onClick: local Function(){ vm:adjustBaseTextPt(delta: 1.0); }
				),
				ScrapButton(
					label: 'Reset',
					minWidthPt: 56.0,
					heightPt: 26.0,
					onClick: local Function(){ vm:resetBaseTextPt(); }
				)
			])
		);

		local Row is zoomRow: Row(gapPt: 8.0);
		local Int is zi: 0;
		while({ zi < zoomValues:length() }, {
			local Int is zp: zoomValues:get(index: zi);
			local ScrapButton is zBtn: ScrapButton(
				label: (zp as String) . '%',
				selected: (zp == vm:model:uiZoomPct),
				minWidthPt: 56.0,
				heightPt: 26.0,
				onClick: local Function(){ vm:selectZoomPct(pct: zp); }
			);
			zoomBtns:add(item: zBtn);
			zoomRow:addChild(child: zBtn);
			zi: zi + 1;
		});

		:sync();

		return Column(
			gapPt: 10.0,
			children: Array([
				Row(
					gapPt: 12.0,
					children: Array([
						Label(text: 'Appearance', heading: true),
						ScrapButton(
							label: 'Reset All',
							minWidthPt: 72.0,
							heightPt: 24.0,
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
					child: Column(
						gapPt: 6.0,
						children: Array([
							Label(text: 'Document Text Size (relative to default)', muted: true),
							docSizeRow,
							Label(text: 'Default Theme Text Size', muted: true),
							baseTextRow
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
		docDeltaVal:setText(text: vm:docDeltaLabel());
		baseTextVal:setText(text: vm:baseTextLabel());
		local Int is zi: 0;
		while({ zi < zoomValues:length() && zi < zoomBtns:length() }, {
			zoomBtns:get(index: zi):setSelected(next: zoomValues:get(index: zi) == vm:model:uiZoomPct);
			zi: zi + 1;
		});
	}
}