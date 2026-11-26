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
		['base', 'fabric', Theme],
		['base', 'fabric', ThemePreset],
		['specedit', 'viewmodel', SettingsViewModel],
		['specedit', 'view', 'settings', SettingsLabel],
		['specedit', 'view', 'settings', SettingsChip]
	];

	SettingsViewModel is vm: SettingsViewModel();
	Array of SettingsChip is themeChips: Array();
	SettingsLabel is docDeltaVal: SettingsLabel(text: '0 pt', minWidthPt: 58.0);
	SettingsLabel is baseTextVal: SettingsLabel(text: '15 pt', minWidthPt: 58.0);
	Array of Int is zoomValues: Array([70, 100, 115, 130]);
	Array of SettingsChip is zoomChips: Array();

	replace Function is init(SettingsViewModel is vm){
		:vm: vm;
		:themeChips: Array();
		:zoomChips: Array();
	}

	Function of SewNode is build(){
		:themeChips: Array();
		:zoomChips: Array();

		local Row is themeRow: Row(gapPt: 8.0);
		local Array of ThemePreset is presets: Theme:presets();
		local Int is ti: 0;
		while({ ti < presets:length() }, {
			local ThemePreset is p: presets:get(index: ti);
			local SettingsChip is chip: SettingsChip(
				label: Theme:presetLabel(preset: p),
				selected: (p == vm:model:themePreset),
				minWidthPt: 76.0,
				onClick: local Function(){ vm:selectTheme(preset: p); }
			);
			themeChips:add(item: chip);
			themeRow:addChild(child: chip);
			ti: ti + 1;
		});

		local Row is docSizeRow: Row(
			gapPt: 8.0,
			children: Array([
				SettingsChip(
					label: '-',
					minWidthPt: 34.0,
					onClick: local Function(){ vm:adjustDocTextDelta(delta: -1.0); }
				),
				docDeltaVal,
				SettingsChip(
					label: '+',
					minWidthPt: 34.0,
					onClick: local Function(){ vm:adjustDocTextDelta(delta: 1.0); }
				),
				SettingsChip(
					label: 'Reset',
					minWidthPt: 58.0,
					onClick: local Function(){ vm:resetDocTextDelta(); }
				)
			])
		);

		local Row is baseTextRow: Row(
			gapPt: 8.0,
			children: Array([
				SettingsChip(
					label: '-',
					minWidthPt: 34.0,
					onClick: local Function(){ vm:adjustBaseTextPt(delta: -1.0); }
				),
				baseTextVal,
				SettingsChip(
					label: '+',
					minWidthPt: 34.0,
					onClick: local Function(){ vm:adjustBaseTextPt(delta: 1.0); }
				),
				SettingsChip(
					label: 'Reset',
					minWidthPt: 58.0,
					onClick: local Function(){ vm:resetBaseTextPt(); }
				)
			])
		);

		local Row is zoomRow: Row(gapPt: 8.0);
		local Int is zi: 0;
		while({ zi < zoomValues:length() }, {
			local Int is zp: zoomValues:get(index: zi);
			local SettingsChip is zChip: SettingsChip(
				label: (zp as String) . '%',
				selected: (zp == vm:model:uiZoomPct),
				minWidthPt: 60.0,
				onClick: local Function(){ vm:selectZoomPct(pct: zp); }
			);
			zoomChips:add(item: zChip);
			zoomRow:addChild(child: zChip);
			zi: zi + 1;
		});

		:sync();

		return Column(
			gapPt: 10.0,
			children: Array([
				Row(
					gapPt: 12.0,
					children: Array([
						SettingsLabel(text: 'Appearance', heading: true),
						SettingsChip(
							label: 'Reset All',
							minWidthPt: 76.0,
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
							SettingsLabel(text: 'Document Text Size (relative to default)', muted: true),
							docSizeRow,
							SettingsLabel(text: 'Default Theme Text Size', muted: true),
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
		while({ i < presets:length() && i < themeChips:length() }, {
			themeChips:get(index: i):setSelected(next: presets:get(index: i) == vm:model:themePreset);
			i: i + 1;
		});
		docDeltaVal:setText(next: vm:docDeltaLabel());
		baseTextVal:setText(next: vm:baseTextLabel());
		local Int is zi: 0;
		while({ zi < zoomValues:length() && zi < zoomChips:length() }, {
			zoomChips:get(index: zi):setSelected(next: zoomValues:get(index: zi) == vm:model:uiZoomPct);
			zi: zi + 1;
		});
	}
}