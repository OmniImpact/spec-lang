#! Package theoedit:vm
#! ViewModel for the Theo simple text editor.
#! Owns reactive UI emitters and editor workflow decisions, using
#! [FileStorage] and [PathTransformer] to transform the pure [EditorDocument] model.

Class is EditorViewModel{
	namespace: ['theoedit', 'vm'];

	merge Array of Array of String is using: [
		['base', 'signal', TextEmitter],
		['theoedit', 'model', EditorDocument],
		['theoedit', 'util', [FileStorage, PathTransformer]],
		['theoedit', 'vm', FileManagerViewModel]
	];

	EditorDocument is doc: EditorDocument();
	FileStorage is storage: FileStorage();
	PathTransformer is paths: PathTransformer();
	String is filePath: '';
	Boolean is dirty: false;
	String is messageMode: 'none';
	Boolean is quitAfterSave: false;

	Function is onQuit: local Function(){};
	Function is onPushFileManager: local Function(FileManagerViewModel is _fmVm){};
	Function is onPopFileManager: local Function(){};
	Function is onRebuild: local Function(){};
	Function is onFocusEditor: local Function(){};
	Function is onFocusPrompt: local Function(){};
	Function is onFocusMenu: local Function(){};

	TextEmitter is title: TextEmitter(initial: '[untitled]');
	TextEmitter is currentPath: TextEmitter(initial: '');
	TextEmitter is content: TextEmitter(initial: '');
	TextEmitter is status: TextEmitter(initial: 'Ctrl+M: menu');
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
		status:emit(value: 'Opened');
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
			messageMode: 'none';
			syncFromDoc(emitContent: false);
			status:emit(value: 'Saved');
		}, {
			status:emit(value: "Save failed: {{errMsg}}");
		});
		return ok;
	}

	Function is openFileDialog(String is mode){
		local String is initName: if({ mode == 'saveAs' }, { doc:filePath }, { '' });
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
					onFocusEditor();
				});
			},
			onCancel: {
				clearMessage();
				onPopFileManager();
				onFocusEditor();
			}
		);
		onPushFileManager(fmVm);
	}

	Function is triggerSave(){
		local Boolean is openedDialog: false;
		requestSave(onNeedSaveAs: {
			openedDialog: true;
			openFileDialog(mode: 'saveAs');
		});
		if({ !openedDialog }, {
			onFocusEditor();
		});
	}

	Function is triggerSaveAs(){
		openFileDialog(mode: 'saveAs');
	}

	Function is triggerOpen(){
		openFileDialog(mode: 'open');
	}

	Function is triggerQuit(){
		requestQuit(
			onNeedPrompt: {
				onRebuild();
				onFocusPrompt();
			},
			onReadyToQuit: onQuit
		);
	}

	Function is triggerPromptSave(){
		local Boolean is handled: false;
		confirmPromptSave(
			onNeedSaveAs: {
				handled: true;
				onRebuild();
				openFileDialog(mode: 'saveAs');
			},
			onReadyToQuit: {
				handled: true;
				onRebuild();
				onQuit();
			}
		);
		if({ !handled }, {
			onRebuild();
		});
	}

	Function is triggerPromptDiscard(){
		onQuit();
	}

	Function is triggerPromptCancel(){
		clearMessage();
		onRebuild();
		onFocusEditor();
	}

	Function is toggleMenuOrCancelPrompt(Boolean is editorIsFocused){
		if({ hasMessage() }, {
			triggerPromptCancel();
			return;
		});
		if({ editorIsFocused }, {
			onFocusMenu();
		}, {
			onFocusEditor();
		});
	}

	Function is requestSave(Function is onNeedSaveAs){
		if({ doc:filePath == '' }, {
			onNeedSaveAs();
			return;
		});
		save();
	}

	Function is requestQuit(Function is onNeedPrompt, Function is onReadyToQuit){
		if({ doc:dirty }, {
			showUnsavedPrompt();
			onNeedPrompt();
			return;
		});
		onReadyToQuit();
	}

	Function is confirmPromptSave(Function is onNeedSaveAs, Function is onReadyToQuit){
		clearMessage();
		if({ doc:filePath == '' }, {
			quitAfterSave: true;
			onNeedSaveAs();
			return;
		});
		if({ save() }, {
			onReadyToQuit();
		});
	}

	Function is completeFileDialog(String is mode, String is path, Function is onReadyToQuit){
		if({ mode == 'saveAs' }, {
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
		messageMode: 'confirmQuit';
		messageText:emit(value: 'Unsaved changes — save before quitting?');
	}

	Function is clearMessage(){
		messageMode: 'none';
		quitAfterSave: false;
		messageText:emit(value: '');
	}

	Function of Boolean is hasMessage(){
		return messageMode != 'none';
	}
}
