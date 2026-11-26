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
		['base', 'scrap', Clickable],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', ScrollView],
		['base', 'scrap', Frame],
		['base', 'scrap', SectionV],
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
	SectionV is categorySection: SectionV();
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
		:categorySection: SectionV();
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

	local Function of Int is routeIndex(String is routeName){
		local Int is i: 0;
		while({ i < categoryRoutes:length() }, {
			if({ categoryRoutes:get(index: i) == routeName }, { return i; });
			i: i + 1;
		});
		return 0;
	}

	local Function of SewNode is buildContent(){
		:navStack: NavStack(
			route: vm:selectedRoute,
			routes: Array([
				NavRoute(name: 'appearance', child: ScrollView(child: Padding(useThemePad: true, child: appearanceView:build()))),
				NavRoute(name: 'locations', child: ScrollView(child: Padding(useThemePad: true, child: locationsView:build()))),
				NavRoute(name: 'interface', child: ScrollView(child: Padding(useThemePad: true, child: interfaceView:build())))
			])
		);

		:categorySection: SectionV(
			segmented: true,
			options: Array(['Appearance', 'Locations', 'Interface']),
			selectedIndex: :routeIndex(routeName: vm:selectedRoute:current()),
			itemMinWidthPt: 96.0,
			itemHeightPt: 22.0,
			onSelect: local Function(Int is idx){
				vm:selectRoute(routeName: categoryRoutes:get(index: idx));
			}
		);

		local Row is bodyRow: Row(
			gapPt: 10.0,
			children: Array([
				categorySection,
				Frame(padPt: 0.0, child: navStack)
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
		categorySection:setSelectedIndex(index: :routeIndex(routeName: vm:selectedRoute:current()));
		appearanceView:sync();
		locationsView:sync();
		interfaceView:sync();
		navStack:invalidate();
	}
}