#! Package specedit:viewmodel
#! Pure ViewModel for SpecEdit: owns reactive Emitters, ToolbarConfig, file loading, and commands.

Class is EditorViewModel{
	replace [String] is namespace: ['specedit', 'viewmodel'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as File()],
		['base', 'struct', Array],
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
	BoolEmitter is fileDialogOpen: BoolEmitter(initial: false);
	TextEmitter is documentText: TextEmitter(initial: '');
	Float is windowWidthPt: 800.0;
	Float is windowHeightPt: 600.0;
	Float is toolbarHeightPt: 30.0;
	ToolbarConfig is toolbarConfig: ToolbarConfig();

	replace Function is init(EditorModel is model){
		:model: model;
		title: TextEmitter(initial: :computeTitle());
		running: BoolEmitter(initial: true);
		fileDialogOpen: BoolEmitter(initial: false);
		documentText: TextEmitter(initial: model:text);
		toolbarConfig: :buildToolbarConfig();
	}

	local Function of String is computeTitle(){
		if({ model:dirty }, {
			return 'SpecEdit - ' . model:documentName . ' *';
		});
		return 'SpecEdit - ' . model:documentName;
	}

	local Function of String is baseName(String is path){
		local Int is len: path:length();
		if({ len == 0 }, { return 'Untitled'; });
		local Int is i: len - 1;
		while({ i >= 0 && path:byteAt(index: i) != 47 }, { i: i - 1; });
		return path:substring(start: i + 1, end: len);
	}

	local Function of ToolbarConfig is buildToolbarConfig(){
		local ToolbarConfig is cfg: ToolbarConfig(heightPt: toolbarHeightPt);
		local MenuConfig is fileMenu: MenuConfig(id: 'file', label: 'File');
		fileMenu:addItem(item: MenuItemConfig(
			id: 'open',
			label: 'Open...',
			onClick: local Function(){ :requestOpen(); }
		));
		fileMenu:addItem(item: MenuItemConfig(
			id: 'quit',
			label: 'Quit',
			onClick: local Function(){ :requestQuit(); }
		));
		cfg:addMenu(menu: fileMenu);
		return cfg;
	}

	Function is requestOpen(){
		fileDialogOpen:emit(value: true);
	}

	Function is cancelOpen(){
		fileDialogOpen:emit(value: false);
	}

	## Opens the first selected file from `FileDialog` and publishes its text to the View.
	Function is openFiles(Array of String is paths){
		fileDialogOpen:emit(value: false);
		if({ paths:length() == 0 }, { return; });
		local String is path: paths:get(index: 0);
		local String is content: fileRead(
			path: path,
			onSuccess: local Function(String is _s){},
			onError: local Function(Any is _err){},
			default: ''
		);
		model:filePath: path;
		model:documentName: :baseName(path: path);
		model:text: content;
		model:dirty: false;
		documentText:emit(value: content);
		title:emit(value: :computeTitle());
	}

	## Command invoked by menu/keyboard bindings to exit the application.
	Function is requestQuit(){
		running:emit(value: false);
	}
}
