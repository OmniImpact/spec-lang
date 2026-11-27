#! Package suitshowcase:view
#! Root view for SuitShowcase combining a left category sidebar, NavStack demo pane, and status bar.

Class is ShowcaseView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'signal', BoolEmitter],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'sew', Row],
		['base', 'sew', Padding],
		['base', 'sew', 'nav', NavStack],
		['base', 'sew', 'nav', NavRoute],
		['base', 'fabric', Theme],
		['base', 'scrap', Bar],
		['base', 'scrap', Frame],
		['base', 'scrap', ScrollView],
		['base', 'scrap', SectionV],
		['base', 'scrap', ToolkitContainer],
		['suitshowcase', 'viewmodel', ShowcaseViewModel],
		['suitshowcase', 'view', IntroPageView],
		['suitshowcase', 'view', ThemeBuilderPageView],
		['suitshowcase', 'view', GridPageView],
		['suitshowcase', 'view', ButtonsPageView],
		['suitshowcase', 'view', InputsPageView],
		['suitshowcase', 'view', SlidersPageView],
		['suitshowcase', 'view', BarsPageView],
		['suitshowcase', 'view', DropdownsPageView],
		['suitshowcase', 'view', ColorPageView],
		['suitshowcase', 'view', LinesBordersPageView],
		['suitshowcase', 'view', FillEffectsPageView],
		['suitshowcase', 'view', DateTimePageView],
		['suitshowcase', 'view', TextStylesPageView],
		['suitshowcase', 'view', TextTreePageView]
	];

	Array of String is categoryRoutes: Array(['intro', 'theme', 'grid', 'buttons', 'inputs', 'sliders', 'bars', 'dropdowns', 'colors', 'datetime', 'textstyles', 'lines', 'fills', 'text']);

	local Function of Int is routeIndex(String is routeName){
		local Int is i: 0;
		while({ i < categoryRoutes:length() }, {
			if({ categoryRoutes:get(index: i) == routeName }, { return i; });
			i: i + 1;
		});
		return 0;
	}

	Function of ToolkitContainer is build(ShowcaseViewModel is vm){
		local IntroPageView is introPage: IntroPageView(vm: vm);
		local ThemeBuilderPageView is themePage: ThemeBuilderPageView(vm: vm);
		local GridPageView is gridPage: GridPageView(vm: vm);
		local ButtonsPageView is buttonsPage: ButtonsPageView(vm: vm);
		local InputsPageView is inputsPage: InputsPageView(vm: vm);
		local SlidersPageView is slidersPage: SlidersPageView(vm: vm);
		local BarsPageView is barsPage: BarsPageView(vm: vm);
		local DropdownsPageView is dropdownsPage: DropdownsPageView(vm: vm);
		local ColorPageView is colorPage: ColorPageView(vm: vm);
		local LinesBordersPageView is linesPage: LinesBordersPageView(vm: vm);
		local FillEffectsPageView is fillsPage: FillEffectsPageView(vm: vm);
		local DateTimePageView is dateTimePage: DateTimePageView(vm: vm);
		local TextStylesPageView is textStylesPage: TextStylesPageView(vm: vm);
		local TextTreePageView is textPage: TextTreePageView(vm: vm);

		local NavStack is navStack: NavStack(
			route: vm:selectedRoute,
			routes: Array([
				NavRoute(name: 'intro', child: ScrollView(child: Padding(useThemePad: true, child: introPage:build()))),
				NavRoute(name: 'theme', child: ScrollView(child: Padding(useThemePad: true, child: themePage:build()))),
				NavRoute(name: 'grid', child: ScrollView(child: Padding(useThemePad: true, child: gridPage:build()))),
				NavRoute(name: 'buttons', child: ScrollView(child: Padding(useThemePad: true, child: buttonsPage:build()))),
				NavRoute(name: 'inputs', child: ScrollView(child: Padding(useThemePad: true, child: inputsPage:build()))),
				NavRoute(name: 'sliders', child: ScrollView(child: Padding(useThemePad: true, child: slidersPage:build()))),
				NavRoute(name: 'bars', child: ScrollView(child: Padding(useThemePad: true, child: barsPage:build()))),
				NavRoute(name: 'dropdowns', child: ScrollView(child: Padding(useThemePad: true, child: dropdownsPage:build()))),
				NavRoute(name: 'colors', child: ScrollView(allowHScroll: true, child: Padding(useThemePad: true, child: colorPage:build()))),
				NavRoute(name: 'datetime', child: ScrollView(allowHScroll: true, child: Padding(useThemePad: true, child: dateTimePage:build()))),
				NavRoute(name: 'textstyles', child: ScrollView(child: Padding(useThemePad: true, child: textStylesPage:build()))),
				NavRoute(name: 'lines', child: ScrollView(child: Padding(useThemePad: true, child: linesPage:build()))),
				NavRoute(name: 'fills', child: ScrollView(child: Padding(useThemePad: true, child: fillsPage:build()))),
				NavRoute(name: 'text', child: ScrollView(child: Padding(useThemePad: true, child: textPage:build())))
			])
		);

		local SectionV is sidebar: SectionV(
			segmented: true,
			options: Array(['Intro', 'Theme Builder', 'Grid Layout', 'Buttons & Sections', 'Inputs & Toggles', 'Sliders', 'Bars & Toolbars', 'Dropdowns', 'Color Selector', 'Date & Time', 'Text Styles', 'Lines & Borders', 'Fill & Effects', 'Text & Tree']),
			selectedIndex: :routeIndex(routeName: vm:selectedRoute:current()),
			itemMinWidthPt: 132.0,
			itemHeightPt: 24.0,
			onSelect: local Function(Int is idx){
				if({ idx >= 0 && idx < categoryRoutes:length() }, {
					vm:selectRoute(routeName: categoryRoutes:get(index: idx));
				});
			}
		);

		local SewNode is body: Padding(
			useThemePad: true,
			padScale: 1.25,
			child: Row(
				gapPt: 10.0,
				children: Array([
					ScrollView(child: sidebar, fitContentWidth: true),
					Frame(padPt: 0.0, child: navStack)
				]),
				flexFlags: Array([false, true])
			)
		);

		local String is appIconSvg: "<svg viewBox=\"0 0 24 24\"><rect x=\"2\" y=\"2\" width=\"20\" height=\"20\" rx=\"4\" fill=\"#2a3346\" stroke=\"#64d2ff\" stroke-width=\"1.6\"/><rect x=\"5\" y=\"5\" width=\"14\" height=\"3.5\" rx=\"1\" fill=\"#64d2ff\"/><rect x=\"5\" y=\"10.5\" width=\"5.5\" height=\"8.5\" rx=\"1\" fill=\"#8fa8c8\"/><rect x=\"12.5\" y=\"10.5\" width=\"6.5\" height=\"3.5\" rx=\"1\" fill=\"#e8edf5\"/><rect x=\"12.5\" y=\"15.5\" width=\"6.5\" height=\"3.5\" rx=\"1\" fill=\"#64d2ff\"/></svg>";

		local ToolkitContainer is container: ToolkitContainer(
			title: TextEmitter(initial: 'SuitShowcase'),
			iconSvg: appIconSvg,
			running: BoolEmitter(initial: true),
			theme: vm:activeTheme,
			widthPt: 760.0,
			heightPt: 520.0,
			hasToolbar: false,
			body: body,
			bottomBar: Bar(leftText: vm:statusText),
			hasBottomBar: true
		);

		vm:bindThemeApply(onThemeApply: local Function(Theme is t){
			container:setTheme(nextTheme: t);
		});
		vm:bindAlphaApply(onAlphaApply: local Function(Int is pct){
			container:setWindowAlphaPct(pct: pct);
		});
		vm:bindRefresh(onRefresh: local Function(){
			sidebar:setSelectedIndex(index: :routeIndex(routeName: vm:selectedRoute:current()));
			themePage:sync();
			buttonsPage:sync();
			inputsPage:sync();
			slidersPage:sync();
			navStack:invalidate();
			container:isDirty: true;
		});

		return container;
	}
}
