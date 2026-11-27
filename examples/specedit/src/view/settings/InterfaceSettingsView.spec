#! Package specedit:view:settings
#! Interface settings category view using Grid, Frame, Label, and Switch.

Class is InterfaceSettingsView{
	replace [String] is namespace: ['specedit', 'view', 'settings'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Column],
		['base', 'sew', Grid],
		['base', 'fabric', TextStyle],
		['base', 'scrap', Frame],
		['base', 'scrap', Label],
		['base', 'scrap', Switch],
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
			tooltip: 'Use monospace font by default for new documents',
			onToggle: local Function(Boolean is _next){ vm:toggleDefaultMonospace(); }
		);
		:wrapSwitch: Switch(
			checked: vm:model:defaultWrap,
			tooltip: 'Enable word wrapping by default for new documents',
			onToggle: local Function(Boolean is _next){ vm:toggleDefaultWrap(); }
		);
		:treeSwitch: Switch(
			checked: vm:model:defaultShowFileTree,
			tooltip: 'Show the file tree sidebar on startup',
			onToggle: local Function(Boolean is _next){ vm:toggleDefaultShowFileTree(); }
		);

		local Grid is defaultsGrid: Grid(
			columns: 2,
			colGapPt: 12.0,
			rowGapPt: 10.0,
			flexCols: Array([true, false]),
			children: Array([
				Column(
					gapPt: 1.0,
					children: Array([
						Label(text: 'Default Monospace Font'),
						Label(text: 'Use a fixed-width font for newly opened documents', style: TextStyle:CAPTION, muted: true)
					])
				),
				monoSwitch,
				Column(
					gapPt: 1.0,
					children: Array([
						Label(text: 'Default Word Wrap'),
						Label(text: 'Wrap long lines to fit the editor viewport width', style: TextStyle:CAPTION, muted: true)
					])
				),
				wrapSwitch,
				Column(
					gapPt: 1.0,
					children: Array([
						Label(text: 'Show File Tree on Startup'),
						Label(text: 'Open the workspace file tree sidebar when launching', style: TextStyle:CAPTION, muted: true)
					])
				),
				treeSwitch
			])
		);

		return Column(
			gapPt: 10.0,
			children: Array([
				Label(text: 'Interface', heading: true),
				Frame(
					title: 'Editor & Workspace Defaults',
					fillBg: true,
					child: defaultsGrid
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