#! Package theoedit:vm
#! ViewModel for the theoedit file manager dialog (Open / Save As).
#! Owns directory navigation state, entry list, and submission path resolution,
#! delegating filesystem listing/sorting to [DirectoryBrowser].

Class is FileManagerViewModel{
	namespace: ['theoedit', 'vm'];

	merge Array of Array of String is using: [
		['base', 'signal', TextEmitter],
		['theoedit', 'model', DirectoryBrowser]
	];

	DirectoryBrowser is browser: DirectoryBrowser();
	String is mode: 'open';
	String is curDir: '.';
	String is initialName: '';
	Array of String is entries: Array();
	TextEmitter is headerTitle: TextEmitter(initial: 'File Manager');

	replace Function is init(
		String is mode: 'open',
		String is initialDir: '.',
		String is initialName: ''
	){
		:mode: mode;
		:initialName: initialName;
		curDir: browser:normalizeDir(path: initialDir);
		entries: browser:listEntries(dir: curDir);
		headerTitle:emit(value: "File Manager — {{curDir}}");
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
		curDir: nextDir;
		entries: browser:listEntries(dir: curDir);
		headerTitle:emit(value: "File Manager — {{curDir}}");
	}

	Function is activateEntry(String is entry, Function is onListUpdated, Function is onFileChosen){
		if({ entry == '..' }, {
			navigateTo(nextDir: browser:parentDir(dir: curDir));
			onListUpdated(entries);
			return;
		});
		if({ entry:endsWith(suffix: '/') }, {
			navigateTo(nextDir: browser:childDir(dir: curDir, entry: entry));
			onListUpdated(entries);
			return;
		});
		onFileChosen(entry);
	}

	Function is selectEntry(String is entry, Function is onFileSelected){
		if({ !browser:isDirectoryEntry(entry: entry) }, {
			onFileSelected(entry);
		});
	}

	Function is submit(String is typedName, Function is onConfirmed){
		local String is full: browser:resolveTargetPath(dir: curDir, typedName: typedName);
		if({ full == '' }, { return; });
		onConfirmed(full);
	}
}
