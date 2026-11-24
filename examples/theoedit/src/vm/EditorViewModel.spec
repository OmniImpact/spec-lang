#! Package theoedit:vm
#! ViewModel for the Theo simple text editor.
#! Owns reactive UI emitters and editor workflow decisions, using
#! [FileStorage] and [PathTransformer] to transform the pure [EditorDocument] model.

Class is EditorViewModel{
	replace [String] is namespace: ['theoedit', 'vm'];

	merge [[String]] is using: [
		['base', 'signal', [EnumEmitter, TextEmitter]],
		['theoedit', 'model', EditorDocument],
		['theoedit', 'util', [EditorFocus, EditorMessageMode, EditorStrings, FileDialogMode, FileStorage, PathTransformer]],
		['theoedit', 'vm', FileManagerViewModel]
	];

	EditorDocument is doc: EditorDocument();
	FileStorage is storage: FileStorage();
	PathTransformer is paths: PathTransformer();
	String is filePath: '';
	Boolean is dirty: false;
	EditorMessageMode is messageMode: EditorMessageMode:NONE;
	Boolean is quitAfterSave: false;

	Function is onQuit: local Function(){};
	Function is onPushFileManager: local Function(FileManagerViewModel is _fmVm){};
	Function is onPopFileManager: local Function(){};
	Function is onRebuild: local Function(){};

	EnumEmitter of EditorFocus is focus: EnumEmitter(initial: EditorFocus:EDITOR);
	EnumEmitter of EditorFocus is hover: EnumEmitter(initial: EditorFocus:NONE);

	TextEmitter is title: TextEmitter(initial: EditorStrings:UNTITLED);
	TextEmitter is currentPath: TextEmitter(initial: '');
	TextEmitter is content: TextEmitter(initial: '');
	TextEmitter is status: TextEmitter(initial: EditorStrings:STATUS_DEFAULT);
	TextEmitter is messageText: TextEmitter(initial: '');

	replace Function is init(String is filePath: ''){
		:filePath: filePath;
		load();
	}

	local Function is syncFromDoc(Boolean is emitContent){
		filePath: doc:filePath;
		dirty: doc:dirty;
		currentPath:emit(value: doc:filePath);
		title:emit(value: paths:formatDocumentTitle(filePath: doc:filePath, dirty: doc:dirty));
		if({ emitContent }, {
			content:emit(value: doc:text);
		});
	}

	Function is load(){
		local String is loadedText: storage:readText(path: filePath);
		doc:replaceWith(path: filePath, nextText: loadedText);
		syncFromDoc(emitContent: true);
	}

	Function is openFile(String is path){
		filePath: path;
		clearMessage();
		load();
		status:emit(value: EditorStrings:STATUS_OPENED);
	}

	Function is onTextChanged(String is nextText){
		local Boolean is wasDirty: doc:dirty;
		doc:updateText(nextText: nextText);
		dirty: doc:dirty;
		content:emit(value: nextText);
		if({ !wasDirty }, {
			title:emit(value: paths:formatDocumentTitle(filePath: doc:filePath, dirty: doc:dirty));
		});
	}

	Function of Boolean is save(){
		if({ doc:filePath == '' }, {
			return false;
		});
		return saveTo(path: doc:filePath);
	}

	Function of Boolean is saveTo(String is path){
		local String is errMsg: '';
		local Boolean is ok: storage:writeText(
			path: path,
			content: doc:text,
			onError: local Function(String is msg){
				errMsg: msg;
			}
		);
		if({ ok }, {
			doc:markSaved(path: path);
			messageMode: EditorMessageMode:NONE;
			syncFromDoc(emitContent: false);
			status:emit(value: EditorStrings:STATUS_SAVED);
		}, {
			status:emit(value: EditorStrings:saveFailed(err: errMsg));
		});
		return ok;
	}

	Function is setFocus(EditorFocus is target){
		if({ focus:current() != target }, {
			focus:emit(value: target);
		});
	}

	Function is setHover(EditorFocus is target, Boolean is isHovered){
		if({ isHovered }, {
			if({ hover:current() != target }, {
				hover:emit(value: target);
			});
			return;
		});
		if({ hover:current() == target }, {
			hover:emit(value: EditorFocus:NONE);
		});
	}

	local Function is focusEditor(){
		focus:emit(value: EditorFocus:EDITOR);
	}

	local Function is focusMenu(){
		focus:emit(value: EditorFocus:SAVE);
	}

	local Function is focusPromptSave(){
		focus:emit(value: EditorFocus:PROMPT_SAVE);
	}

	Function is openFileDialog(FileDialogMode is mode){
		local String is initName: if({ mode == FileDialogMode:SAVE_AS }, { doc:filePath }, { '' });
		local FileManagerViewModel is fmVm: FileManagerViewModel(
			mode: mode,
			initialDir: '.',
			initialName: initName,
			onConfirm: local Function(String is chosenPath){
				local Boolean is finished: false;
				completeFileDialog(
					mode: mode,
					path: chosenPath,
					onReadyToQuit: {
						finished: true;
						onPopFileManager();
						onQuit();
					}
				);
				if({ !finished }, {
					onPopFileManager();
					focusEditor();
				});
			},
			onCancel: {
				clearMessage();
				onPopFileManager();
				focusEditor();
			}
		);
		onPushFileManager(fmVm);
	}

	Function is triggerSave(){
		if({ doc:filePath == '' }, {
			openFileDialog(mode: FileDialogMode:SAVE_AS);
			return;
		});
		save();
		focusEditor();
	}

	Function is triggerSaveAs(){
		openFileDialog(mode: FileDialogMode:SAVE_AS);
	}

	Function is triggerOpen(){
		openFileDialog(mode: FileDialogMode:OPEN);
	}

	Function is triggerQuit(){
		if({ doc:dirty }, {
			showUnsavedPrompt();
			onRebuild();
			focusPromptSave();
			return;
		});
		onQuit();
	}

	Function is triggerPromptSave(){
		clearMessage();
		onRebuild();
		if({ doc:filePath == '' }, {
			quitAfterSave: true;
			openFileDialog(mode: FileDialogMode:SAVE_AS);
			return;
		});
		if({ save() }, {
			onQuit();
		});
	}

	Function is triggerPromptDiscard(){
		onQuit();
	}

	Function is triggerPromptCancel(){
		clearMessage();
		onRebuild();
		focusEditor();
	}

	Function is toggleMenuOrCancelPrompt(){
		if({ hasMessage() }, {
			triggerPromptCancel();
			return;
		});
		if({ focus:current() == EditorFocus:EDITOR }, {
			focusMenu();
		}, {
			focusEditor();
		});
	}

	Function is completeFileDialog(FileDialogMode is mode, String is path, Function is onReadyToQuit){
		if({ mode == FileDialogMode:SAVE_AS }, {
			local Boolean is shouldQuit: quitAfterSave;
			local Boolean is saved: saveTo(path: path);
			quitAfterSave: false;
			if({ saved && shouldQuit }, {
				onReadyToQuit();
			});
			return;
		});
		openFile(path: path);
	}

	Function is showUnsavedPrompt(){
		messageMode: EditorMessageMode:CONFIRM_QUIT;
		messageText:emit(value: EditorStrings:PROMPT_UNSAVED_QUIT);
	}

	Function is clearMessage(){
		messageMode: EditorMessageMode:NONE;
		quitAfterSave: false;
		messageText:emit(value: '');
	}

	Function of Boolean is hasMessage(){ messageMode != EditorMessageMode:NONE; }
}
