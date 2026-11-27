#! Package suitshowcase:view
#! Showcase page exercising Toolbar, TabBar, Bar, and ScrapPanel widgets.

Class is BarsPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'fabric', TextStyle],
		['base', 'scrap', Bar],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', ScrapButton],
		['base', 'scrap', ScrapPanel],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['base', 'scrap', 'menu', MenuConfig],
		['base', 'scrap', 'menu', MenuItemConfig],
		['base', 'scrap', 'menu', MenuItemKind],
		['base', 'scrap', 'toolbar', Toolbar],
		['base', 'scrap', 'toolbar', ToolbarConfig],
		['base', 'scrap', 'tab', TabBar],
		['base', 'scrap', 'tab', TabItemConfig],
		['base', 'scrap', 'text', TextScrap],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();
	TextEmitter is barActionText: TextEmitter(initial: 'Interact with the Toolbar, TabBar, or Bar above');
	TextEmitter is barRightText: TextEmitter(initial: 'Spec (Click)');
	TabBar is demoTabs: TabBar();
	Int is nextTabNum: 4;

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
	}

	Function of SewNode is build(){
		local ToolbarConfig is tbCfg: ToolbarConfig(
			menus: Array([
				MenuConfig(id: 'file', label: 'File', items: Array([
					MenuItemConfig(id: 'new', label: 'New Item', onClick: local Function(){ barActionText:emit(value: 'Toolbar: File -> New Item'); }),
					MenuItemConfig(id: 'open', label: 'Open...', onClick: local Function(){ barActionText:emit(value: 'Toolbar: File -> Open...'); })
				])),
				MenuConfig(id: 'view', label: 'View', items: Array([
					MenuItemConfig(id: 'grid', label: 'Show Grid', kind: MenuItemKind:TOGGLE, checked: true, onClick: local Function(){ barActionText:emit(value: 'Toolbar: View -> Show Grid'); }),
					MenuItemConfig(id: 'snap', label: 'Snap to Bounds', kind: MenuItemKind:TOGGLE, checked: false, onClick: local Function(){ barActionText:emit(value: 'Toolbar: View -> Snap to Bounds'); })
				])),
				MenuConfig(id: 'mode', label: 'Mode', items: Array([
					MenuItemConfig(id: 'm1', label: 'Design', kind: MenuItemKind:RADIO, checked: true, onClick: local Function(){ barActionText:emit(value: 'Toolbar: Mode -> Design'); }),
					MenuItemConfig(id: 'm2', label: 'Inspect', kind: MenuItemKind:RADIO, checked: false, onClick: local Function(){ barActionText:emit(value: 'Toolbar: Mode -> Inspect'); })
				]))
			])
		);
		local Toolbar is demoToolbar: Toolbar(config: tbCfg);

		:demoTabs: TabBar(
			tabs: Array([
				TabItemConfig(id: 't1', label: 'Main.spec', closable: true),
				TabItemConfig(id: 't2', label: 'Theme.spec', closable: true),
				TabItemConfig(id: 't3', label: 'README.md', closable: false)
			]),
			activeIndex: 0,
			onSelectTab: local Function(Int is idx){
				demoTabs:selectTab(index: idx);
				barActionText:emit(value: 'Selected tab index ' . (idx as String));
			},
			onCloseTab: local Function(Int is idx){
				demoTabs:removeTab(index: idx);
				barActionText:emit(value: 'Closed tab index ' . (idx as String));
			},
			onReorderTab: local Function(Int is fromIdx, Int is toIdx){
				barActionText:emit(value: 'Reordered tab ' . (fromIdx as String) . ' -> ' . (toIdx as String));
			}
		);

		local Bar is staticBar: Bar(
			leftText: TextEmitter(initial: 'Ln 12, Col 4'),
			centerText: TextEmitter(initial: 'UTF-8'),
			rightText: TextEmitter(initial: 'Ready')
		);

		local Bar is interactiveBar: Bar(
			leftText: TextEmitter(initial: 'Interactive Bar'),
			rightText: barRightText,
			rightInteractive: true,
			onRightClick: local Function(Int is _x, Int is _y){
				barActionText:emit(value: 'Clicked interactive Bar right trigger');
			}
		);

		return SectionV(
			children: Array([
				Label(text: 'Bars & Toolbars', style: TextStyle:H1),
				Frame(
					title: 'Toolbar (Menu Triggers & Dropdowns)',
					child: Frame(padPt: 0.0, child: demoToolbar)
				),
				Frame(
					title: 'TabBar (Selectable & Closable Tabs)',
					child: SectionV(
						children: Array([
							Frame(padPt: 0.0, child: demoTabs),
							ScrapButton(
								label: 'Add Tab',
								onClick: local Function(){
									demoTabs:addTab(
										tab: TabItemConfig(id: 't' . (nextTabNum as String), label: 'Tab ' . (nextTabNum as String) . '.spec', closable: true),
										activate: true
									);
									:nextTabNum: nextTabNum + 1;
									barActionText:emit(value: 'Added new tab');
								}
							)
						])
					)
				),
				Frame(
					title: 'Status Bar Variants',
					child: SectionV(
						children: Array([
							Frame(padPt: 0.0, child: staticBar),
							Frame(padPt: 0.0, child: interactiveBar)
						])
					)
				),
				Frame(
					title: 'ScrapPanel Surface',
					child: ScrapPanel(heightPt: 28.0)
				),
				TextScrap(text: barActionText, muted: true)
			])
		);
	}
}
