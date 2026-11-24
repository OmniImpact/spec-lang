#! Package cleoweather:model
#! Parses raw NWS `/gridpoints/.../forecast` JSON into [ForecastReport] models.

Class is ForecastParser{
	replace [String] is namespace: ['cleoweather', 'model'];

	merge [[String]] is using: [
		['base', 'core', [Result, SpecError]],
		['base', 'data', [JsonError, as Json()]],
		['base', 'struct', [Array, Map]],
		['cleoweather', 'model', [ForecastPeriod, ForecastReport]]
	];

	## Parses [rawJson] into a [ForecastReport], capturing any JSON error in [ForecastReport:errorMessage].
	Function of ForecastReport is parse(String is rawJson){
		local Result of Map of String to Any to JsonError is rootR: parseMapResult(text: rawJson);
		local Map of String to Any is root: Map:init();
		local String is parseMsg: '';
		match(on: rootR, when: [
			Result:Ok: local Function of Void(Map of String to Any is v){
				root: v;
			},
			Result:Err: local Function of Void(SpecError of JsonError is e){
				parseMsg: e:description;
			}
		]);
		if({ parseMsg != '' }, {
			return ForecastReport(errorMessage: "JSON parse error: {{parseMsg}}");
		});

		local Map is props: getObject(obj: root, key: 'properties');
		local String is updated: getString(obj: props, key: 'updateTime', default: getString(obj: props, key: 'updated', default: 'unknown'));
		local Array is rawPeriods: getArray(obj: props, key: 'periods');
		local [ForecastPeriod] is periods: [];
		local Int is i: 0;
		while({ i < rawPeriods:length() }, {
			local Map is p: getObjectAt(arr: rawPeriods, index: i);
			periods:push(item: ForecastPeriod(
				name: getString(obj: p, key: 'name', default: '?'),
				temperature: getInt(obj: p, key: 'temperature', default: 0),
				temperatureUnit: getString(obj: p, key: 'temperatureUnit', default: 'F'),
				windSpeed: getString(obj: p, key: 'windSpeed', default: ''),
				windDirection: getString(obj: p, key: 'windDirection', default: ''),
				shortForecast: getString(obj: p, key: 'shortForecast', default: '')
			));
			i: i + 1;
		});
		return ForecastReport(updatedAt: updated, periods: periods);
	}
}
