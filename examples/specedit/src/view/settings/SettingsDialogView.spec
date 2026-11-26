#! Package specedit:view:settings
#! Top-level Settings dialog combining left category sidebar and a NavStack right pane.

Class is SettingsDialogView{
	replace [String] is namespace: ['specedit', 'view', 'settings'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Column],
		['base', 'sew', Row],
		['base', 'sew', Padding],
		['base', 'sew', 'nav', NavStack],
		['base', 'sew', 'nav', NavRoute],
		['base', 'scrap', Dialog],
		['base', 'scrap', ScrapButton],
		['specedit', 'viewmodel', SettingsViewModel],
		['specedit', 'view', 'settings', SettingsChip],
		['specedit', 'view', 'settings', AppearanceSettingsView],
		['specedit', 'view', 'settings', LocationsSettingsView],
		['specedit', 'view', 'settings', InterfaceSettingsView]
	];

	SettingsViewModel is vm: SettingsViewModel();
	AppearanceSettingsView is appearanceView: AppearanceSettingsView(vm: SettingsViewModel());
	LocationsSettingsView is locationsView: LocationsSettingsView(vm: SettingsViewModel());
	InterfaceSettingsView is interfaceView: InterfaceSettingsView(vm: SettingsViewModel());
	Array of String is categoryRoutes: Array(['appearance', 'locations', 'interface']);
	Array of SettingsChip is categoryChips: Array();
	NavStack is navStack: NavStack();
	Dialog is dlg: Dialog();

	replace Function is init(SettingsViewModel is vm){
		:vm: vm;
		:appearanceView: AppearanceSettingsView(vm: vm);
		:locationsView: LocationsSettingsView(vm: vm);
		:interfaceView: InterfaceSettingsView(vm: vm);
		:categoryChips: Array();
		:navStack: NavStack();
	}

	Function of Dialog is build(){
		:navStack: NavStack(
			route: vm:selectedRoute,
			routes: Array([
				NavRoute(name: 'appearance', child: appearanceView:build()),
				NavRoute(name: 'locations', child: locationsView:build()),
				NavRoute(name: 'interface', child: interfaceView:build())
			])
		);

		local String is curRoute: vm:selectedRoute:current();
		:categoryChips: Array([
			SettingsChip(
				label: 'Appearance',
				selected: (curRoute == 'appearance'),
				minWidthPt: 132.0,
				heightPt: 32.0,
				onClick: local Function(){ vm:selectRoute(routeName: 'appearance'); }
			),
			SettingsChip(
				label: 'Locations',
				selected: (curRoute == 'locations'),
				minWidthPt: 132.0,
				heightPt: 32.0,
				onClick: local Function(){ vm:selectRoute(routeName: 'locations'); }
			),
			SettingsChip(
				label: 'Interface',
				selected: (curRoute == 'interface'),
				minWidthPt: 132.0,
				heightPt: 32.0,
				onClick: local Function(){ vm:selectRoute(routeName: 'interface'); }
			)
		]);

		local Column is sidebar: Column(
			gapPt: 8.0,
			children: Array([
				categoryChips:get(index: 0),
				categoryChips:get(index: 1),
				categoryChips:get(index: 2)
			])
		);

		local Row is bodyRow: Row(
			gapPt: 16.0,
			children: Array([
				sidebar,
				navStack
			]),
			flexFlags: Array([false, true])
		);

		local Row is footerRow: Row(
			gapPt: 8.0,
			children: Array([
				ScrapButton(
					label: 'Close',
					minWidthPt: 84.0,
					heightPt: 30.0,
					onClick: local Function(){ vm:closeSettings(); }
				)
			])
		);

		local Column is root: Column(
			gapPt: 12.0,
			children: Array([
				bodyRow,
				footerRow
			]),
			flexFlags: Array([true, false])
		);

		:dlg: Dialog(
			title: 'Settings',
			open: vm:open,
			widthPt: 640.0,
			heightPt: 420.0,
			minWidthPt: 500.0,
			minHeightPt: 340.0,
			content: Padding(padPt: 16.0, child: root)
		);

		vm:bindViewRefresh(onRefresh: local Function(){
			:sync();
			dlg:isDirty: true;
		});

		return dlg;
	}

	Function is sync(){
		local String is curRoute: vm:selectedRoute:current();
		local Int is i: 0;
		while({ i < categoryRoutes:length() && i < categoryChips:length() }, {
			categoryChips:get(index: i):setSelected(next: categoryRoutes:get(index: i) == curRoute);
			i: i + 1;
		});
		appearanceView:sync();
		locationsView:sync();
		interfaceView:sync();
		navStack:invalidate();
	}
}