#! Package specedit:view:settings
#! Locations settings category view using VSection and HSection.

Class is LocationsSettingsView{
	replace [String] is namespace: ['specedit', 'view', 'settings'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', VSection],
		['base', 'scrap', HSection],
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

		local HSection is actionsRow: HSection(
			children: Array([
				ScrapButton(
					label: 'Add Location',
					minWidthPt: 96.0,
					onClick: local Function(){ vm:requestAddLocation(); }
				)
			])
		);

		return VSection(
			children: Array([
				Label(text: 'Locations', heading: true),
				actionsRow,
				Frame(
					title: 'Pinned Locations (drag gripper to reorder)',
					child: listView
				)
			]),
			flexFlags: Array([false, false, false])
		);
	}

	Function is sync(){
		listView:invalidate();
	}
}