#! Package theoedit:util
#! Centralized UI strings, labels, shortcut keys, and message formatters for theoedit.

Class is EditorStrings{
	replace [String] is namespace: ['theoedit', 'util'];

	held String is UNTITLED: '[untitled]';
	held String is STATUS_DEFAULT: 'Ctrl+M: menu';
	held String is STATUS_OPENED: 'Opened';
	held String is STATUS_SAVED: 'Saved';
	held String is PROMPT_UNSAVED_QUIT: 'Unsaved changes — save before quitting?';

	held String is FILE_MANAGER_TITLE: 'File Manager';
	held String is FILE_MANAGER_HINTS: 'Ctrl+M: menu · Ctrl+F: files/name';
	held String is FILE_MANAGER_NAME_LABEL: 'Name: ';
	held String is FILE_MANAGER_PLACEHOLDER: 'filename';

	held String is LABEL_QUIT: ' Quit ';
	held String is LABEL_SAVE: ' Save ';
	held String is LABEL_SAVE_AS: ' Save As ';
	held String is LABEL_OPEN: ' Open ';
	held String is LABEL_DISCARD: ' Discard ';
	held String is LABEL_CANCEL: ' Cancel ';

	held String is KEY_QUIT: 'q';
	held String is KEY_SAVE: 's';
	held String is KEY_SAVE_AS: 'a';
	held String is KEY_OPEN: 'o';
	held String is KEY_DISCARD: 'd';
	held String is KEY_CANCEL: 'c';

	held Function of String is dirtyTitle(String is base){
		return "{{base}} *";
	}

	held Function of String is fileManagerTitle(String is dir){
		return "File Manager — {{dir}}";
	}

	held Function of String is saveFailed(String is err){
		return "Save failed: {{err}}";
	}
}
