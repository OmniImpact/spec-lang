#! Package specedit
#! Composition root for SpecEdit (wires Model -> ViewModel -> View -> ToolkitContainer).

Class is SpecEdit{
	replace [String] is namespace: ['specedit'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'cli', Cli],
		['base', 'scrap', ToolkitContainer],
		['specedit', 'viewmodel', EditorViewModel],
		['specedit', 'view', EditorView]
	];

	replace Function is init(Map of String to String is args){
		local Cli is cli: Cli():parseOrExit();
		local Int is durationMs: cli:getInt(name: 'duration-ms', default: 0);
		local Array of String is files: cli:positionals();

		local EditorViewModel is vm: EditorViewModel();
		local EditorView is view: EditorView(vm: vm);
		local ToolkitContainer is container: view:build();
		if({ files:length() > 0 }, {
			vm:openFiles(paths: files);
		});
		container:run(durationMs: durationMs);
	}
}
