#! Package specedit:view:settings
#! Locations settings category view using Row, Column, Frame, and PinnedLocationsList.

Class is LocationsSettingsView{
	replace [String] is namespace: ['specedit', 'view', 'settings'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Column],
		['base', 'sew', Row],
		['base', 'fabric', TextStyle],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', ScrapButton],
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

		local Row is headerRow: Row(
			gapPt: 8.0,
			flexFlags: Array([true, false]),
			children: Array([
				Label(text: 'Locations', heading: true),
				Row(
					gapPt: 6.0,
					children: Array([
						ScrapButton(
							label: 'Pin Current Folder',
							minWidthPt: 110.0,
							tooltip: 'Pin the currently open folder to quick-access locations',
							onClick: local Function(){ vm:pinCurrentDirectory(); }
						),
						ScrapButton(
							label: 'Add Location...',
							minWidthPt: 96.0,
							tooltip: 'Browse for a folder to pin',
							onClick: local Function(){ vm:requestAddLocation(); }
						)
					])
				)
			])
		);

		return Column(
			gapPt: 10.0,
			children: Array([
				headerRow,
				Frame(
					title: 'Pinned Locations',
					fillBg: true,
					padPt: 4.0,
					child: listView
				),
				Label(
					text: 'Drag a row by its gripper handle to reorder pinned folders.',
					style: TextStyle:CAPTION,
					muted: true
				)
			])
		);
	}

	Function is sync(){
		listView:invalidate();
	}
}