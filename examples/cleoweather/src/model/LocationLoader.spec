#! Package cleoweather:model
#! Loads US states and major cities with NWS grid coordinates from `locations.json`.

Class is LocationLoader{
	replace [String] is namespace: ['cleoweather', 'model'];

	merge [[String]] is using: [
		['base', 'core', [Result, SpecError]],
		['base', 'data', [JsonError, as Json()]],
		['base', 'struct', [Array, Map]],
		['base', 'sys', [Bundle, as File()]],
		['cleoweather', 'model', [CityLocation, StateGroup]]
	];

	String is filePath: 'locations.json';

	replace Function is init(String is filePath: 'locations.json'){
		:filePath: filePath;
	}

	## Resolves [filePath] locally or relative to the repository root.
	Function of String is resolvePath(){
		if({ fileExists(path: filePath) }, { return filePath; });
		if({ fileExists(path: 'examples/cleoweather/locations.json') }, { return 'examples/cleoweather/locations.json'; });
		return filePath;
	}

	## Loads all states and their cities from the configured JSON file.
	Function of [StateGroup] is loadStates(){
		local [StateGroup] is out: [];
		local String is raw: '';
		local String is diskPath: resolvePath();
		if({ fileExists(path: diskPath) }, {
			raw: fileRead(path: diskPath, default: '');
		});
		if({ raw == '' }, {
			raw: Bundle():readText(path: filePath, default: '');
		});
		if({ raw == '' }, { return out; });

		local Result of Map of String to Any to JsonError is rootR: parseMapResult(text: raw);
		local Map of String to Any is root: Map:init();
		local Boolean is ok: false;
		match(on: rootR, when: [
			Result:Ok: local Function of Void(Map of String to Any is v){
				root: v;
				ok: true;
			},
			Result:Err: local Function of Void(SpecError of JsonError is _e){ }
		]);
		if({ !ok }, { return out; });

		local Array is statesArr: getArray(obj: root, key: 'states');
		local Int is si: 0;
		while({ si < statesArr:length() }, {
			local Map is stObj: getObjectAt(arr: statesArr, index: si);
			local String is code: getString(obj: stObj, key: 'code', default: '');
			local String is name: getString(obj: stObj, key: 'name', default: '');
			local Array is citiesArr: getArray(obj: stObj, key: 'cities');
			local [CityLocation] is cities: [];
			local Int is ci: 0;
			while({ ci < citiesArr:length() }, {
				local Map is cObj: getObjectAt(arr: citiesArr, index: ci);
				cities:push(item: CityLocation(
					name: getString(obj: cObj, key: 'name', default: ''),
					office: getString(obj: cObj, key: 'office', default: ''),
					gridX: getInt(obj: cObj, key: 'gridX', default: 0),
					gridY: getInt(obj: cObj, key: 'gridY', default: 0)
				));
				ci: ci + 1;
			});
			if({ code != '' && name != '' && cities:length() > 0 }, {
				out:push(item: StateGroup(code: code, name: name, cities: cities));
			});
			si: si + 1;
		});
		return out;
	}
}
