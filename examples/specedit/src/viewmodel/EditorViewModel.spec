#! Package specedit:viewmodel
#! Pure ViewModel for SpecEdit: owns multi-document tabs, reactive Emitters, ToolbarConfig, context menus, and commands.

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
		['base', 'scrap', TabBar],
		['base', 'scrap', TabItemConfig],
		['base', 'scrap', ContextMenu],
		['specedit', 'model', EditorModel],
		['specedit', 'util', SpecEditStrings]
	];

	EditorModel is model: EditorModel();
	Array of EditorModel is documents: Array();
	Int is activeDocIdx: 0;
	TabBar is boundTabBar: TabBar();
	Boolean is hasBoundTabBar: false;
	ContextMenu is contextMenu: ContextMenu();

	TextEmitter is title: TextEmitter(initial: SpecEditStrings:baseTitle(documentName: SpecEditStrings:UNTITLED));
	BoolEmitter is running: BoolEmitter(initial: true);
	BoolEmitter is fileDialogOpen: BoolEmitter(initial: false);
	BoolEmitter is aboutOpen: BoolEmitter(initial: false);
	BoolEmitter is wrapEnabled: BoolEmitter(initial: false);
	BoolEmitter is lineNumbersEnabled: BoolEmitter(initial: false);
	TextEmitter is documentText: TextEmitter(initial: '');
	TextEmitter is cursorStatus: TextEmitter(initial: SpecEditStrings:DEFAULT_CURSOR_STATUS);
	TextEmitter is versionText: TextEmitter(initial: SpecEditStrings:VERSION_TEXT);
	TextEmitter is descriptionText: TextEmitter(initial: SpecEditStrings:DESCRIPTION_TEXT);
	Float is windowWidthPt: 800.0;
	Float is windowHeightPt: 600.0;
	Float is toolbarHeightPt: 30.0;
	String is themePreset: SpecEditStrings:THEME_PRESET;
	String is aboutTitle: SpecEditStrings:ABOUT_TITLE;
	Float is aboutWidthPt: 420.0;
	Float is aboutHeightPt: 170.0;
	String is fileDialogTitle: SpecEditStrings:FILE_DIALOG_TITLE;
	Boolean is allowMultipleFiles: false;
	ToolbarConfig is toolbarConfig: ToolbarConfig();

	MenuItemConfig is wrapItem: MenuItemConfig(id: SpecEditStrings:ITEM_WRAP_ID, label: SpecEditStrings:ITEM_WRAP_LABEL, kind: SpecEditStrings:MENU_KIND_TOGGLE);
	MenuItemConfig is lineNumsItem: MenuItemConfig(id: SpecEditStrings:ITEM_LINE_NUMS_ID, label: SpecEditStrings:ITEM_LINE_NUMS_LABEL, kind: SpecEditStrings:MENU_KIND_TOGGLE);

	Function is copyHandler: local Function(){};
	Function is cutHandler: local Function(){};
	Function is pasteHandler: local Function(){};
	Function is selectAllHandler: local Function(){};

	replace Function is init(EditorModel is model: EditorModel(documentName: SpecEditStrings:UNTITLED)){
		:model: model;
		:documents: Array([model]);
		:activeDocIdx: 0;
		title: TextEmitter(initial: :computeTitle());
		running: BoolEmitter(initial: true);
		fileDialogOpen: BoolEmitter(initial: false);
		aboutOpen: BoolEmitter(initial: false);
		wrapEnabled: BoolEmitter(initial: false);
		lineNumbersEnabled: BoolEmitter(initial: false);
		documentText: TextEmitter(initial: model:text);
		cursorStatus: TextEmitter(initial: SpecEditStrings:DEFAULT_CURSOR_STATUS);
		toolbarConfig: :buildToolbarConfig();
	}

	local Function of String is computeTitle(){
		local String is base: SpecEditStrings:baseTitle(documentName: model:documentName);
		return if({ model:dirty }, { SpecEditStrings:dirtyTitle(base: base) }, { base });
	}

	local Function of String is baseName(String is path){
		local Int is len: path:length();
		if({ len == 0 }, { return SpecEditStrings:UNTITLED; });
		local Int is i: len - 1;
		while({ i >= 0 && path:byteAt(index: i) != 47 }, { i: i - 1; });
		return path:substring(start: i + 1, end: len);
	}

	local Function is syncTabs(){
		if({ !hasBoundTabBar }, { return; });
		local Array of TabItemConfig is items: Array();
		local Int is i: 0;
		while({ i < documents:length() }, {
			local EditorModel is d: documents:get(index: i);
			local String is tid: if({ d:filePath != '' }, { d:filePath }, { SpecEditStrings:UNTITLED . ':' . i });
			items:add(item: TabItemConfig(id: tid, label: d:documentName, closable: true, dirty: d:dirty));
			i: i + 1;
		});
		boundTabBar:setTabs(tabs: items, activeIndex: activeDocIdx);
	}

	local Function is activateDocument(Int is idx){
		if({ idx < 0 || idx >= documents:length() }, { return; });
		activeDocIdx: idx;
		model: documents:get(index: idx);
		documentText:emit(value: model:text);
		title:emit(value: :computeTitle());
		:syncTabs();
	}

	Function is bindTabBar(TabBar is tabBar){
		boundTabBar: tabBar;
		hasBoundTabBar: true;
		:syncTabs();
	}

	local Function of ToolbarConfig is buildToolbarConfig(){
		local ToolbarConfig is cfg: ToolbarConfig(heightPt: toolbarHeightPt);

		local MenuConfig is fileMenu: MenuConfig(id: SpecEditStrings:MENU_FILE_ID, label: SpecEditStrings:MENU_FILE_LABEL);
		fileMenu:addItem(item: MenuItemConfig(
			id: SpecEditStrings:ITEM_OPEN_ID,
			label: SpecEditStrings:ITEM_OPEN_LABEL,
			onClick: local Function(){ :requestOpen(); }
		));
		fileMenu:addItem(item: MenuItemConfig(
			id: SpecEditStrings:ITEM_QUIT_ID,
			label: SpecEditStrings:ITEM_QUIT_LABEL,
			onClick: local Function(){ :requestQuit(); }
		));
		cfg:addMenu(menu: fileMenu);

		local MenuConfig is editMenu: MenuConfig(id: SpecEditStrings:MENU_EDIT_ID, label: SpecEditStrings:MENU_EDIT_LABEL);
		editMenu:addItem(item: MenuItemConfig(
			id: SpecEditStrings:ITEM_COPY_ID,
			label: SpecEditStrings:ITEM_COPY_LABEL,
			onClick: local Function(){ :requestCopy(); }
		));
		editMenu:addItem(item: MenuItemConfig(
			id: SpecEditStrings:ITEM_CUT_ID,
			label: SpecEditStrings:ITEM_CUT_LABEL,
			onClick: local Function(){ :requestCut(); }
		));
		editMenu:addItem(item: MenuItemConfig(
			id: SpecEditStrings:ITEM_PASTE_ID,
			label: SpecEditStrings:ITEM_PASTE_LABEL,
			onClick: local Function(){ :requestPaste(); }
		));
		editMenu:addItem(item: MenuItemConfig(
			id: SpecEditStrings:ITEM_SELECT_ALL_ID,
			label: SpecEditStrings:ITEM_SELECT_ALL_LABEL,
			onClick: local Function(){ :requestSelectAll(); }
		));
		cfg:addMenu(menu: editMenu);

		local MenuConfig is viewMenu: MenuConfig(id: SpecEditStrings:MENU_VIEW_ID, label: SpecEditStrings:MENU_VIEW_LABEL);
		wrapItem: MenuItemConfig(
			id: SpecEditStrings:ITEM_WRAP_ID,
			label: SpecEditStrings:ITEM_WRAP_LABEL,
			checked: wrapEnabled:current(),
			kind: SpecEditStrings:MENU_KIND_TOGGLE,
			onClick: local Function(){ :toggleWrap(); }
		);
		lineNumsItem: MenuItemConfig(
			id: SpecEditStrings:ITEM_LINE_NUMS_ID,
			label: SpecEditStrings:ITEM_LINE_NUMS_LABEL,
			checked: lineNumbersEnabled:current(),
			kind: SpecEditStrings:MENU_KIND_TOGGLE,
			onClick: local Function(){ :toggleLineNumbers(); }
		);
		viewMenu:addItem(item: wrapItem);
		viewMenu:addItem(item: lineNumsItem);
		cfg:addMenu(menu: viewMenu);

		local MenuConfig is helpMenu: MenuConfig(id: SpecEditStrings:MENU_HELP_ID, label: SpecEditStrings:MENU_HELP_LABEL);
		helpMenu:addItem(item: MenuItemConfig(
			id: SpecEditStrings:ITEM_ABOUT_ID,
			label: SpecEditStrings:ITEM_ABOUT_LABEL,
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

	## Opens selected files into tabs (reusing already-open tabs or replacing an empty initial Untitled tab).
	Function is openFiles(Array of String is paths){
		fileDialogOpen:emit(value: false);
		if({ paths:length() == 0 }, { return; });
		local Int is pIdx: 0;
		while({ pIdx < paths:length() }, {
			local String is path: paths:get(index: pIdx);
			local Int is existingIdx: -1;
			local Int is k: 0;
			while({ k < documents:length() && existingIdx < 0 }, {
				if({ documents:get(index: k):filePath == path }, {
					existingIdx: k;
				});
				k: k + 1;
			});

			if({ existingIdx >= 0 }, {
				:activateDocument(idx: existingIdx);
			}, {
				local String is content: fileRead(
					path: path,
					onSuccess: local Function(String is _s){},
					onError: local Function(Any is _err){},
					default: ''
				);
				local Boolean is reuseEmpty: (documents:length() == 1) && (model:filePath == '') && (model:text == '') && (!model:dirty);
				if({ reuseEmpty }, {
					model:filePath: path;
					model:documentName: :baseName(path: path);
					model:text: content;
					model:dirty: false;
					:activateDocument(idx: 0);
				}, {
					local EditorModel is doc: EditorModel(documentName: :baseName(path: path));
					doc:filePath: path;
					doc:text: content;
					doc:dirty: false;
					documents:add(item: doc);
					:activateDocument(idx: documents:length() - 1);
				});
			});
			pIdx: pIdx + 1;
		});
	}

	Function is selectTab(Int is index){
		:activateDocument(idx: index);
	}

	Function is closeTab(Int is index){
		if({ index < 0 || index >= documents:length() }, { return; });
		if({ documents:length() == 1 }, {
			:closeAllTabs();
			return;
		});
		local Array of EditorModel is nextDocs: Array();
		local Int is i: 0;
		while({ i < documents:length() }, {
			if({ i != index }, {
				nextDocs:add(item: documents:get(index: i));
			});
			i: i + 1;
		});
		documents: nextDocs;
		local Int is nextActive: activeDocIdx;
		if({ index < activeDocIdx }, {
			nextActive: activeDocIdx - 1;
		});
		if({ nextActive >= documents:length() }, {
			nextActive: documents:length() - 1;
		});
		:activateDocument(idx: nextActive);
	}

	Function is closeOtherTabs(Int is keepIndex){
		if({ keepIndex < 0 || keepIndex >= documents:length() }, { return; });
		local EditorModel is kept: documents:get(index: keepIndex);
		documents: Array([kept]);
		:activateDocument(idx: 0);
	}

	Function is closeAllTabs(){
		local EditorModel is fresh: EditorModel(documentName: SpecEditStrings:UNTITLED);
		documents: Array([fresh]);
		:activateDocument(idx: 0);
	}

	Function is showTabContextMenu(Int is index, Int is x, Int is y){
		local Array of MenuItemConfig is items: Array([
			MenuItemConfig(
				id: SpecEditStrings:ITEM_CLOSE_OTHERS_ID,
				label: SpecEditStrings:ITEM_CLOSE_OTHERS_LABEL,
				onClick: local Function(){ :closeOtherTabs(keepIndex: index); }
			),
			MenuItemConfig(
				id: SpecEditStrings:ITEM_CLOSE_ALL_ID,
				label: SpecEditStrings:ITEM_CLOSE_ALL_LABEL,
				onClick: local Function(){ :closeAllTabs(); }
			)
		]);
		contextMenu:open(x: x, y: y, items: items);
	}

	Function is showEditorContextMenu(Int is x, Int is y){
		local Array of MenuItemConfig is items: Array([
			MenuItemConfig(
				id: SpecEditStrings:ITEM_CUT_ID,
				label: SpecEditStrings:ITEM_CUT_LABEL,
				onClick: local Function(){ :requestCut(); }
			),
			MenuItemConfig(
				id: SpecEditStrings:ITEM_COPY_ID,
				label: SpecEditStrings:ITEM_COPY_LABEL,
				onClick: local Function(){ :requestCopy(); }
			),
			MenuItemConfig(
				id: SpecEditStrings:ITEM_PASTE_ID,
				label: SpecEditStrings:ITEM_PASTE_LABEL,
				onClick: local Function(){ :requestPaste(); }
			)
		]);
		contextMenu:open(x: x, y: y, items: items);
	}

	Function is onDocumentEdited(String is text){
		model:text: text;
		if({ !model:dirty }, {
			model:dirty: true;
			title:emit(value: :computeTitle());
			:syncTabs();
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
