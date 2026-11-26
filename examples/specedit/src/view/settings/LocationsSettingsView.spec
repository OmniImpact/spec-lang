#! Package specedit:view:settings
#! Locations settings category view for managing pinned files and folders.

Class is LocationsSettingsView{
	replace [String] is namespace: ['specedit', 'view', 'settings'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Column],
		['base', 'sew', Row],
		['base', 'scrap', Frame],
		['base', 'scrap', ScrollView],
		['specedit', 'viewmodel', SettingsViewModel],
		['specedit', 'view', 'settings', SettingsLabel],
		['specedit', 'view', 'settings', SettingsChip]
	];

	SettingsViewModel is vm: SettingsViewModel();
	Column is listCol: Column(gapPt: 6.0);

	replace Function is init(SettingsViewModel is vm){
		:vm: vm;
		:listCol: Column(gapPt: 6.0);
	}

	Function of SewNode is build(){
		:listCol: Column(gapPt: 6.0);
		:sync();

		local Row is actionsRow: Row(
			gapPt: 8.0,
			children: Array([
				SettingsChip(
					label: 'Pin Current Folder',
					minWidthPt: 120.0,
					onClick: local Function(){ vm:pinCurrentDirectory(); }
				),
				SettingsChip(
					label: 'Pin Current File',
					minWidthPt: 110.0,
					onClick: local Function(){ vm:pinCurrentFile(); }
				)
			])
		);

		return Column(
			gapPt: 10.0,
			children: Array([
				SettingsLabel(text: 'Locations', heading: true),
				actionsRow,
				Frame(
					title: 'Pinned Files & Folders',
					child: ScrollView(child: listCol)
				)
			]),
			flexFlags: Array([false, false, true])
		);
	}

	Function is sync(){
		listCol:children: Array();
		listCol:flexFlags: Array();
		local Int is count: vm:pinned:paths:length();
		if({ count == 0 }, {
			listCol:addChild(child: SettingsLabel(text: 'No pinned locations.', muted: true));
			listCol:invalidate();
			return;
		});
		local Int is i: 0;
		while({ i < count }, {
			local Int is idx: i;
			local String is nm: vm:pinned:names:get(index: idx);
			local String is ppath: vm:pinned:paths:get(index: idx);
			local Row is row: Row(
				gapPt: 8.0,
				children: Array([
					SettingsChip(
						label: 'Remove',
						minWidthPt: 68.0,
						heightPt: 24.0,
						onClick: local Function(){ vm:removePinned(index: idx); }
					),
					SettingsLabel(text: nm . '  (' . ppath . ')')
				])
			);
			listCol:addChild(child: row);
			i: i + 1;
		});
		listCol:invalidate();
	}
}