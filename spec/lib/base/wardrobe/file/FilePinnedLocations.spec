#! Package base:wardrobe
#! Shared JSON persistence for pinned directories (`pinned.json` / `spec_pinned.json`) used by [FileDialog] and [FileTree].

Class is FilePinnedLocations{
	replace [String] is namespace: ['base', 'wardrobe', 'file'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as File()],
		['base', 'sys', Dir],
		['base', 'sys', Process],
		['base', 'sys', Uri],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'core', Result],
		['base', 'data', Json]
	];

	Array of String is names: Array();
	Array of String is paths: Array();

	replace Function is init(){
		:names: Array();
		:paths: Array();
	}

	Function of String is configPath(){
		local Uri is u: Uri();
		local String is appDir: u:appConfigDir(appName: 'spec');
		if({ Dir():isDir(path: appDir) }, {
			return appDir . '/pinned.json';
		});
		return u:configDir() . '/spec_pinned.json';
	}

	Function of Boolean is add(String is name, String is path){
		if({ name == '' || path == '' }, { return false; });
		local Int is i: 0;
		while({ i < paths:length() }, {
			if({ paths:get(index: i) == path }, { return false; });
			i: i + 1;
		});
		names:add(item: name);
		paths:add(item: path);
		return true;
	}

	Function of Boolean is removeAt(Int is index){
		if({ index < 0 || index >= paths:length() }, { return false; });
		names:removeAt(index: index);
		paths:removeAt(index: index);
		return true;
	}

	Function of Boolean is move(Int is fromIdx, Int is toIdx){
		local Int is count: paths:length();
		if({ fromIdx < 0 || fromIdx >= count || toIdx < 0 || toIdx >= count || fromIdx == toIdx }, { return false; });
		local String is nm: names:get(index: fromIdx);
		local String is pp: paths:get(index: fromIdx);
		if({ fromIdx < toIdx }, {
			local Int is i: fromIdx;
			while({ i < toIdx }, {
				names:set(index: i, item: names:get(index: i + 1));
				paths:set(index: i, item: paths:get(index: i + 1));
				i: i + 1;
			});
		}, {
			local Int is i: fromIdx;
			while({ i > toIdx }, {
				names:set(index: i, item: names:get(index: i - 1));
				paths:set(index: i, item: paths:get(index: i - 1));
				i: i - 1;
			});
		});
		names:set(index: toIdx, item: nm);
		paths:set(index: toIdx, item: pp);
		return true;
	}

	local Function is addDefaults(){
		local String is home: Process():getEnv(key: 'HOME', default: '');
		if({ home == '' }, {
			home: Process():getEnv(key: 'USERPROFILE', default: '');
		});
		if({ home != '' && Dir():isDir(path: home) }, {
			:add(name: 'Home', path: home);
			local Array of String is entries: Dir():dirList(path: home);
			local String is docsPath: '';
			local String is dlPath: '';
			local Int is i: 0;
			while({ i < entries:length() }, {
				local String is nm: entries:get(index: i);
				local String is low: nm:toLower();
				if({ low == 'documents' || low == 'downloads' }, {
					local String is full: if({ home:endsWith(suffix: '/') }, { home . nm }, { home . '/' . nm });
					if({ Dir():isDir(path: full) }, {
						if({ low == 'documents' && docsPath == '' }, { docsPath: full; });
						if({ low == 'downloads' && dlPath == '' }, { dlPath: full; });
					});
				});
				i: i + 1;
			});
			if({ docsPath != '' }, { :add(name: 'Documents', path: docsPath); });
			if({ dlPath != '' }, { :add(name: 'Downloads', path: dlPath); });
		});
		:add(name: 'Root', path: '/');
	}

	Function is load(){
		:names: Array();
		:paths: Array();
		local String is raw: fileRead(
			path: :configPath(),
			onSuccess: local Function(String is _s){},
			onError: local Function(Any is _err){},
			default: ''
		);
		if({ raw == '' }, {
			:addDefaults();
			return;
		});
		local Json is j: Json();
		local Array is arr: Array();
		match(on: j:parseArrayResult(text: raw), when: [
			Result:Ok: local Function(Array is v){ arr: v; }
		], default: {});
		local Int is i: 0;
		while({ i < arr:length() }, {
			local Map of String to Any is obj: j:getObjectAt(arr: arr, index: i);
			local String is pname: j:getString(obj: obj, key: 'name', default: '');
			local String is ppath: j:getString(obj: obj, key: 'path', default: '');
			if({ pname != '' && ppath != '' && Dir():isDir(path: ppath) }, {
				:add(name: pname, path: ppath);
			});
			i: i + 1;
		});
		if({ paths:length() == 0 }, {
			:addDefaults();
		});
	}

	Function is save(){
		local Array is arr: Array();
		local Int is i: 0;
		while({ i < paths:length() }, {
			local Map of String to Any is obj: Map:init();
			obj:set(key: 'name', value: names:get(index: i));
			obj:set(key: 'path', value: paths:get(index: i));
			arr:add(item: obj);
			i: i + 1;
		});
		local String is jsonStr: Json():format(value: arr, indent: 2) . "\n";
		fileWrite(
			path: :configPath(),
			content: jsonStr,
			onSuccess: local Function(Int is _n){},
			onError: local Function(Any is _err){}
		);
	}
}
