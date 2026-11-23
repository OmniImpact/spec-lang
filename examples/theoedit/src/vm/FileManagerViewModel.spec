#! Package theoedit:vm
#! ViewModel for the theoedit file manager dialog (Open / Save As).
#! Uses [DirectoryScanner] and [PathTransformer] to transform the pure
#! [DirectoryListing] model for the view.

Class is FileManagerViewModel{
	namespace: ['theoedit', 'vm'];

	merge Array of Array of String is using: [
		['base', 'signal', [BoolEmitter, TextEmitter]],
		['theoedit', 'model', DirectoryListing],
		['theoedit', 'util', [DirectoryScanner, PathTransformer]]
	];

	DirectoryScanner is scanner: DirectoryScanner();
	PathTransformer is paths: PathTransformer();
	DirectoryListing is listing: DirectoryListing();
	String is mode: 'open';
	String is curDir: '.';
	String is initialName: '';
	Array of String is entries: Array();
	TextEmitter is headerTitle: TextEmitter(initial: 'File Manager');
	BoolEmitter is listFocused: BoolEmitter(initial: true);
	BoolEmitter is inputFocused: BoolEmitter(initial: false);
	BoolEmitter is okFocused: BoolEmitter(initial: false);
	Function is onConfirm: local Function(String is _path){};
	Function is onCancel: local Function(){};
	Function is onListUpdated: local Function(Array of String is _nextItems){};
	Function is onNameUpdated: local Function(String is _fileName){};

	replace Function is init(
		String is mode: 'open',
		String is initialDir: '.',
		String is initialName: '',
		Function is onConfirm: local Function(String is _path){},
		Function is onCancel: local Function(){}
	){
		:mode: mode;
		:initialName: initialName;
		:onConfirm: onConfirm;
		:onCancel: onCancel;
		if({ isSaveAs() }, {
			listFocused:emit(value: false);
			inputFocused:emit(value: true);
		});
		navigateTo(nextDir: initialDir);
	}

	Function of Boolean is isSaveAs(){
		return mode == 'saveAs';
	}

	Function of String is actionLabel(){
		return if({ isSaveAs() }, { ' Save ' }, { ' Open ' });
	}

	Function of String is actionKey(){
		return if({ isSaveAs() }, { 's' }, { 'o' });
	}

	Function is navigateTo(String is nextDir){
		listing: scanner:scan(dir: nextDir);
		curDir: listing:dir;
		entries: listing:entries;
		headerTitle:emit(value: "File Manager — {{curDir}}");
	}

	Function is activateEntry(String is entry){
		if({ entry == '..' }, {
			navigateTo(nextDir: paths:parentDir(dir: curDir));
			onListUpdated(entries);
			return;
		});
		if({ entry:endsWith(suffix: '/') }, {
			navigateTo(nextDir: paths:childDir(dir: curDir, entry: entry));
			onListUpdated(entries);
			return;
		});
		onNameUpdated(entry);
		confirm(typedName: entry);
	}

	Function is selectEntry(String is entry){
		if({ !paths:isDirectoryEntry(entry: entry) }, {
			onNameUpdated(entry);
		});
	}

	Function is confirm(String is typedName){
		local String is full: paths:resolveTargetPath(dir: curDir, typedName: typedName);
		if({ full == '' }, { return; });
		onConfirm(full);
	}

	Function is cancel(){
		onCancel();
	}

	local Function is focusList(){
		inputFocused:emit(value: false);
		okFocused:emit(value: false);
		listFocused:emit(value: true);
	}

	local Function is focusInput(){
		listFocused:emit(value: false);
		okFocused:emit(value: false);
		inputFocused:emit(value: true);
	}

	local Function is focusOk(){
		listFocused:emit(value: false);
		inputFocused:emit(value: false);
		okFocused:emit(value: true);
	}

	Function is handleEscKey(){
		cancel();
	}

	Function is handleMenuKey(Boolean is actionsFocused){
		if({ actionsFocused }, {
			if({ isSaveAs() }, {
				focusInput();
			}, {
				focusList();
			});
			return;
		});
		focusOk();
	}

	Function is handleFocusToggleKey(Boolean is listIsFocused){
		if({ listIsFocused }, {
			focusInput();
		}, {
			focusList();
		});
	}

	Function of Boolean is handleUpFromActions(Boolean is actionsFocused){
		if({ actionsFocused }, {
			focusInput();
			return true;
		});
		return false;
	}
}
