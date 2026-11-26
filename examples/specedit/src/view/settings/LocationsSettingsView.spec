#! Package specedit:view:settings
#! Locations settings category view for adding, removing, and drag-reordering pinned directories.

Class is LocationsSettingsView{
	replace [String] is namespace: ['specedit', 'view', 'settings'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Column],
		['base', 'sew', Row],
		['base', 'scrap', Frame],
		['base', 'scrap', ScrollView],
		['specedit', 'viewmodel', SettingsViewModel],
		['specedit', 'view', 'settings', SettingsLabel],
		['specedit', 'view', 'settings', SettingsChip],
		['specedit', 'view', 'settings', PinnedLocationsList]
	];

	SettingsViewModel is vm: SettingsViewModel();
	PinnedLocationsList is listView: PinnedLocationsList(vm: SettingsViewModel());

	replace Function is init(SettingsViewModel is vm){
		:vm: vm;
		:listView: PinnedLocationsList(vm: vm);
	}

	Function of SewNode is build(){
		:listView: PinnedLocationsList(vm: vm);

		local Row is actionsRow: Row(
			gapPt: 8.0,
			children: Array([
				SettingsChip(
					label: 'Add Location',
					minWidthPt: 112.0,
					onClick: local Function(){ vm:requestAddLocation(); }
				),
				SettingsChip(
					label: 'Pin Current Folder',
					minWidthPt: 124.0,
					onClick: local Function(){ vm:pinCurrentDirectory(); }
				)
			])
		);

		return Column(
			gapPt: 10.0,
			children: Array([
				SettingsLabel(text: 'Locations', heading: true),
				actionsRow,
				Frame(
					title: 'Pinned Locations (drag gripper to reorder)',
					child: ScrollView(child: listView)
				)
			]),
			flexFlags: Array([false, false, true])
		);
	}

	Function is sync(){
		listView:invalidate();
	}
}