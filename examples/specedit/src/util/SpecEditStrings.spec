#! Package specedit:util
#! Centralized UI strings, menu IDs/labels, theme/dialog constants, and title formatters for SpecEdit.

Class is SpecEditStrings{
	replace [String] is namespace: ['specedit', 'util'];

	replace [[String]] is using: [
		['base', 'sys', Conditional],
		['base', 'sys', Loops]
	];

	held String is APP_NAME: 'SpecEdit';
	held String is UNTITLED: 'Untitled';
	held String is TITLE_SEP: ' - ';
	held String is DIRTY_SUFFIX: ' *';
	held String is DEFAULT_CURSOR_STATUS: 'Ln 1, Col 1';
	held String is VERSION_TEXT: 'SpecEdit 0.1.0';
	held String is DESCRIPTION_TEXT: 'Resolution-independent text editor built on Suit, Sew, Fabric, and Scrap.';
	held String is ABOUT_TITLE: 'About SpecEdit';
	held String is FILE_DIALOG_TITLE: 'Open File';
	held String is SAVE_DIALOG_TITLE: 'Save File';
	held String is ROUTE_WELCOME: 'Welcome';
	held String is ROUTE_FILES: 'Files';

	held String is MENU_FILE_ID: 'file';
	held String is MENU_FILE_LABEL: 'File';
	held String is ITEM_NEW_ID: 'new';
	held String is ITEM_NEW_LABEL: 'New';
	held String is ITEM_OPEN_ID: 'open';
	held String is ITEM_OPEN_LABEL: 'Open';
	held String is ITEM_SAVE_ID: 'save';
	held String is ITEM_SAVE_LABEL: 'Save';
	held String is ITEM_SAVE_AS_ID: 'save_as';
	held String is ITEM_SAVE_AS_LABEL: 'Save As';
	held String is ITEM_SETTINGS_ID: 'settings';
	held String is ITEM_SETTINGS_LABEL: 'Settings';
	held String is ITEM_QUIT_ID: 'quit';
	held String is ITEM_QUIT_LABEL: 'Quit';

	held String is MENU_EDIT_ID: 'edit';
	held String is MENU_EDIT_LABEL: 'Edit';
	held String is ITEM_COPY_ID: 'copy';
	held String is ITEM_COPY_LABEL: 'Copy';
	held String is ITEM_CUT_ID: 'cut';
	held String is ITEM_CUT_LABEL: 'Cut';
	held String is ITEM_PASTE_ID: 'paste';
	held String is ITEM_PASTE_LABEL: 'Paste';
	held String is ITEM_SELECT_ALL_ID: 'select_all';
	held String is ITEM_SELECT_ALL_LABEL: 'Select All';

	held String is MENU_VIEW_ID: 'view';
	held String is MENU_VIEW_LABEL: 'View';
	held String is ITEM_WRAP_ID: 'wrap';
	held String is ITEM_WRAP_LABEL: 'Wrap';
	held String is ITEM_LINE_NUMS_ID: 'line_numbers';
	held String is ITEM_LINE_NUMS_LABEL: 'Line Numbers';
	held String is ITEM_MONOSPACE_ID: 'monospace';
	held String is ITEM_MONOSPACE_LABEL: 'Monospace';
	held String is ITEM_FILE_TREE_ID: 'file_tree';
	held String is ITEM_FILE_TREE_LABEL: 'File Tree';

	held String is MENU_HELP_ID: 'help';
	held String is MENU_HELP_LABEL: 'Help';
	held String is ITEM_ABOUT_ID: 'about';
	held String is ITEM_ABOUT_LABEL: 'About';

	held String is ITEM_CLOSE_OTHERS_ID: 'close_others';
	held String is ITEM_CLOSE_OTHERS_LABEL: 'Close Others';
	held String is ITEM_CLOSE_ALL_ID: 'close_all';
	held String is ITEM_CLOSE_ALL_LABEL: 'Close All';

	held Function of String is baseTitle(String is documentName){
		SpecEditStrings:APP_NAME . SpecEditStrings:TITLE_SEP . documentName
	}

	held Function of String is dirtyTitle(String is base){
		base . SpecEditStrings:DIRTY_SUFFIX
	}

	held Function of String is baseName(String is path, String is fallback: ''){
		local Int is len: path:length();
		Conditional:if(check: { len == 0 }, then: { return fallback; });
		local Int is i: len - 1;
		Loops:while(check: { i >= 0 }, body: {
			local Int is b: path:byteAt(index: i);
			Conditional:if(check: { b == 47 || b == 92 }, then: {
				local String is tail: path:substring(start: i + 1, end: len);
				return Conditional:if(check: { tail != '' }, then: { tail }, else: { fallback });
			});
			i: i - 1;
		});
		return path;
	}
}
