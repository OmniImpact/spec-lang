#! Package theoedit:util
#! Pure string/path/title transformation utilities used by ViewModels.

Class is PathTransformer{
	replace [String] is namespace: ['theoedit', 'util'];

	merge [[String]] is using: [
		['theoedit', 'util', EditorStrings]
	];

	Function of Boolean is isDirectoryEntry(String is entry){ entry == '..' || entry:endsWith(suffix: '/') }

	Function of String is parentDir(String is dir){
		local Array of String is parts: dir:split(delimiter: '/');
		if({ parts:length() > 2 }, {
			parts:removeAt(index: parts:length() - 1);
			return parts:join(separator: '/');
		});
		return '/';
	}

	Function of String is childDir(String is dir, String is entry){
		local String is sub: if({ entry:endsWith(suffix: '/') }, {
			entry:substring(start: 0, end: entry:length() - 1)
		}, {
			entry
		});
		return if({ dir == '/' }, { "/{{sub}}" }, { "{{dir}}/{{sub}}" });
	}

	Function of String is resolveTargetPath(String is dir, String is typedName){
		local String is typed: typedName:trim();
		if({ typed == '' }, { return ''; });
		if({ typed:startsWith(prefix: '/') }, { return typed; });
		return if({ dir == '/' }, { "/{{typed}}" }, { "{{dir}}/{{typed}}" });
	}

	Function of String is formatDocumentTitle(String is filePath, Boolean is dirty){
		local String is base: if({ filePath != '' }, { filePath }, { EditorStrings:UNTITLED });
		return if({ dirty }, { EditorStrings:dirtyTitle(base: base) }, { base });
	}
}
