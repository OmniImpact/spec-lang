#! Package specedit:view:settings
#! Interface settings category view for default editor/layout preferences.

Class is InterfaceSettingsView{
	replace [String] is namespace: ['specedit', 'view', 'settings'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Column],
		['base', 'sew', Row],
		['base', 'scrap', Frame],
		['specedit', 'viewmodel', SettingsViewModel],
		['specedit', 'view', 'settings', SettingsLabel],
		['specedit', 'view', 'settings', SettingsChip]
	];

	SettingsViewModel is vm: SettingsViewModel();
	SettingsChip is monoChip: SettingsChip();
	SettingsChip is wrapChip: SettingsChip();
	SettingsChip is treeChip: SettingsChip();

	replace Function is init(SettingsViewModel is vm){
		:vm: vm;
	}

	local Function of String is toggleText(Boolean is on){
		if({ on }, { return 'On'; });
		return 'Off';
	}

	Function of SewNode is build(){
		:monoChip: SettingsChip(
			label: :toggleText(on: vm:model:defaultMonospace),
			selected: vm:model:defaultMonospace,
			minWidthPt: 64.0,
			onClick: local Function(){ vm:toggleDefaultMonospace(); }
		);
		:wrapChip: SettingsChip(
			label: :toggleText(on: vm:model:defaultWrap),
			selected: vm:model:defaultWrap,
			minWidthPt: 64.0,
			onClick: local Function(){ vm:toggleDefaultWrap(); }
		);
		:treeChip: SettingsChip(
			label: :toggleText(on: vm:model:defaultShowFileTree),
			selected: vm:model:defaultShowFileTree,
			minWidthPt: 64.0,
			onClick: local Function(){ vm:toggleDefaultShowFileTree(); }
		);

		return Column(
			gapPt: 12.0,
			children: Array([
				SettingsLabel(text: 'Interface', heading: true),
				Frame(
					title: 'Startup Defaults',
					child: Column(
						gapPt: 10.0,
						children: Array([
							Row(
								gapPt: 10.0,
								children: Array([
									monoChip,
									SettingsLabel(text: 'Default Monospace Font')
								])
							),
							Row(
								gapPt: 10.0,
								children: Array([
									wrapChip,
									SettingsLabel(text: 'Default Word Wrap')
								])
							),
							Row(
								gapPt: 10.0,
								children: Array([
									treeChip,
									SettingsLabel(text: 'Show File Tree by Default')
								])
							)
						])
					)
				)
			])
		);
	}

	Function is sync(){
		monoChip:setSelected(next: vm:model:defaultMonospace);
		monoChip:setLabel(next: :toggleText(on: vm:model:defaultMonospace));
		wrapChip:setSelected(next: vm:model:defaultWrap);
		wrapChip:setLabel(next: :toggleText(on: vm:model:defaultWrap));
		treeChip:setSelected(next: vm:model:defaultShowFileTree);
		treeChip:setLabel(next: :toggleText(on: vm:model:defaultShowFileTree));
	}
}