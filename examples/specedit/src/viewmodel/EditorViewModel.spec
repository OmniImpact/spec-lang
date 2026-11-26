#! Package specedit:viewmodel
#! Pure ViewModel for SpecEdit: owns reactive Emitters, ToolbarConfig, and commands.

Class is EditorViewModel{
	replace [String] is namespace: ['specedit', 'viewmodel'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'signal', BoolEmitter],
		['base', 'signal', TextEmitter],
		['base', 'scrap', ToolbarConfig],
		['base', 'scrap', MenuConfig],
		['base', 'scrap', MenuItemConfig],
		['specedit', 'model', EditorModel]
	];

	EditorModel is model: EditorModel();
	TextEmitter is title: TextEmitter(initial: 'SpecEdit - Untitled');
	BoolEmitter is running: BoolEmitter(initial: true);
	Float is windowWidthPt: 800.0;
	Float is windowHeightPt: 600.0;
	Float is toolbarHeightPt: 26.0;
	ToolbarConfig is toolbarConfig: ToolbarConfig();

	replace Function is init(EditorModel is model){
		:model: model;
		title: TextEmitter(initial: :computeTitle());
		running: BoolEmitter(initial: true);
		toolbarConfig: :buildToolbarConfig();
	}

	local Function of String is computeTitle(){
		if({ model:dirty }, {
			return 'SpecEdit - ' . model:documentName . ' *';
		});
		return 'SpecEdit - ' . model:documentName;
	}

	local Function of ToolbarConfig is buildToolbarConfig(){
		local ToolbarConfig is cfg: ToolbarConfig(heightPt: toolbarHeightPt);
		local MenuConfig is fileMenu: MenuConfig(id: 'file', label: 'File');
		fileMenu:addItem(item: MenuItemConfig(
			id: 'quit',
			label: 'Quit',
			onClick: local Function(){ :requestQuit(); }
		));
		cfg:addMenu(menu: fileMenu);
		return cfg;
	}

	## Command invoked by menu/keyboard bindings to exit the application.
	Function is requestQuit(){
		running:emit(value: false);
	}
}
