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
	BoolEmitter is aboutOpen: BoolEmitter(initial: false);
	BoolEmitter is wrapEnabled: BoolEmitter(initial: false);
	BoolEmitter is lineNumbersEnabled: BoolEmitter(initial: false);
	TextEmitter is documentText: TextEmitter(initial: '');
	TextEmitter is cursorStatus: TextEmitter(initial: 'Ln 1, Col 1');
	TextEmitter is versionText: TextEmitter(initial: 'SpecEdit 0.1.0');
	TextEmitter is descriptionText: TextEmitter(initial: 'Resolution-independent text editor built on Suit, Sew, Fabric, and Scrap.');
	Float is windowWidthPt: 800.0;
	Float is windowHeightPt: 600.0;
	Float is toolbarHeightPt: 30.0;
	String is themePreset: 'light_grayscale';
	String is aboutTitle: 'About SpecEdit';
	Float is aboutWidthPt: 420.0;
	Float is aboutHeightPt: 170.0;
	String is fileDialogTitle: 'Open File';
	Boolean is allowMultipleFiles: false;
	ToolbarConfig is toolbarConfig: ToolbarConfig();

	MenuItemConfig is wrapItem: MenuItemConfig(id: 'wrap', label: 'Wrap', kind: 'toggle');
	MenuItemConfig is lineNumsItem: MenuItemConfig(id: 'line_numbers', label: 'Line Numbers', kind: 'toggle');

	Function is copyHandler: local Function(){};
	Function is cutHandler: local Function(){};
	Function is pasteHandler: local Function(){};
	Function is selectAllHandler: local Function(){};

	replace Function is init(EditorModel is model: EditorModel(documentName: 'Untitled')){
		:model: model;
		title: TextEmitter(initial: :computeTitle());
		running: BoolEmitter(initial: true);
		fileDialogOpen: BoolEmitter(initial: false);
		aboutOpen: BoolEmitter(initial: false);
		wrapEnabled: BoolEmitter(initial: false);
		lineNumbersEnabled: BoolEmitter(initial: false);
		documentText: TextEmitter(initial: model:text);
		cursorStatus: TextEmitter(initial: 'Ln 1, Col 1');
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

		local MenuConfig is editMenu: MenuConfig(id: 'edit', label: 'Edit');
		editMenu:addItem(item: MenuItemConfig(
			id: 'copy',
			label: 'Copy',
			onClick: local Function(){ :requestCopy(); }
		));
		editMenu:addItem(item: MenuItemConfig(
			id: 'cut',
			label: 'Cut',
			onClick: local Function(){ :requestCut(); }
		));
		editMenu:addItem(item: MenuItemConfig(
			id: 'paste',
			label: 'Paste',
			onClick: local Function(){ :requestPaste(); }
		));
		editMenu:addItem(item: MenuItemConfig(
			id: 'select_all',
			label: 'Select All',
			onClick: local Function(){ :requestSelectAll(); }
		));
		cfg:addMenu(menu: editMenu);

		local MenuConfig is viewMenu: MenuConfig(id: 'view', label: 'View');
		wrapItem: MenuItemConfig(
			id: 'wrap',
			label: 'Wrap',
			checked: wrapEnabled:current(),
			kind: 'toggle',
			onClick: local Function(){ :toggleWrap(); }
		);
		lineNumsItem: MenuItemConfig(
			id: 'line_numbers',
			label: 'Line Numbers',
			checked: lineNumbersEnabled:current(),
			kind: 'toggle',
			onClick: local Function(){ :toggleLineNumbers(); }
		);
		viewMenu:addItem(item: wrapItem);
		viewMenu:addItem(item: lineNumsItem);
		cfg:addMenu(menu: viewMenu);

		local MenuConfig is helpMenu: MenuConfig(id: 'help', label: 'Help');
		helpMenu:addItem(item: MenuItemConfig(
			id: 'about',
			label: 'About',
			onClick: local Function(){ :requestAbout(); }
		));
		cfg:addMenu(menu: helpMenu);

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

	Function is onDocumentEdited(String is text){
		model:text: text;
		if({ !model:dirty }, {
			model:dirty: true;
			title:emit(value: :computeTitle());
		});
	}

	## Binds View-owned editor text actions (copy/cut/paste/selectAll) without coupling VM to `TextView`.
	Function is bindEditorActions(
		Function is onCopy,
		Function is onCut,
		Function is onPaste,
		Function is onSelectAll
	){
		copyHandler: onCopy;
		cutHandler: onCut;
		pasteHandler: onPaste;
		selectAllHandler: onSelectAll;
	}

	Function is requestCopy(){
		local Function is fn: copyHandler;
		fn();
	}

	Function is requestCut(){
		local Function is fn: cutHandler;
		fn();
	}

	Function is requestPaste(){
		local Function is fn: pasteHandler;
		fn();
	}

	Function is requestSelectAll(){
		local Function is fn: selectAllHandler;
		fn();
	}

	Function is toggleWrap(){
		local Boolean is next: !wrapEnabled:current();
		wrapEnabled:emit(value: next);
		wrapItem:checked: next;
	}

	Function is toggleLineNumbers(){
		local Boolean is next: !lineNumbersEnabled:current();
		lineNumbersEnabled:emit(value: next);
		lineNumsItem:checked: next;
	}

	Function is requestAbout(){
		aboutOpen:emit(value: true);
	}

	## Command invoked by menu/keyboard bindings to exit the application.
	Function is requestQuit(){
		running:emit(value: false);
	}
}
