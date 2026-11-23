#! Package theoedit:model
#! Pure document state model: holds file path, text content, and dirty flag
#! with zero I/O, UI, or formatting dependencies.

Class is EditorDocument{
	namespace: ['theoedit', 'model'];

	String is filePath: '';
	String is text: '';
	Boolean is dirty: false;

	replace Function is init(String is filePath: '', String is text: '', Boolean is dirty: false){
		:filePath: filePath;
		:text: text;
		:dirty: dirty;
	}

	Function is replaceWith(String is path, String is nextText){
		filePath: path;
		text: nextText;
		dirty: false;
	}

	Function is updateText(String is nextText){
		text: nextText;
		dirty: true;
	}

	Function is markSaved(String is path){
		filePath: path;
		dirty: false;
	}
}
