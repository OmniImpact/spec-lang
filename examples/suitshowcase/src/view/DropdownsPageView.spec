#! Package suitshowcase:view
#! Dedicated showcase page highlighting dropdown widgets: ColorSwatchDropdown variants and Toolbar menu dropdowns.

Class is DropdownsPageView{
	replace [String] is namespace: ['suitshowcase', 'view'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'sew', SewNode],
		['base', 'fabric', Color],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', ColorSwatchDropdown],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['base', 'scrap', 'menu', MenuConfig],
		['base', 'scrap', 'menu', MenuItemConfig],
		['base', 'scrap', 'toolbar', Toolbar],
		['base', 'scrap', 'toolbar', ToolbarConfig],
		['base', 'scrap', 'text', TextScrap],
		['suitshowcase', 'viewmodel', ShowcaseViewModel]
	];

	ShowcaseViewModel is vm: ShowcaseViewModel();
	TextEmitter is statusLabel: TextEmitter(initial: 'Open any dropdown below to inspect floating overlay behavior');

	replace Function is init(ShowcaseViewModel is vm){
		:vm: vm;
	}

	Function of SewNode is build(){
		local Color is c1: Color(r: 66, g: 133, b: 244);
		local Color is c2: Color(r: 76, g: 175, b: 80);
		local Color is c3: Color(r: 239, g: 83, b: 80);

		local Toolbar is menuBar: Toolbar(
			config: ToolbarConfig(
				menus: Array([
					MenuConfig(
						id: 'actions',
						label: 'Actions',
						items: Array([
							MenuItemConfig(id: 'a1', label: 'Run Action', onClick: local Function(){ statusLabel:emit(value: 'Menu: Run Action'); }),
							MenuItemConfig(
								id: 'sub',
								label: 'More Options',
								subItems: Array([
									MenuItemConfig(id: 's1', label: 'Sub-item Alpha', onClick: local Function(){ statusLabel:emit(value: 'Menu: Sub-item Alpha'); }),
									MenuItemConfig(id: 's2', label: 'Sub-item Beta', onClick: local Function(){ statusLabel:emit(value: 'Menu: Sub-item Beta'); })
								])
							)
						])
					),
					MenuConfig(
						id: 'presets',
						label: 'Presets',
						items: Array([
							MenuItemConfig(id: 'p1', label: 'Default', kind: 'radio', checked: true, onClick: local Function(){ statusLabel:emit(value: 'Menu: Default preset'); }),
							MenuItemConfig(id: 'p2', label: 'Compact', kind: 'radio', checked: false, onClick: local Function(){ statusLabel:emit(value: 'Menu: Compact preset'); })
						])
					)
				])
			)
		);

		return SectionV(
			children: Array([
				Label(text: 'Dropdowns', heading: true),
				TextScrap(text: statusLabel, muted: true),
				Frame(
					title: 'Menu & Submenu Dropdowns (Toolbar)',
					child: Frame(padPt: 0.0, child: menuBar)
				),
				Frame(
					title: 'ColorSwatchDropdown Configurations',
					child: SectionH(
						children: Array([
							SectionV(
								title: 'Ring + History',
								children: Array([
									ColorSwatchDropdown(
										color: c1,
										showPicker: true,
										showHistory: true,
										compactPicker: false,
										tooltip: 'Concentric ring color picker + swatch history',
										onChange: local Function(Color is c){ statusLabel:emit(value: 'Ring + History: ' . c:toHex()); }
									)
								])
							),
							SectionV(
								title: 'Compact + History',
								children: Array([
									ColorSwatchDropdown(
										color: c2,
										showPicker: true,
										showHistory: true,
										compactPicker: true,
										tooltip: 'Compact 3-bar picker + swatch history',
										onChange: local Function(Color is c){ statusLabel:emit(value: 'Compact + History: ' . c:toHex()); }
									)
								])
							),
							SectionV(
								title: 'Swatches Only',
								children: Array([
									ColorSwatchDropdown(
										color: c3,
										showPicker: false,
										showHistory: true,
										historyColors: Array([
											Color(r: 239, g: 83, b: 80),
											Color(r: 255, g: 167, b: 38),
											Color(r: 76, g: 175, b: 80),
											Color(r: 66, g: 133, b: 244),
											Color(r: 171, g: 71, b: 188)
										]),
										tooltip: 'Picker disabled; choose from custom swatch history',
										onChange: local Function(Color is c){ statusLabel:emit(value: 'Swatches Only: ' . c:toHex()); }
									)
								])
							),
							SectionV(
								title: 'Picker Only',
								children: Array([
									ColorSwatchDropdown(
										color: c1,
										showPicker: true,
										showHistory: false,
										compactPicker: true,
										tooltip: 'History disabled; compact picker only',
										onChange: local Function(Color is c){ statusLabel:emit(value: 'Picker Only: ' . c:toHex()); }
									)
								])
							)
						])
					)
				)
			])
		);
	}
}
