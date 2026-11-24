#! Package theoedit:util
#! File persistence utility used by ViewModels to read and write document text.

Class is FileStorage{
	replace [String] is namespace: ['theoedit', 'util'];

	merge [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'sys', FileError],
		['base', 'sys', as File()]
	];

	Function of String is readText(String is path){
		if({ path != '' && fileExists(path: path) }, {
			return fileRead(path: path, default: '');
		});
		return '';
	}

	Function of Boolean is writeText(String is path, String is content, Function is onError){
		local Boolean is ok: false;
		fileWrite(
			path: path,
			content: content,
			onSuccess: local Function(Int is _bytes){
				ok: true;
			},
			onError: local Function(SpecError of FileError is err){
				onError(err:description);
			}
		);
		return ok;
	}
}
