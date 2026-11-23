#! Package theoedit:model
#! Pure filesystem directory browser model: lists entries (directories first,
#! case-insensitive alphabetical), resolves parent/child navigation, and
#! resolves typed file paths without any UI or signal dependencies.

Class is DirectoryBrowser{
	namespace: ['theoedit', 'model'];

	merge Array of Array of String is using: [
		['base', 'sys', as Dir()],
		['base', 'sys', as Uri()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Function of String is normalizeDir(String is path){
		return Uri:fromFilePath(filePath: path):toFilePath();
	}

	Function of Boolean is isDirectoryEntry(String is entry){
		return entry == '..' || entry:endsWith(suffix: '/');
	}

	Function is sortAlpha(Array of String is items){
		local Int is n: items:length();
		local Int is i: 1;
		while({ i < n }, {
			local String is key: items:get(index: i);
			local String is keyLow: key:toLower();
			local Int is j: i - 1;
			local Boolean is done: false;
			while({ !done && j >= 0 }, {
				local String is cur: items:get(index: j);
				local String is curLow: cur:toLower();
				local Boolean is gt: curLow > keyLow || (curLow == keyLow && cur > key);
				if({ gt }, {
					items:set(index: j + 1, item: cur);
					j: j - 1;
				}, {
					done: true;
				});
			});
			items:set(index: j + 1, item: key);
			i: i + 1;
		});
	}

	Function of Array of String is listEntries(String is dir){
		local Array of String is dirs: Array();
		local Array of String is files: Array();
		Dir:dirList(path: dir):each(action: local Function(String is name){
			if({ name:startsWith(prefix: '.') }, { return; });
			local String is full: "{{dir}}/{{name}}";
			if({ Dir:dirList(path: full):length() > 0 }, {
				dirs:add(item: "{{name}}/");
			}, {
				files:add(item: name);
			});
		});
		sortAlpha(items: dirs);
		sortAlpha(items: files);
		local Array of String is out: Array(['..']);
		dirs:each(action: local Function(String is d){ out:add(item: d); });
		files:each(action: local Function(String is f){ out:add(item: f); });
		return out;
	}

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
}
