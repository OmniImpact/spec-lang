#! Package theoedit:vm
#! ViewModel for the Theo simple text editor.
#! Owns reactive UI emitters and editor workflow decisions, delegating
#! document persistence to [EditorDocument].

Class is EditorViewModel{
	namespace: ['theoedit', 'vm'];

	merge Array of Array of String is using: [
		['base', 'signal', TextEmitter],
		['theoedit', 'model', EditorDocument]
	];

	EditorDocument is doc: EditorDocument(filePath: '');
	String is filePath: '';
	Boolean is dirty: false;
	String is messageMode: 'none';
	Boolean is quitAfterSave: false;

	TextEmitter is title: TextEmitter(initial: '[untitled]');
	TextEmitter is currentPath: TextEmitter(initial: '');
	TextEmitter is content: TextEmitter(initial: '');
	TextEmitter is status: TextEmitter(initial: 'Ctrl+M: menu');
	TextEmitter is messageText: TextEmitter(initial: '');

	replace Function is init(String is filePath: ''){
		doc: EditorDocument(filePath: filePath);
		syncFromDoc(emitContent: true);
	}

	local Function is syncFromDoc(Boolean is emitContent){
		filePath: doc:filePath;
		dirty: doc:dirty;
		currentPath:emit(value: doc:filePath);
		title:emit(value: doc:displayTitle());
		if({ emitContent }, {
			content:emit(value: doc:text);
		});
	}

	Function is load(){
		doc:load();
		syncFromDoc(emitContent: true);
	}

	Function is openFile(String is path){
		doc:open(path: path);
		clearMessage();
		syncFromDoc(emitContent: true);
		status:emit(value: 'Opened');
	}

	Function is onTextChanged(String is nextText){
		local Boolean is wasDirty: doc:dirty;
		doc:updateText(nextText: nextText);
		dirty: doc:dirty;
		content:emit(value: nextText);
		if({ !wasDirty }, {
			title:emit(value: doc:displayTitle());
		});
	}

	Function of Boolean is save(){
		if({ doc:filePath == '' }, {
			return false;
		});
		return saveTo(path: doc:filePath);
	}

	Function of Boolean is saveTo(String is path){
		local Boolean is ok: doc:saveTo(path: path);
		if({ ok }, {
			messageMode: 'none';
			syncFromDoc(emitContent: false);
			status:emit(value: 'Saved');
		}, {
			status:emit(value: "Save failed: {{doc:lastError}}");
		});
		return ok;
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
