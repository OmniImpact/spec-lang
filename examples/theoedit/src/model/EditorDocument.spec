#! Package theoedit:model
#! Pure document model for theoedit: holds file path, text content, dirty state,
#! and performs file load/save without any UI or signal dependencies.

Class is EditorDocument{
	namespace: ['theoedit', 'model'];

	merge Array of Array of String is using: [
		['base', 'core', SpecError],
		['base', 'sys', FileError],
		['base', 'sys', as File()]
	];

	String is filePath: '';
	String is text: '';
	Boolean is dirty: false;
	String is lastError: '';

	replace Function is init(String is filePath: ''){
		:filePath: filePath;
		load();
	}

	Function is load(){
		local String is loadedText: '';
		if({ filePath != '' && fileExists(path: filePath) }, {
			loadedText: fileRead(path: filePath, default: '');
		});
		text: loadedText;
		dirty: false;
		lastError: '';
	}

	Function is open(String is path){
		filePath: path;
		load();
	}

	Function is updateText(String is nextText){
		text: nextText;
		dirty: true;
	}

	Function of Boolean is save(){
		if({ filePath == '' }, {
			return false;
		});
		return saveTo(path: filePath);
	}

	Function of Boolean is saveTo(String is path){
		local Boolean is ok: false;
		lastError: '';
		fileWrite(
			path: path,
			content: text,
			onSuccess: local Function(Int is _bytes){
				filePath: path;
				dirty: false;
				ok: true;
			},
			onError: local Function(SpecError of FileError is err){
				lastError: err:description;
			}
		);
		return ok;
	}

	Function of String is baseTitle(){
		return if({ filePath != '' }, { filePath }, { '[untitled]' });
	}

	Function of String is displayTitle(){
		local String is base: baseTitle();
		return if({ dirty }, { "{{base}} *" }, { base });
	}
}
