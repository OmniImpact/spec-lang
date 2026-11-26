#! Package specedit
#! Composition root for SpecEdit (wires Model -> ViewModel -> View -> ToolkitContainer).

Class is SpecEdit{
	replace [String] is namespace: ['specedit'];

	replace [[String]] is using: [
		['base', 'struct', Map],
		['base', 'cli', Cli],
		['base', 'scrap', ToolkitContainer],
		['specedit', 'model', EditorModel],
		['specedit', 'viewmodel', EditorViewModel],
		['specedit', 'view', EditorView]
	];

	replace Function is init(Map of String to String is args){
		local Cli is cli: Cli():parseOrExit();
		local Int is durationMs: cli:getInt(name: 'duration-ms', default: 0);

		local EditorModel is model: EditorModel(documentName: 'Untitled');
		local EditorViewModel is vm: EditorViewModel(model: model);
		EditorView(vm: vm):build():run(durationMs: durationMs);
	}
}
