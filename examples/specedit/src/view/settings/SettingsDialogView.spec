#! Package specedit:view:settings
#! Top-level Settings dialog (subclass of Dialog) combining left category sidebar and NavStack pane.

Class of Dialog is SettingsDialogView{
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
		['specedit', 'view', 'settings', AppearanceSettingsView],
		['specedit', 'view', 'settings', LocationsSettingsView],
		['specedit', 'view', 'settings', InterfaceSettingsView]
	];

	SettingsViewModel is vm: SettingsViewModel();
	AppearanceSettingsView is appearanceView: AppearanceSettingsView(vm: SettingsViewModel());
	LocationsSettingsView is locationsView: LocationsSettingsView(vm: SettingsViewModel());
	InterfaceSettingsView is interfaceView: InterfaceSettingsView(vm: SettingsViewModel());
	Array of String is categoryRoutes: Array(['appearance', 'locations', 'interface']);
	Array of ScrapButton is categoryBtns: Array();
	NavStack is navStack: NavStack();

	replace Function is init(SettingsViewModel is vm){
		:vm: vm;
		:title: 'Settings';
		:open: vm:open;
		:widthPt: 480.0;
		:heightPt: 330.0;
		:minWidthPt: 400.0;
		:minHeightPt: 270.0;
		:hasContent: true;
		:appearanceView: AppearanceSettingsView(vm: vm);
		:locationsView: LocationsSettingsView(vm: vm);
		:interfaceView: InterfaceSettingsView(vm: vm);
		:categoryBtns: Array();
		:navStack: NavStack();
		:content: :buildContent();
		:onTick: local Function(Int is _ms){
			if({ vm:stepPending() }, {
				:isDirty: true;
			});
		};
		vm:bindViewRefresh(onRefresh: local Function(){
			:sync();
			:isDirty: true;
		});
	}

	local Function of SewNode is buildContent(){
		:navStack: NavStack(
			route: vm:selectedRoute,
			routes: Array([
				NavRoute(name: 'appearance', child: appearanceView:build()),
				NavRoute(name: 'locations', child: locationsView:build()),
				NavRoute(name: 'interface', child: interfaceView:build())
			])
		);

		local String is curRoute: vm:selectedRoute:current();
		:categoryBtns: Array([
			ScrapButton(
				label: 'Appearance',
				selected: (curRoute == 'appearance'),
				minWidthPt: 96.0,
				heightPt: 22.0,
				onClick: local Function(){ vm:selectRoute(routeName: 'appearance'); }
			),
			ScrapButton(
				label: 'Locations',
				selected: (curRoute == 'locations'),
				minWidthPt: 96.0,
				heightPt: 22.0,
				onClick: local Function(){ vm:selectRoute(routeName: 'locations'); }
			),
			ScrapButton(
				label: 'Interface',
				selected: (curRoute == 'interface'),
				minWidthPt: 96.0,
				heightPt: 22.0,
				onClick: local Function(){ vm:selectRoute(routeName: 'interface'); }
			)
		]);

		local Column is sidebar: Column(
			gapPt: 5.0,
			children: Array([
				categoryBtns:get(index: 0),
				categoryBtns:get(index: 1),
				categoryBtns:get(index: 2)
			])
		);

		local Row is bodyRow: Row(
			gapPt: 10.0,
			children: Array([
				sidebar,
				navStack
			]),
			flexFlags: Array([false, true])
		);

		local Row is footerRow: Row(
			gapPt: 6.0,
			children: Array([
				ScrapButton(
					label: 'Close',
					minWidthPt: 64.0,
					heightPt: 22.0,
					onClick: local Function(){ vm:closeSettings(); }
				)
			])
		);

		local Column is root: Column(
			gapPt: 8.0,
			children: Array([
				bodyRow,
				footerRow
			]),
			flexFlags: Array([true, false])
		);

		return Padding(useThemePad: true, padScale: 1.5, child: root);
	}

	Function is sync(){
		local String is curRoute: vm:selectedRoute:current();
		local Int is i: 0;
		while({ i < categoryRoutes:length() && i < categoryBtns:length() }, {
			categoryBtns:get(index: i):setSelected(next: categoryRoutes:get(index: i) == curRoute);
			i: i + 1;
		});
		appearanceView:sync();
		locationsView:sync();
		interfaceView:sync();
		navStack:invalidate();
	}
}