#! Package specedit:viewmodel
#! Pure ViewModel for SpecEdit: owns multi-document tabs, reactive Emitters, ToolbarConfig, context menus, and commands.

Class is EditorViewModel{
	replace [String] is namespace: ['specedit', 'viewmodel'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as File()],
		['base', 'sys', as Process()],
		['base', 'struct', Array],
		['base', 'signal', BoolEmitter],
		['base', 'signal', TextEmitter],
		['base', 'scrap', 'toolbar', ToolbarConfig],
		['base', 'scrap', 'menu', MenuConfig],
		['base', 'scrap', 'menu', MenuItemConfig],
		['base', 'scrap', 'tab', TabBar],
		['base', 'scrap', 'tab', TabItemConfig],
		['base', 'scrap', 'menu', MenuContext],
		['base', 'scrap', 'text', CodeEditorView],
		['base', 'scrap', 'highlighter', Highlighter],
		['specedit', 'model', EditorModel],
		['specedit', 'viewmodel', SettingsViewModel],
		['specedit', 'util', SpecEditStrings],
		['specedit', 'util', EditorIcons]
	];

	EditorModel is model: EditorModel();
	Array of EditorModel is documents: Array();
	Int is activeDocIdx: -1;
	TabBar is boundTabBar: TabBar();
	Boolean is hasBoundTabBar: false;
	CodeEditorView is boundCodeEditor: CodeEditorView(text: TextEmitter(initial: ''));
	Boolean is hasBoundCodeEditor: false;
	EditorIcons is icons: EditorIcons();
	MenuContext is contextMenu: MenuContext();

	TextEmitter is title: TextEmitter(initial: SpecEditStrings:APP_NAME);
	BoolEmitter is running: BoolEmitter(initial: true);
	TextEmitter is activeRoute: TextEmitter(initial: SpecEditStrings:ROUTE_WELCOME);
	BoolEmitter is fileDialogOpen: BoolEmitter(initial: false);
	BoolEmitter is fileDialogSaveMode: BoolEmitter(initial: false);
	BoolEmitter is fileDialogDirMode: BoolEmitter(initial: false);
	Boolean is fileDialogPinMode: false;
	TextEmitter is fileDialogTitle: TextEmitter(initial: SpecEditStrings:FILE_DIALOG_TITLE);
	TextEmitter is fileDialogSuggestedName: TextEmitter(initial: '');
	BoolEmitter is aboutOpen: BoolEmitter(initial: false);
	BoolEmitter is wrapEnabled: BoolEmitter(initial: false);
	BoolEmitter is lineNumbersEnabled: BoolEmitter(initial: false);
	BoolEmitter is monospaceEnabled: BoolEmitter(initial: true);
	BoolEmitter is fileTreeEnabled: BoolEmitter(initial: false);
	TextEmitter is documentText: TextEmitter(initial: '');
	TextEmitter is activeFilePath: TextEmitter(initial: '');
	TextEmitter is activeLanguage: TextEmitter(initial: '');
	TextEmitter is cursorStatus: TextEmitter(initial: '');
	TextEmitter is syntaxStatus: TextEmitter(initial: '');
	TextEmitter is versionText: TextEmitter(initial: SpecEditStrings:VERSION_TEXT);
	TextEmitter is descriptionText: TextEmitter(initial: SpecEditStrings:DESCRIPTION_TEXT);
	TextEmitter is processStatsText: TextEmitter(initial: '');
	Int is statsWindowWallMs: 0;
	Int is statsWindowCpuUs: 0;
	Float is emaCpuPct: 0.0;
	Float is windowWidthPt: 800.0;
	Float is windowHeightPt: 600.0;
	SettingsViewModel is settingsVm: SettingsViewModel();
	String is aboutTitle: SpecEditStrings:ABOUT_TITLE;
	Float is aboutWidthPt: 420.0;
	Float is aboutHeightPt: 255.0;
	Boolean is allowMultipleFiles: false;
	ToolbarConfig is toolbarConfig: ToolbarConfig();
	MenuConfig is editMenu: MenuConfig(id: SpecEditStrings:MENU_EDIT_ID, label: SpecEditStrings:MENU_EDIT_LABEL, visible: false);
	MenuConfig is viewMenu: MenuConfig(id: SpecEditStrings:MENU_VIEW_ID, label: SpecEditStrings:MENU_VIEW_LABEL, visible: false);

	MenuItemConfig is saveItem: MenuItemConfig(id: SpecEditStrings:ITEM_SAVE_ID, label: SpecEditStrings:ITEM_SAVE_LABEL, enabled: false);
	MenuItemConfig is saveAsItem: MenuItemConfig(id: SpecEditStrings:ITEM_SAVE_AS_ID, label: SpecEditStrings:ITEM_SAVE_AS_LABEL, enabled: false);
	MenuItemConfig is cutItem: MenuItemConfig(id: SpecEditStrings:ITEM_CUT_ID, label: SpecEditStrings:ITEM_CUT_LABEL, enabled: false);
	MenuItemConfig is copyItem: MenuItemConfig(id: SpecEditStrings:ITEM_COPY_ID, label: SpecEditStrings:ITEM_COPY_LABEL, enabled: false);
	MenuItemConfig is pasteItem: MenuItemConfig(id: SpecEditStrings:ITEM_PASTE_ID, label: SpecEditStrings:ITEM_PASTE_LABEL, enabled: false);
	MenuItemConfig is selectAllItem: MenuItemConfig(id: SpecEditStrings:ITEM_SELECT_ALL_ID, label: SpecEditStrings:ITEM_SELECT_ALL_LABEL, enabled: false);
	MenuItemConfig is wrapItem: MenuItemConfig(id: SpecEditStrings:ITEM_WRAP_ID, label: SpecEditStrings:ITEM_WRAP_LABEL, kind: SpecEditStrings:MENU_KIND_TOGGLE);
	MenuItemConfig is lineNumsItem: MenuItemConfig(id: SpecEditStrings:ITEM_LINE_NUMS_ID, label: SpecEditStrings:ITEM_LINE_NUMS_LABEL, kind: SpecEditStrings:MENU_KIND_TOGGLE);
	MenuItemConfig is monospaceItem: MenuItemConfig(id: SpecEditStrings:ITEM_MONOSPACE_ID, label: SpecEditStrings:ITEM_MONOSPACE_LABEL, checked: true, kind: SpecEditStrings:MENU_KIND_TOGGLE);
	MenuItemConfig is fileTreeItem: MenuItemConfig(id: SpecEditStrings:ITEM_FILE_TREE_ID, label: SpecEditStrings:ITEM_FILE_TREE_LABEL, checked: false, kind: SpecEditStrings:MENU_KIND_TOGGLE);

	Function is copyHandler: local Function(){};
	Function is cutHandler: local Function(){};
	Function is pasteHandler: local Function(){};
	Function is selectAllHandler: local Function(){};
	Function is canCopyHandler: local Function of Boolean(){ false };
	Function is canPasteHandler: local Function of Boolean(){ false };

	replace Function is init(){
		:icons: EditorIcons();
		:contextMenu: MenuContext(
			radioOffIconSvg: icons:radioOff,
			radioOnIconSvg: icons:radioOn,
			checkboxOnIconSvg: icons:checkboxOn
		);
		:model: EditorModel(documentName: SpecEditStrings:UNTITLED);
		:documents: Array();
		:activeDocIdx: -1;
		activeRoute: TextEmitter(initial: SpecEditStrings:ROUTE_WELCOME);
		title: TextEmitter(initial: :computeTitle());
		running: BoolEmitter(initial: true);
		fileDialogOpen: BoolEmitter(initial: false);
		fileDialogSaveMode: BoolEmitter(initial: false);
		fileDialogTitle: TextEmitter(initial: SpecEditStrings:FILE_DIALOG_TITLE);
		fileDialogSuggestedName: TextEmitter(initial: '');
		:settingsVm: SettingsViewModel();
		aboutOpen: BoolEmitter(initial: false);
		wrapEnabled: BoolEmitter(initial: settingsVm:model:defaultWrap);
		lineNumbersEnabled: BoolEmitter(initial: false);
		monospaceEnabled: BoolEmitter(initial: settingsVm:model:defaultMonospace);
		fileTreeEnabled: BoolEmitter(initial: settingsVm:model:defaultShowFileTree);
		documentText: TextEmitter(initial: '');
		activeFilePath: TextEmitter(initial: '');
		activeLanguage: TextEmitter(initial: '');
		cursorStatus: TextEmitter(initial: '');
		syntaxStatus: TextEmitter(initial: '');
		processStatsText: TextEmitter(initial: '');
		statsWindowWallMs: Process:clockMs();
		statsWindowCpuUs: Process:cpuTimeUs();
		emaCpuPct: 0.0;
		toolbarConfig: :buildToolbarConfig();
		:refreshMenuStates();
	}

	Function of Boolean is hasOpenDocument(){
		return documents:length() > 0 && activeDocIdx >= 0 && activeDocIdx < documents:length();
	}

	local Function of String is computeTitle(){
		if({ !:hasOpenDocument() }, { return SpecEditStrings:APP_NAME; });
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

	local Function is syncSyntaxState(){
		if({ !:hasOpenDocument() }, {
			activeLanguage:emit(value: '');
			syntaxStatus:emit(value: '');
			return;
		});
		activeLanguage:emit(value: model:languageOverride);
		local String is label: 'Plain Text';
		if({ hasBoundCodeEditor }, {
			local Highlighter is hl: boundCodeEditor:highlighterFor(langOverride: model:languageOverride, path: model:filePath);
			label: hl:displayName();
		});
		syntaxStatus:emit(value: label);
	}

	Function is bindCodeEditor(CodeEditorView is editor){
		:boundCodeEditor: editor;
		:hasBoundCodeEditor: true;
		:syncSyntaxState();
	}

	Function is setDocumentLanguage(String is langId){
		if({ !:hasOpenDocument() }, { return; });
		model:languageOverride: langId;
		:syncSyntaxState();
	}

	Function is showSyntaxMenu(Int is x, Int is y){
		if({ !:hasOpenDocument() || !hasBoundCodeEditor }, { return; });
		local Highlighter is detected: boundCodeEditor:highlighterFor(langOverride: '', path: model:filePath);
		local String is curOverride: model:languageOverride;
		local Array of MenuItemConfig is items: Array();
		items:add(item: MenuItemConfig(
			id: 'syntax_auto',
			label: 'Auto-Detect (' . detected:displayName() . ')',
			checked: (curOverride == ''),
			kind: 'radio',
			onClick: local Function(){ :setDocumentLanguage(langId: ''); }
		));
		items:add(item: MenuItemConfig(
			id: 'syntax_plain',
			label: 'Plain Text',
			checked: (curOverride == 'plain'),
			kind: 'radio',
			onClick: local Function(){ :setDocumentLanguage(langId: 'plain'); }
		));
		local Array of Highlighter is registered: boundCodeEditor:registeredHighlighters();
		local Int is i: 0;
		while({ i < registered:length() }, {
			local Highlighter is h: registered:get(index: i);
			local String is lid: h:languageId();
			items:add(item: MenuItemConfig(
				id: 'syntax_' . lid,
				label: h:displayName(),
				checked: (curOverride == lid),
				kind: 'radio',
				onClick: local Function(){ :setDocumentLanguage(langId: lid); }
			));
			i: i + 1;
		});
		contextMenu:open(x: x, y: y, items: items);
	}

	local Function is activateDocument(Int is idx){
		if({ idx < 0 || idx >= documents:length() }, { return; });
		activeDocIdx: idx;
		model: documents:get(index: idx);
		activeRoute:emit(value: SpecEditStrings:ROUTE_FILES);
		documentText:emit(value: model:text);
		activeFilePath:emit(value: model:filePath);
		cursorStatus:emit(value: SpecEditStrings:DEFAULT_CURSOR_STATUS);
		title:emit(value: :computeTitle());
		:syncSyntaxState();
		:syncTabs();
		:refreshMenuStates();
	}

	Function is refreshMenuStates(){
		local Boolean is hasDoc: :hasOpenDocument();
		local Function is copyQ: canCopyHandler;
		local Function is pasteQ: canPasteHandler;
		local Boolean is hasSel: if({ hasDoc }, { copyQ() }, { false });
		local Boolean is hasClip: if({ hasDoc }, { pasteQ() }, { false });
		editMenu:visible: hasDoc;
		viewMenu:visible: hasDoc;
		saveItem:enabled: hasDoc && model:dirty;
		saveAsItem:enabled: hasDoc;
		cutItem:enabled: hasSel;
		copyItem:enabled: hasSel;
		pasteItem:enabled: hasClip;
		selectAllItem:enabled: hasDoc && (model:text:length() > 0);
	}

	Function is bindTabBar(TabBar is tabBar){
		boundTabBar: tabBar;
		hasBoundTabBar: true;
		:syncTabs();
	}

	local Function of ToolbarConfig is buildToolbarConfig(){
		local ToolbarConfig is cfg: ToolbarConfig(
			radioOffIconSvg: icons:radioOff,
			radioOnIconSvg: icons:radioOn,
			checkboxOffIconSvg: icons:checkboxOff,
			checkboxOnIconSvg: icons:checkboxOn
		);

		local MenuConfig is fileMenu: MenuConfig(id: SpecEditStrings:MENU_FILE_ID, label: SpecEditStrings:MENU_FILE_LABEL);
		fileMenu:addItem(item: MenuItemConfig(
			id: SpecEditStrings:ITEM_NEW_ID,
			label: SpecEditStrings:ITEM_NEW_LABEL,
			iconSvg: icons:fileNew,
			onClick: local Function(){ :newDocument(); }
		));
		fileMenu:addItem(item: MenuItemConfig(
			id: SpecEditStrings:ITEM_OPEN_ID,
			label: SpecEditStrings:ITEM_OPEN_LABEL,
			iconSvg: icons:fileOpen,
			onClick: local Function(){ :requestOpen(); }
		));
		saveItem: MenuItemConfig(
			id: SpecEditStrings:ITEM_SAVE_ID,
			label: SpecEditStrings:ITEM_SAVE_LABEL,
			enabled: false,
			iconSvg: icons:fileSave,
			onClick: local Function(){ :requestSave(); }
		);
		saveAsItem: MenuItemConfig(
			id: SpecEditStrings:ITEM_SAVE_AS_ID,
			label: SpecEditStrings:ITEM_SAVE_AS_LABEL,
			enabled: false,
			iconSvg: icons:fileSaveAs,
			onClick: local Function(){ :requestSaveAs(); }
		);
		fileMenu:addItem(item: saveItem);
		fileMenu:addItem(item: saveAsItem);
		fileMenu:addItem(item: MenuItemConfig(
			id: SpecEditStrings:ITEM_SETTINGS_ID,
			label: SpecEditStrings:ITEM_SETTINGS_LABEL,
			iconSvg: icons:settings,
			onClick: local Function(){ settingsVm:openSettings(); }
		));
		fileMenu:addItem(item: MenuItemConfig(
			id: SpecEditStrings:ITEM_QUIT_ID,
			label: SpecEditStrings:ITEM_QUIT_LABEL,
			iconSvg: icons:quit,
			onClick: local Function(){ :requestQuit(); }
		));
		cfg:addMenu(menu: fileMenu);

		:editMenu: MenuConfig(id: SpecEditStrings:MENU_EDIT_ID, label: SpecEditStrings:MENU_EDIT_LABEL, visible: :hasOpenDocument());
		copyItem: MenuItemConfig(
			id: SpecEditStrings:ITEM_COPY_ID,
			label: SpecEditStrings:ITEM_COPY_LABEL,
			enabled: false,
			iconSvg: icons:editCopy,
			onClick: local Function(){ :requestCopy(); }
		);
		cutItem: MenuItemConfig(
			id: SpecEditStrings:ITEM_CUT_ID,
			label: SpecEditStrings:ITEM_CUT_LABEL,
			enabled: false,
			iconSvg: icons:editCut,
			onClick: local Function(){ :requestCut(); }
		);
		pasteItem: MenuItemConfig(
			id: SpecEditStrings:ITEM_PASTE_ID,
			label: SpecEditStrings:ITEM_PASTE_LABEL,
			enabled: false,
			iconSvg: icons:editPaste,
			onClick: local Function(){ :requestPaste(); }
		);
		selectAllItem: MenuItemConfig(
			id: SpecEditStrings:ITEM_SELECT_ALL_ID,
			label: SpecEditStrings:ITEM_SELECT_ALL_LABEL,
			enabled: false,
			iconSvg: icons:editSelectAll,
			onClick: local Function(){ :requestSelectAll(); }
		);
		editMenu:addItem(item: copyItem);
		editMenu:addItem(item: cutItem);
		editMenu:addItem(item: pasteItem);
		editMenu:addItem(item: selectAllItem);
		cfg:addMenu(menu: editMenu);

		:viewMenu: MenuConfig(id: SpecEditStrings:MENU_VIEW_ID, label: SpecEditStrings:MENU_VIEW_LABEL, visible: :hasOpenDocument());
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
		monospaceItem: MenuItemConfig(
			id: SpecEditStrings:ITEM_MONOSPACE_ID,
			label: SpecEditStrings:ITEM_MONOSPACE_LABEL,
			checked: monospaceEnabled:current(),
			kind: SpecEditStrings:MENU_KIND_TOGGLE,
			onClick: local Function(){ :toggleMonospace(); }
		);
		fileTreeItem: MenuItemConfig(
			id: SpecEditStrings:ITEM_FILE_TREE_ID,
			label: SpecEditStrings:ITEM_FILE_TREE_LABEL,
			checked: fileTreeEnabled:current(),
			kind: SpecEditStrings:MENU_KIND_TOGGLE,
			onClick: local Function(){ :toggleFileTree(); }
		);
		viewMenu:addItem(item: wrapItem);
		viewMenu:addItem(item: lineNumsItem);
		viewMenu:addItem(item: monospaceItem);
		viewMenu:addItem(item: fileTreeItem);
		cfg:addMenu(menu: viewMenu);

		local MenuConfig is helpMenu: MenuConfig(id: SpecEditStrings:MENU_HELP_ID, label: SpecEditStrings:MENU_HELP_LABEL);
		helpMenu:addItem(item: MenuItemConfig(
			id: SpecEditStrings:ITEM_ABOUT_ID,
			label: SpecEditStrings:ITEM_ABOUT_LABEL,
			iconSvg: icons:infoAbout,
			onClick: local Function(){ :requestAbout(); }
		));
		cfg:addMenu(menu: helpMenu);

		return cfg;
	}

	Function is newDocument(){
		local EditorModel is doc: EditorModel(documentName: SpecEditStrings:UNTITLED);
		documents:add(item: doc);
		:activateDocument(idx: documents:length() - 1);
	}

	Function is requestOpen(){
		fileDialogPinMode: false;
		fileDialogDirMode:emit(value: false);
		fileDialogSaveMode:emit(value: false);
		fileDialogTitle:emit(value: SpecEditStrings:FILE_DIALOG_TITLE);
		fileDialogSuggestedName:emit(value: '');
		fileDialogOpen:emit(value: true);
	}

	Function is requestPinLocation(){
		fileDialogPinMode: true;
		fileDialogSaveMode:emit(value: false);
		fileDialogDirMode:emit(value: true);
		fileDialogTitle:emit(value: 'Select Location to Pin');
		fileDialogSuggestedName:emit(value: '');
		fileDialogOpen:emit(value: true);
	}

	Function is requestSave(){
		if({ !:hasOpenDocument() }, { return; });
		if({ model:filePath != '' }, {
			:saveDocumentToPath(path: model:filePath);
			return;
		});
		:requestSaveAs();
	}

	Function is requestSaveAs(){
		if({ !:hasOpenDocument() }, { return; });
		local String is suggested: if({ model:filePath != '' }, { :baseName(path: model:filePath) }, { model:documentName });
		fileDialogSaveMode:emit(value: true);
		fileDialogTitle:emit(value: SpecEditStrings:SAVE_DIALOG_TITLE);
		fileDialogSuggestedName:emit(value: suggested);
		fileDialogOpen:emit(value: true);
	}

	Function is cancelOpen(){
		fileDialogOpen:emit(value: false);
	}

	Function is onFileDialogSelected(Array of String is paths){
		fileDialogOpen:emit(value: false);
		if({ paths:length() == 0 }, {
			fileDialogPinMode: false;
			fileDialogDirMode:emit(value: false);
			return;
		});
		if({ fileDialogPinMode }, {
			fileDialogPinMode: false;
			fileDialogDirMode:emit(value: false);
			settingsVm:pinPath(path: paths:get(index: 0));
			return;
		});
		if({ fileDialogSaveMode:current() }, {
			:saveDocumentToPath(path: paths:get(index: 0));
			return;
		});
		:openFiles(paths: paths);
	}

	local Function is saveDocumentToPath(String is path){
		if({ !:hasOpenDocument() || path == '' }, { return; });
		local Boolean is ok: fileWrite(
			path: path,
			content: model:text,
			onSuccess: local Function(Int is _written){},
			onError: local Function(Any is _err){}
		);
		if({ ok }, {
			model:filePath: path;
			model:documentName: :baseName(path: path);
			model:dirty: false;
			activeFilePath:emit(value: path);
			title:emit(value: :computeTitle());
			:syncSyntaxState();
			:syncTabs();
			:refreshMenuStates();
		});
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
		documents: Array();
		activeDocIdx: -1;
		model: EditorModel(documentName: SpecEditStrings:UNTITLED);
		activeRoute:emit(value: SpecEditStrings:ROUTE_WELCOME);
		documentText:emit(value: '');
		activeFilePath:emit(value: '');
		cursorStatus:emit(value: '');
		title:emit(value: :computeTitle());
		:syncSyntaxState();
		:syncTabs();
		:refreshMenuStates();
	}

	Function is showTabContextMenu(Int is index, Int is x, Int is y){
		local Array of MenuItemConfig is items: Array([
			MenuItemConfig(
				id: SpecEditStrings:ITEM_CLOSE_OTHERS_ID,
				label: SpecEditStrings:ITEM_CLOSE_OTHERS_LABEL,
				enabled: documents:length() > 1,
				onClick: local Function(){ :closeOtherTabs(keepIndex: index); }
			),
			MenuItemConfig(
				id: SpecEditStrings:ITEM_CLOSE_ALL_ID,
				label: SpecEditStrings:ITEM_CLOSE_ALL_LABEL,
				enabled: documents:length() > 0,
				onClick: local Function(){ :closeAllTabs(); }
			)
		]);
		contextMenu:open(x: x, y: y, items: items);
	}

	Function is showEditorContextMenu(Int is x, Int is y){
		local Boolean is hasDoc: :hasOpenDocument();
		local Function is copyQ: canCopyHandler;
		local Function is pasteQ: canPasteHandler;
		local Boolean is hasSel: if({ hasDoc }, { copyQ() }, { false });
		local Boolean is hasClip: if({ hasDoc }, { pasteQ() }, { false });
		local Array of MenuItemConfig is items: Array([
			MenuItemConfig(
				id: SpecEditStrings:ITEM_CUT_ID,
				label: SpecEditStrings:ITEM_CUT_LABEL,
				enabled: hasSel,
				onClick: local Function(){ :requestCut(); }
			),
			MenuItemConfig(
				id: SpecEditStrings:ITEM_COPY_ID,
				label: SpecEditStrings:ITEM_COPY_LABEL,
				enabled: hasSel,
				onClick: local Function(){ :requestCopy(); }
			),
			MenuItemConfig(
				id: SpecEditStrings:ITEM_PASTE_ID,
				label: SpecEditStrings:ITEM_PASTE_LABEL,
				enabled: hasClip,
				onClick: local Function(){ :requestPaste(); }
			)
		]);
		contextMenu:open(x: x, y: y, items: items);
	}

	Function is onDocumentEdited(String is text){
		if({ !:hasOpenDocument() }, { return; });
		model:text: text;
		if({ !model:dirty }, {
			model:dirty: true;
			title:emit(value: :computeTitle());
			:syncTabs();
		});
		:refreshMenuStates();
	}

	## Binds View-owned editor text actions (copy/cut/paste/selectAll) without coupling VM to `TextView`.
	Function is bindEditorActions(
		Function is onCopy,
		Function is onCut,
		Function is onPaste,
		Function is onSelectAll,
		Function is canCopy,
		Function is canPaste
	){
		copyHandler: onCopy;
		cutHandler: onCut;
		pasteHandler: onPaste;
		selectAllHandler: onSelectAll;
		canCopyHandler: canCopy;
		canPasteHandler: canPaste;
		:refreshMenuStates();
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

	Function is toggleMonospace(){
		local Boolean is next: !monospaceEnabled:current();
		monospaceEnabled:emit(value: next);
		monospaceItem:checked: next;
	}

	Function is applyInterfaceDefaults(Boolean is mono, Boolean is wrap, Boolean is showTree){
		monospaceEnabled:emit(value: mono);
		monospaceItem:checked: mono;
		wrapEnabled:emit(value: wrap);
		wrapItem:checked: wrap;
		fileTreeEnabled:emit(value: showTree);
		fileTreeItem:checked: showTree;
	}

	Function is toggleFileTree(){
		local Boolean is next: !fileTreeEnabled:current();
		fileTreeEnabled:emit(value: next);
		fileTreeItem:checked: next;
	}

	local Function is emitProcessStats(Int is pid, Int is cpuMs, Int is cpuPct, Int is memKb){
		local Int is memMb: memKb / 1024;
		local Int is memTenths: ((memKb % 1024) * 10) / 1024;
		processStatsText:emit(
			value: 'PID ' . (pid as String)
				. '  |  CPU ' . (cpuMs as String) . ' ms (' . (cpuPct as String) . '%)'
				. '  |  Mem ' . (memMb as String) . '.' . (memTenths as String) . ' MB'
		);
	}

	Function is stepAboutStats(Int is nowMs){
		local Int is elapsed: nowMs - statsWindowWallMs;
		if({ elapsed < 250 }, { return; });
		local Int is pid: Process:getPid();
		local Int is cpuUs: Process:cpuTimeUs();
		local Int is memKb: Process:currentMemoryKb();
		local Int is dCpuUs: cpuUs - statsWindowCpuUs;
		local Float is instPct: ((dCpuUs as Float) / ((elapsed as Float) * 10.0));
		if({ emaCpuPct <= 0.0 }, {
			emaCpuPct: instPct;
		}, {
			emaCpuPct: (emaCpuPct * 0.6) + (instPct * 0.4);
		});
		statsWindowWallMs: nowMs;
		statsWindowCpuUs: cpuUs;
		:emitProcessStats(pid: pid, cpuMs: cpuUs / 1000, cpuPct: (emaCpuPct + 0.5) as Int, memKb: memKb);
	}

	Function is refreshAboutStats(){
		local Int is nowMs: Process:clockMs();
		local Int is pid: Process:getPid();
		local Int is cpuUs: Process:cpuTimeUs();
		local Int is memKb: Process:currentMemoryKb();
		statsWindowWallMs: nowMs;
		statsWindowCpuUs: cpuUs;
		:emitProcessStats(pid: pid, cpuMs: cpuUs / 1000, cpuPct: (emaCpuPct + 0.5) as Int, memKb: memKb);
	}

	Function is requestAbout(){
		:refreshAboutStats();
		aboutOpen:emit(value: true);
	}

	## Command invoked by menu/keyboard bindings to exit the application.
	Function is requestQuit(){
		running:emit(value: false);
	}

	## Handles system-wide keyboard shortcuts across Welcome and Files containers.
	Function of Boolean is handleShortcut(Int is key, Int is mods){
		local Boolean is shift: (mods & 1) != 0;
		local Boolean is ctrl: (mods & 2) != 0;
		if({ !ctrl }, { return false; });
		if({ key == 110 || key == 78 }, { :newDocument(); return true; });
		if({ key == 111 || key == 79 }, { :requestOpen(); return true; });
		if({ key == 115 || key == 83 }, {
			if({ shift }, { :requestSaveAs(); }, { :requestSave(); });
			return true;
		});
		if({ key == 119 || key == 87 }, {
			if({ :hasOpenDocument() }, { :closeTab(index: activeDocIdx); });
			return true;
		});
		if({ key == 113 || key == 81 }, { :requestQuit(); return true; });
		if({ key == 99 || key == 67 }, {
			if({ :hasOpenDocument() }, { :requestCopy(); });
			return true;
		});
		if({ key == 120 || key == 88 }, {
			if({ :hasOpenDocument() }, { :requestCut(); });
			return true;
		});
		if({ key == 118 || key == 86 }, {
			if({ :hasOpenDocument() }, { :requestPaste(); });
			return true;
		});
		if({ key == 97 || key == 65 }, {
			if({ :hasOpenDocument() }, { :requestSelectAll(); });
			return true;
		});
		return false;
	}
}
