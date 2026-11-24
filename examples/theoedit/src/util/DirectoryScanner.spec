#! Package theoedit:util
#! Directory scanning and sorting utility used by ViewModels to build
#! [DirectoryListing] models.

Class is DirectoryScanner{
	replace [String] is namespace: ['theoedit', 'util'];

	merge [[String]] is using: [
		['base', 'sys', as Dir()],
		['base', 'sys', as Uri()],
		['theoedit', 'model', DirectoryListing]
	];

	Function of String is normalizeDir(String is path){
		return Uri:fromFilePath(filePath: path):toFilePath();
	}

	local Function of Boolean is entryLess(String is a, String is aLow, String is b, String is bLow){
		if({ aLow != bLow }, { return aLow < bLow; });
		return a < b;
	}

	local Function is mergeRange(Array of String is items, Array of String is lows, Array of String is tmpItems, Array of String is tmpLows, Int is left, Int is mid, Int is right){
		local Int is i: left;
		local Int is j: mid;
		local Int is k: left;
		while({ i < mid && j < right }, {
			local String is ai: items:get(index: i);
			local String is ali: lows:get(index: i);
			local String is bj: items:get(index: j);
			local String is blj: lows:get(index: j);
			if({ entryLess(a: ai, aLow: ali, b: bj, bLow: blj) }, {
				tmpItems:set(index: k, item: ai);
				tmpLows:set(index: k, item: ali);
				i: i + 1;
			}, {
				tmpItems:set(index: k, item: bj);
				tmpLows:set(index: k, item: blj);
				j: j + 1;
			});
			k: k + 1;
		});
		while({ i < mid }, {
			tmpItems:set(index: k, item: items:get(index: i));
			tmpLows:set(index: k, item: lows:get(index: i));
			i: i + 1;
			k: k + 1;
		});
		while({ j < right }, {
			tmpItems:set(index: k, item: items:get(index: j));
			tmpLows:set(index: k, item: lows:get(index: j));
			j: j + 1;
			k: k + 1;
		});
		local Int is p: left;
		while({ p < right }, {
			items:set(index: p, item: tmpItems:get(index: p));
			lows:set(index: p, item: tmpLows:get(index: p));
			p: p + 1;
		});
	}

	local Function is mergeSortRange(Array of String is items, Array of String is lows, Array of String is tmpItems, Array of String is tmpLows, Int is left, Int is right){
		if({ right - left <= 1 }, { return; });
		local Int is mid: left + (right - left) / 2;
		mergeSortRange(items: items, lows: lows, tmpItems: tmpItems, tmpLows: tmpLows, left: left, right: mid);
		mergeSortRange(items: items, lows: lows, tmpItems: tmpItems, tmpLows: tmpLows, left: mid, right: right);
		mergeRange(items: items, lows: lows, tmpItems: tmpItems, tmpLows: tmpLows, left: left, mid: mid, right: right);
	}

	Function is sortAlpha(Array of String is items){
		local Int is n: items:length();
		if({ n <= 1 }, { return; });
		local Array of String is lows: Array();
		local Array of String is tmpItems: Array();
		local Array of String is tmpLows: Array();
		local Int is i: 0;
		while({ i < n }, {
			local String is s: items:get(index: i);
			lows:add(item: s:toLower());
			tmpItems:add(item: s);
			tmpLows:add(item: '');
			i: i + 1;
		});
		mergeSortRange(items: items, lows: lows, tmpItems: tmpItems, tmpLows: tmpLows, left: 0, right: n);
	}

	Function of DirectoryListing is scan(String is dir){
		local String is normDir: normalizeDir(path: dir);
		local Array of String is dirs: Array();
		local Array of String is files: Array();
		Dir:dirList(path: normDir):each(action: local Function(String is name){
			if({ name:startsWith(prefix: '.') }, { return; });
			local String is full: "{{normDir}}/{{name}}";
			if({ Dir:dirList(path: full):length() > 0 }, {
				dirs:add(item: "{{name}}/");
			}, {
				files:add(item: name);
			});
		});
		sortAlpha(items: dirs);
		sortAlpha(items: files);
		local Array of String is entries: Array(['..']);
		dirs:each(action: local Function(String is d){ entries:add(item: d); });
		files:each(action: local Function(String is f){ entries:add(item: f); });
		return DirectoryListing(dir: normDir, dirs: dirs, files: files, entries: entries);
	}
}
