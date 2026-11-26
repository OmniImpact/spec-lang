#! Package base:cli
#! JSON-driven CLI parser and `--help` generator backed by `base:sys:Bundle`.

Class is Cli{
	replace [String] is namespace: ['base', 'cli'];

	merge [[String]] is using: [
		['base', 'cli', CliOption],
		['base', 'data', Json],
		['base', 'struct', [Array, Map]],
		['base', 'sys', [Bundle, as File(), as Output()]],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	String is appName: '';
	String is appVersion: '';
	String is appDescription: '';
	String is usageLine: '';
	[CliOption] is options: [];
	Map of String to String is values: Map:init();
	Array of String is posArgs: Array();
	Boolean is helpRequested: false;
	Boolean is versionRequested: false;
	String is errorMessage: '';
	Boolean is quiet: false;

	replace Function is init(Boolean is quiet: false, String is jsonText: ''){
		:quiet: quiet;
		if({ jsonText != '' }, {
			:loadSchema(jsonText: jsonText);
		});
	}

	## Loads option definitions from a bundled asset (e.g. `'cli.json'`),
	## falling back to disk paths when running unbundled.
	Function of Cli is loadFromBundle(String is bundlePath: 'cli.json', String is fallbackPath: ''){
		local Bundle is b: Bundle(autoLoad: true);
		local String is txt: '';
		if({ b:isBundled() && b:has(path: bundlePath) }, {
			txt: b:readText(path: bundlePath, default: '');
		});
		if({ txt == '' && fileExists(path: bundlePath) }, {
			txt: fileRead(path: bundlePath, onSuccess: local Function(String is _s){}, onError: local Function(Any is _e){}, default: '');
		});
		if({ txt == '' && fallbackPath != '' && fileExists(path: fallbackPath) }, {
			txt: fileRead(path: fallbackPath, onSuccess: local Function(String is _s){}, onError: local Function(Any is _e){}, default: '');
		});
		if({ txt != '' }, {
			:loadSchema(jsonText: txt);
		}, {
			:ensureDefaultHelp();
		});
		return :;
	}

	local Function is ensureDefaultHelp(){
		local Boolean is hasHelp: false;
		local Int is i: 0;
		while({ i < options:length() }, {
			local CliOption is opt: options:get(index: i);
			if({ opt:longName == 'help' || opt:shortName == 'h' }, {
				hasHelp: true;
			});
			i: i + 1;
		});
		if({ !hasHelp }, {
			options:push(item: CliOption(
				shortName: 'h',
				longName: 'help',
				optType: 'bool',
				description: 'Show this help message'
			));
		});
	}

	## Loads option definitions from a JSON schema string.
	Function is loadSchema(String is jsonText){
		options: [];
		if({ jsonText:trim() == '' }, {
			ensureDefaultHelp();
			return;
		});
		local Json is j: Json();
		local Map of String to Any is root: j:parseObjectText(text: jsonText);
		appName: j:getString(obj: root, key: 'name', default: '');
		appVersion: j:getString(obj: root, key: 'version', default: '');
		appDescription: j:getString(obj: root, key: 'description', default: '');
		usageLine: j:getString(obj: root, key: 'usage', default: '');

		local Array of Any is optsArr: j:getArray(obj: root, key: 'options');
		local Int is i: 0;
		while({ i < optsArr:length() }, {
			local Map of String to Any is o: j:getObjectAt(arr: optsArr, index: i);
			local CliOption is opt: CliOption(
				shortName: j:getString(obj: o, key: 'short', default: ''),
				longName: j:getString(obj: o, key: 'long', default: ''),
				optType: j:getString(obj: o, key: 'type', default: 'string'),
				defaultVal: j:getString(obj: o, key: 'default', default: ''),
				argLabel: j:getString(obj: o, key: 'arg', default: ''),
				description: j:getString(obj: o, key: 'description', default: ''),
				required: j:getBool(obj: o, key: 'required', default: false)
			);
			if({ opt:canonicalKey() != '' }, {
				options:push(item: opt);
			});
			i: i + 1;
		});
		ensureDefaultHelp();
	}

	local Function of CliOption is findByLong(String is name){
		local Int is i: 0;
		while({ i < options:length() }, {
			local CliOption is opt: options:get(index: i);
			if({ opt:longName == name }, { return opt; });
			i: i + 1;
		});
		return CliOption();
	}

	local Function of CliOption is findByShort(String is name){
		local Int is i: 0;
		while({ i < options:length() }, {
			local CliOption is opt: options:get(index: i);
			if({ opt:shortName == name }, { return opt; });
			i: i + 1;
		});
		return CliOption();
	}

	local Function is storeOptionValue(CliOption is opt, String is val){
		local String is k: opt:canonicalKey();
		if({ k == '' }, { return; });
		if({ opt:optType == 'list' && values:has(key: k) }, {
			local String is prev: values:getString(key: k, default: '');
			if({ prev != '' }, {
				values:set(key: k, value: prev . "\n" . val);
			}, {
				values:set(key: k, value: val);
			});
		}, {
			values:set(key: k, value: val);
		});
		if({ k == 'help' && val == 'true' }, {
			helpRequested: true;
		});
		if({ k == 'version' && val == 'true' }, {
			versionRequested: true;
		});
	}

	## Parses raw CLI arguments (`Process:rawArgs()`).
	## Returns `false` if `--help`/`--version` was handled or validation failed.
	Function of Boolean is parse(Array of String is rawArgs){
		values: Map:init();
		posArgs: Array();
		helpRequested: false;
		versionRequested: false;
		errorMessage: '';

		local Int is di: 0;
		while({ di < options:length() }, {
			local CliOption is opt: options:get(index: di);
			if({ opt:defaultVal != '' }, {
				values:set(key: opt:canonicalKey(), value: opt:defaultVal);
			});
			di: di + 1;
		});

		local Boolean is onlyPositional: false;
		local Int is i: 0;
		local Int is n: rawArgs:length();
		while({ i < n }, {
			local String is tok: rawArgs:get(index: i, default: '');
			if({ onlyPositional }, {
				posArgs:add(item: tok);
				i: i + 1;
			}, {
				if({ tok == '--' }, {
					onlyPositional: true;
					i: i + 1;
				}, {
					if({ tok:startsWith(prefix: '--') && tok:length() > 2 }, {
						local String is body: tok:substring(start: 2, end: tok:length());
						local Int is eq: body:indexOf(search: '=', default: -1);
						if({ eq > 0 }, {
							local String is name: body:substring(start: 0, end: eq);
							local String is val: body:substring(start: eq + 1, end: body:length());
							local CliOption is opt: findByLong(name: name);
							if({ opt:canonicalKey() != '' }, {
								storeOptionValue(opt: opt, val: val);
							}, {
								values:set(key: name, value: val);
							});
						}, {
							local CliOption is opt: findByLong(name: body);
							if({ opt:canonicalKey() != '' }, {
								if({ opt:optType == 'bool' }, {
									storeOptionValue(opt: opt, val: 'true');
								}, {
									if({ i + 1 < n }, {
										i: i + 1;
										storeOptionValue(opt: opt, val: rawArgs:get(index: i, default: ''));
									}, {
										errorMessage: 'missing value for --' . body;
									});
								});
							}, {
								if({ i + 1 < n && !rawArgs:get(index: i + 1, default: ''):startsWith(prefix: '-') }, {
									i: i + 1;
									values:set(key: body, value: rawArgs:get(index: i, default: ''));
								}, {
									values:set(key: body, value: 'true');
								});
							});
						});
						i: i + 1;
					}, {
						if({ tok:startsWith(prefix: '-') && tok:length() > 1 }, {
							local String is body: tok:substring(start: 1, end: tok:length());
							local Int is eq: body:indexOf(search: '=', default: -1);
							if({ eq > 0 }, {
								local String is sname: body:substring(start: 0, end: eq);
								local String is val: body:substring(start: eq + 1, end: body:length());
								local CliOption is opt: findByShort(name: sname);
								if({ opt:canonicalKey() != '' }, {
									storeOptionValue(opt: opt, val: val);
								}, {
									values:set(key: sname, value: val);
								});
							}, {
								local CliOption is opt: findByShort(name: body);
								if({ opt:canonicalKey() != '' }, {
									if({ opt:optType == 'bool' }, {
										storeOptionValue(opt: opt, val: 'true');
									}, {
										if({ i + 1 < n }, {
											i: i + 1;
											storeOptionValue(opt: opt, val: rawArgs:get(index: i, default: ''));
										}, {
											errorMessage: 'missing value for -' . body;
										});
									});
								}, {
									if({ i + 1 < n && !rawArgs:get(index: i + 1, default: ''):startsWith(prefix: '-') }, {
										i: i + 1;
										values:set(key: body, value: rawArgs:get(index: i, default: ''));
									}, {
										values:set(key: body, value: 'true');
									});
								});
							});
							i: i + 1;
						}, {
							posArgs:add(item: tok);
							i: i + 1;
						});
					});
				});
			});
		});

		return finalizeParse();
	}

	## Parses an already-built `Map of String to String` (such as `init(args:)`
	## or programmatic `Driver:init(args:)` calls), normalizing aliases and defaults.
	Function of Boolean is parseMap(Map of String to String is args){
		values: Map:init();
		posArgs: Array();
		helpRequested: false;
		versionRequested: false;
		errorMessage: '';

		local Int is di: 0;
		while({ di < options:length() }, {
			local CliOption is opt: options:get(index: di);
			if({ opt:defaultVal != '' }, {
				values:set(key: opt:canonicalKey(), value: opt:defaultVal);
			});
			di: di + 1;
		});

		local Array of String is ks: args:keys();
		local Int is ki: 0;
		while({ ki < ks:length() }, {
			local String is k: ks:get(index: ki, default: '');
			local String is val: args:getString(key: k, default: '');
			if({ k != '' }, {
				local CliOption is opt: findByLong(name: k);
				if({ opt:canonicalKey() == '' }, {
					opt: findByShort(name: k);
				});
				if({ opt:canonicalKey() != '' }, {
					if({ opt:optType == 'bool' && val == '' }, {
						val: 'true';
					});
					storeOptionValue(opt: opt, val: val);
				}, {
					values:set(key: k, value: val);
				});
			});
			ki: ki + 1;
		});

		return finalizeParse();
	}

	local Function of Boolean is finalizeParse(){
		if({ helpRequested }, {
			if({ !quiet }, {
				printHelp();
			});
			return false;
		});

		if({ versionRequested }, {
			if({ !quiet }, {
				local String is vLine: if({ appName != '' }, { appName . ' ' }, { '' }) . appVersion;
				line(text: vLine:trim());
			});
			return false;
		});

		if({ errorMessage != '' }, {
			if({ !quiet }, {
				local String is prefix: if({ appName != '' }, { appName . ': ' }, { '' });
				line(text: prefix . errorMessage);
			});
			return false;
		});

		local Int is ri: 0;
		while({ ri < options:length() }, {
			local CliOption is opt: options:get(index: ri);
			local String is k: opt:canonicalKey();
			if({ opt:required && (!values:has(key: k) || values:getString(key: k, default: '') == '') }, {
				local String is flagLabel: if({ opt:shortName != '' }, { '-' . opt:shortName }, { '--' . opt:longName });
				if({ opt:shortName != '' && opt:longName != '' }, {
					flagLabel: '-' . opt:shortName . ' (or --' . opt:longName . ')';
				});
				errorMessage: 'missing required option ' . flagLabel;
				if({ !quiet }, {
					local String is prefix: if({ appName != '' }, { appName . ': ' }, { '' });
					line(text: prefix . errorMessage);
				});
				return false;
			});
			ri: ri + 1;
		});

		return true;
	}

	## Formats the aligned `--help` text from the JSON schema.
	Function of String is formatHelp(){
		local String is out: '';
		if({ appName != '' }, {
			out: appName;
			if({ appVersion != '' }, { out: out . ' ' . appVersion; });
			if({ appDescription != '' }, { out: out . ' - ' . appDescription; });
			out: out . "\n";
		}, {
			if({ appDescription != '' }, {
				out: appDescription . "\n";
			});
		});

		if({ usageLine != '' }, {
			out: out . 'Usage: ' . usageLine . "\n";
		}, {
			if({ appName != '' }, {
				out: out . 'Usage: ' . appName . " [options]\n";
			});
		});

		if({ options:length() > 0 }, {
			out: out . "\nOptions:\n";
			local Array of String is leftCols: Array();
			local Int is maxLeft: 0;
			local Int is i: 0;
			while({ i < options:length() }, {
				local CliOption is opt: options:get(index: i);
				local String is left: '  ';
				if({ opt:shortName != '' && opt:longName != '' }, {
					left: left . '-' . opt:shortName . ', --' . opt:longName;
				}, {
					if({ opt:shortName != '' }, {
						left: left . '-' . opt:shortName;
					}, {
						left: left . '    --' . opt:longName;
					});
				});
				if({ opt:optType != 'bool' }, {
					local String is argLbl: if({ opt:argLabel != '' }, { opt:argLabel }, { 'value' });
					left: left . ' <' . argLbl . '>';
				});
				if({ left:length() > maxLeft }, { maxLeft: left:length(); });
				leftCols:add(item: left);
				i: i + 1;
			});

			local Int is padTarget: maxLeft + 2;
			i: 0;
			while({ i < options:length() }, {
				local CliOption is opt: options:get(index: i);
				local String is left: leftCols:get(index: i, default: '');
				local String is pad: '';
				local Int is p: left:length();
				while({ p < padTarget }, {
					pad: pad . ' ';
					p: p + 1;
				});
				local String is desc: opt:description;
				if({ opt:required }, {
					desc: desc . ' [required]';
				});
				if({ opt:defaultVal != '' }, {
					desc: desc . ' (default: ' . opt:defaultVal . ')';
				});
				out: out . left . pad . desc . "\n";
				i: i + 1;
			});
		});
		return out;
	}

	Function is printHelp(){
		line(text: formatHelp());
	}

	Function of Boolean is has(String is name){
		return values:has(key: name);
	}

	Function of String is getString(String is name, String is default: ''){
		return values:getString(key: name, default: default);
	}

	Function of Int is getInt(String is name, Int is default: 0){
		if({ !values:has(key: name) }, { return default; });
		return values:getString(key: name, default: ''):parseInt(default: default);
	}

	Function of Boolean is getBool(String is name){
		if({ !values:has(key: name) }, { return false; });
		local String is v: values:getString(key: name, default: ''):toLower();
		return v == 'true' || v == '1' || v == 'yes';
	}

	Function of Array of String is getList(String is name){
		local Array of String is out: Array();
		if({ !values:has(key: name) }, { return out; });
		local String is raw: values:getString(key: name, default: '');
		if({ raw == '' }, { return out; });
		local Array of String is parts: raw:split(delimiter: "\n");
		local Int is i: 0;
		while({ i < parts:length() }, {
			local String is item: parts:get(index: i, default: '');
			if({ item != '' }, {
				out:add(item: item);
			});
			i: i + 1;
		});
		return out;
	}

	Function of Array of String is positionals(){
		return posArgs;
	}

	Function of Map of String to String is allValues(){
		return values;
	}
}
