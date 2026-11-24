#! Package theoedit:vm
#! ViewModel for the theoedit file manager dialog (Open / Save As).
#! Uses [DirectoryScanner] and [PathTransformer] to transform the pure
#! [DirectoryListing] model for the view.

Class is FileManagerViewModel{
	replace [String] is namespace: ['theoedit', 'vm'];

	merge [[String]] is using: [
		['base', 'signal', [EnumEmitter, ListEmitter, TextEmitter]],
		['theoedit', 'model', DirectoryListing],
		['theoedit', 'util', [DirectoryScanner, EditorStrings, FileDialogMode, FileManagerFocus, PathTransformer]]
	];

	DirectoryScanner is scanner: DirectoryScanner();
	PathTransformer is paths: PathTransformer();
	DirectoryListing is listing: DirectoryListing();
	FileDialogMode is mode: FileDialogMode:OPEN;
	String is curDir: '.';
	TextEmitter is fileName: TextEmitter(initial: '');
	ListEmitter of String is entries: ListEmitter();
	TextEmitter is headerTitle: TextEmitter(initial: EditorStrings:FILE_MANAGER_TITLE);
	EnumEmitter of FileManagerFocus is focus: EnumEmitter(initial: FileManagerFocus:LIST);
	EnumEmitter of FileManagerFocus is hover: EnumEmitter(initial: FileManagerFocus:NONE);
	Function is onConfirm: local Function(String is _path){};
	Function is onCancel: local Function(){};

	replace Function is init(
		FileDialogMode is mode: FileDialogMode:OPEN,
		String is initialDir: '.',
		String is initialName: '',
		Function is onConfirm: local Function(String is _path){},
		Function is onCancel: local Function(){}
	){
		:mode: mode;
		fileName:emit(value: initialName);
		:onConfirm: onConfirm;
		:onCancel: onCancel;
		if({ isSaveAs() }, {
			focus:emit(value: FileManagerFocus:INPUT);
		});
		navigateTo(nextDir: initialDir);
	}

	Function of Boolean is isSaveAs(){
		return mode == FileDialogMode:SAVE_AS;
	}

	Function of String is actionLabel(){
		return if({ isSaveAs() }, { EditorStrings:LABEL_SAVE }, { EditorStrings:LABEL_OPEN });
	}

	Function of String is actionKey(){
		return if({ isSaveAs() }, { EditorStrings:KEY_SAVE }, { EditorStrings:KEY_OPEN });
	}

	Function is navigateTo(String is nextDir){
		listing: scanner:scan(dir: nextDir);
		curDir: listing:dir;
		local [String] is nextEntries: [];
		listing:entries:each(action: local Function(String is item){
			nextEntries:push(item: item);
		});
		entries:emit(value: nextEntries);
		headerTitle:emit(value: EditorStrings:fileManagerTitle(dir: curDir));
	}

	Function is activateEntry(String is entry){
		if({ entry == '..' }, {
			navigateTo(nextDir: paths:parentDir(dir: curDir));
			return;
		});
		if({ entry:endsWith(suffix: '/') }, {
			navigateTo(nextDir: paths:childDir(dir: curDir, entry: entry));
			return;
		});
		fileName:emit(value: entry);
		confirm(typedName: entry);
	}

	Function is selectEntry(String is entry){
		if({ !paths:isDirectoryEntry(entry: entry) }, {
			fileName:emit(value: entry);
		});
	}

	Function is onNameChanged(String is typedName){
		fileName:emit(value: typedName);
	}

	Function is confirmCurrent(){
		confirm(typedName: fileName:current());
	}

	Function is confirm(String is typedName){
		local String is full: paths:resolveTargetPath(dir: curDir, typedName: typedName);
		if({ full == '' }, { return; });
		onConfirm(full);
	}

	Function is cancel(){
		onCancel();
	}

	Function is setFocus(FileManagerFocus is target){
		if({ focus:current() != target }, {
			focus:emit(value: target);
		});
	}

	Function is setHover(FileManagerFocus is target, Boolean is isHovered){
		if({ isHovered }, {
			if({ hover:current() != target }, {
				hover:emit(value: target);
			});
			return;
		});
		if({ hover:current() == target }, {
			hover:emit(value: FileManagerFocus:NONE);
		});
	}

	Function is handleEscKey(){
		cancel();
	}

	Function is handleMenuKey(){
		local FileManagerFocus is cur: focus:current();
		if({ cur == FileManagerFocus:OK || cur == FileManagerFocus:CANCEL }, {
			if({ isSaveAs() }, {
				focus:emit(value: FileManagerFocus:INPUT);
			}, {
				focus:emit(value: FileManagerFocus:LIST);
			});
			return;
		});
		focus:emit(value: FileManagerFocus:OK);
	}

	Function is handleFocusToggleKey(){
		if({ focus:current() == FileManagerFocus:LIST }, {
			focus:emit(value: FileManagerFocus:INPUT);
		}, {
			focus:emit(value: FileManagerFocus:LIST);
		});
	}

	Function of Boolean is handleUpFromActions(){
		local FileManagerFocus is cur: focus:current();
		if({ cur == FileManagerFocus:OK || cur == FileManagerFocus:CANCEL }, {
			focus:emit(value: FileManagerFocus:INPUT);
			return true;
		});
		return false;
	}
}
