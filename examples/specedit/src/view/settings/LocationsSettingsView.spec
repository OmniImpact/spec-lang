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
		['base', 'scrap', Label],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', ScrollView],
		['specedit', 'viewmodel', SettingsViewModel],
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
				ScrapButton(
					label: 'Add Location',
					minWidthPt: 108.0,
					heightPt: 26.0,
					onClick: local Function(){ vm:requestAddLocation(); }
				),
				ScrapButton(
					label: 'Pin Current Folder',
					minWidthPt: 120.0,
					heightPt: 26.0,
					onClick: local Function(){ vm:pinCurrentDirectory(); }
				)
			])
		);

		return Column(
			gapPt: 10.0,
			children: Array([
				Label(text: 'Locations', heading: true),
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