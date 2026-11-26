#! Package specedit:util
#! Bundled monochrome SVG icon loader for SpecEdit.

Class is EditorIcons{
	replace [String] is namespace: ['specedit', 'util'];

	replace [[String]] is using: [
		['base', 'sys', Bundle]
	];

	Bundle is bundle: Bundle();
	String is chevronDown: '';
	String is treePlus: '';
	String is treeMinus: '';
	String is radioOff: '';
	String is radioOn: '';
	String is checkboxOff: '';
	String is checkboxOn: '';
	String is fileNew: '';
	String is fileOpen: '';
	String is fileSave: '';
	String is fileSaveAs: '';
	String is quit: '';
	String is editCut: '';
	String is editCopy: '';
	String is editPaste: '';
	String is editSelectAll: '';
	String is infoAbout: '';

	replace Function is init(){
		:bundle: Bundle();
		:chevronDown: bundle:readText(path: 'resources/icons/chevron-down.svg');
		:treePlus: bundle:readText(path: 'resources/icons/tree-plus.svg');
		:treeMinus: bundle:readText(path: 'resources/icons/tree-minus.svg');
		:radioOff: bundle:readText(path: 'resources/icons/radio-off.svg');
		:radioOn: bundle:readText(path: 'resources/icons/radio-on.svg');
		:checkboxOff: bundle:readText(path: 'resources/icons/checkbox-off.svg');
		:checkboxOn: bundle:readText(path: 'resources/icons/checkbox-on.svg');
		:fileNew: bundle:readText(path: 'resources/icons/file-new.svg');
		:fileOpen: bundle:readText(path: 'resources/icons/file-open.svg');
		:fileSave: bundle:readText(path: 'resources/icons/file-save.svg');
		:fileSaveAs: bundle:readText(path: 'resources/icons/file-save-as.svg');
		:quit: bundle:readText(path: 'resources/icons/quit.svg');
		:editCut: bundle:readText(path: 'resources/icons/edit-cut.svg');
		:editCopy: bundle:readText(path: 'resources/icons/edit-copy.svg');
		:editPaste: bundle:readText(path: 'resources/icons/edit-paste.svg');
		:editSelectAll: bundle:readText(path: 'resources/icons/edit-select-all.svg');
		:infoAbout: bundle:readText(path: 'resources/icons/info-about.svg');
	}
}
