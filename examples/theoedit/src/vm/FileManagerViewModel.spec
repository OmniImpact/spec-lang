#! Package theoedit:vm
#! ViewModel for the theoedit file manager dialog (Open / Save As).
#! Uses [DirectoryScanner] and [PathTransformer] to transform the pure
#! [DirectoryListing] model for the view.

Class is FileManagerViewModel{
	namespace: ['theoedit', 'vm'];

	merge Array of Array of String is using: [
		['base', 'signal', [EnumEmitter, TextEmitter]],
		['theoedit', 'model', DirectoryListing],
		['theoedit', 'util', [DirectoryScanner, FileManagerFocus, PathTransformer]]
	];

	DirectoryScanner is scanner: DirectoryScanner();
	PathTransformer is paths: PathTransformer();
	DirectoryListing is listing: DirectoryListing();
	String is mode: 'open';
	String is curDir: '.';
	String is initialName: '';
	Array of String is entries: Array();
	TextEmitter is headerTitle: TextEmitter(initial: 'File Manager');
	EnumEmitter of FileManagerFocus is focus: EnumEmitter(initial: FileManagerFocus:LIST);
	EnumEmitter of FileManagerFocus is hover: EnumEmitter(initial: FileManagerFocus:NONE);
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
			focus:emit(value: FileManagerFocus:INPUT);
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
