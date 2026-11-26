#! Package specedit:view:settings
#! Interface settings category view using SectionV, SectionH, and Switch.

Class is InterfaceSettingsView{
	replace [String] is namespace: ['specedit', 'view', 'settings'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', Switch],
		['base', 'scrap', SectionV],
		['base', 'scrap', SectionH],
		['specedit', 'viewmodel', SettingsViewModel]
	];

	SettingsViewModel is vm: SettingsViewModel();
	Switch is monoSwitch: Switch();
	Switch is wrapSwitch: Switch();
	Switch is treeSwitch: Switch();

	replace Function is init(SettingsViewModel is vm){
		:vm: vm;
	}

	Function of SewNode is build(){
		:monoSwitch: Switch(
			checked: vm:model:defaultMonospace,
			onToggle: local Function(Boolean is _next){ vm:toggleDefaultMonospace(); }
		);
		:wrapSwitch: Switch(
			checked: vm:model:defaultWrap,
			onToggle: local Function(Boolean is _next){ vm:toggleDefaultWrap(); }
		);
		:treeSwitch: Switch(
			checked: vm:model:defaultShowFileTree,
			onToggle: local Function(Boolean is _next){ vm:toggleDefaultShowFileTree(); }
		);

		return SectionV(
			children: Array([
				Label(text: 'Interface', heading: true),
				Frame(
					title: 'Startup Defaults',
					child: SectionV(
						children: Array([
							SectionH(children: Array([monoSwitch, Label(text: 'Default Monospace Font')])),
							SectionH(children: Array([wrapSwitch, Label(text: 'Default Word Wrap')])),
							SectionH(children: Array([treeSwitch, Label(text: 'Show File Tree by Default')]))
						])
					)
				)
			])
		);
	}

	Function is sync(){
		monoSwitch:setChecked(next: vm:model:defaultMonospace);
		wrapSwitch:setChecked(next: vm:model:defaultWrap);
		treeSwitch:setChecked(next: vm:model:defaultShowFileTree);
	}
}