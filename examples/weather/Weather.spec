#! Weather forecast proof-of-concept using base:net:Http and base:data:Json.
#! Fetches https://api.weather.gov/gridpoints/RAH/74,58/forecast on a worker
#! thread with callbacks and displays a forecast summary.

Class is Weather{
	replace Array of Array of String is using: [
		['base', 'core', SpecError],
		['base', 'net', HttpResponse],
		['base', 'net', as Http()],
		['base', 'data', as Json()],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Output()],
		['base', 'struct', Array],
		['base', 'struct', Map]
	];

	replace Function of Boolean is SpecErrorHandler(SpecError is error){
		Output:line('Unhandled error: ' . error:toString());
		return true;
	}

	replace Function is init(){
		local String is url: 'https://api.weather.gov/gridpoints/RAH/74,58/forecast';
		Output:line('Fetching forecast from ' . url . ' ...');

		ThreadScope:open(body: local Function(ThreadScope is scope){
			Http:get(
				scope: scope,
				url: url,
				onSuccess: local Function(HttpResponse is resp){
					:displayForecast(rawJson: resp:body);
				},
				onError: local Function(String is err){
					Output:line('Error fetching forecast: ' . err);
				}
			);
		});
	}

	Function is displayForecast(String is rawJson){
		local Any is rootAny: Json:parse(text: rawJson);
		if({ Json:hasError() }, {
			Output:line('JSON parse error: ' . Json:errorMessage());
			return;
		});
		local Map is root: rootAny as Map;
		local Map is props: Json:getObject(obj: root, key: 'properties');
		local String is updated: Json:getString(obj: props, key: 'updateTime', default: Json:getString(obj: props, key: 'updated', default: 'unknown'));
		local Array is periods: Json:getArray(obj: props, key: 'periods');

		Output:line('');
		Output:line('=== Raleigh / RAH (74,58) Forecast ===');
		Output:line('Updated: ' . updated);
		Output:line('');

		local Int is limit: if({ periods:length() < 6 }, { periods:length() }, { 6 });
		local Int is i: 0;
		while({ i < limit }, {
			local Map is p: Json:getObjectAt(arr: periods, index: i);
			local String is name: Json:getString(obj: p, key: 'name', default: '?');
			local Int is temp: Json:getInt(obj: p, key: 'temperature', default: 0);
			local String is unit: Json:getString(obj: p, key: 'temperatureUnit', default: 'F');
			local String is wind: Json:getString(obj: p, key: 'windSpeed', default: '');
			local String is dir: Json:getString(obj: p, key: 'windDirection', default: '');
			local String is shortFc: Json:getString(obj: p, key: 'shortForecast', default: '');
			Output:line('  ' . name . ': ' . (temp as String) . '°' . unit . ' | ' . shortFc . ' | Wind ' . wind . ' ' . dir);
			i: i + 1;
		});
	}
}
