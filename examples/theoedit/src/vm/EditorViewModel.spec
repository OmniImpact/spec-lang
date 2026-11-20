#! Package theoedit:vm
#! ViewModel for the Theo simple text editor.

Class is EditorViewModel{
	namespace: ['theoedit', 'vm'];

	merge Array of Array of String is using: [
		['base', 'signal', TextEmitter],
		['base', 'sys', as File()]
	];

	String is filePath: '';
	Boolean is dirty: false;
	String is messageMode: 'none';
	Boolean is quitAfterSave: false;

	TextEmitter is title: TextEmitter(initial: '[untitled]');
	TextEmitter is content: TextEmitter(initial: '');
	TextEmitter is status: TextEmitter(initial: 'Ctrl+M: menu');
	TextEmitter is messageText: TextEmitter(initial: '');

	replace Function is init(String is filePath: ''){
		:filePath: filePath;
		load();
	}

	Function is load(){
		local String is initialText: '';
		if({ filePath != '' && fileExists(path: filePath) }, {
			initialText: fileRead(path: filePath, default: '');
		});
		dirty: false;
		local String is displayTitle: if({ filePath != '' }, { filePath }, { '[untitled]' });
		title:emit(value: displayTitle);
		content:emit(value: initialText);
	}

	Function is openFile(String is path){
		filePath: path;
		messageMode: 'none';
		quitAfterSave: false;
		load();
		status:emit(value: 'Opened');
	}

	Function is onTextChanged(String is nextText){
		content:emit(value: nextText);
		if({ !dirty }, {
			dirty: true;
			local String is baseTitle: if({ filePath != '' }, { filePath }, { '[untitled]' });
			title:emit(value: "{{baseTitle}} *");
		});
	}

	Function of Boolean is save(){
		if({ filePath == '' }, {
			return false;
		});
		saveTo(path: filePath);
	}

	Function of Boolean is saveTo(String is path){
		local Boolean is ok: false;
		fileWrite(
			path: path,
			content: content:current(),
			onSuccess: local Function(Int is _bytes){
				filePath: path;
				dirty: false;
				messageMode: 'none';
				title:emit(value: path);
				status:emit(value: 'Saved');
				ok: true;
			},
			onError: local Function(String is err){
				status:emit(value: "Save failed: {{err}}");
			}
		);
		ok;
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
}
