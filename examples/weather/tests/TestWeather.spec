#! Offline unit tests for the weather example's forecast JSON formatting.

Class of SpecUnitTest is TestWeather{
	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', as Assert()],
		['base', 'data', as Json()],
		['base', 'struct', Map],
		['base', 'struct', Array]
	];

	Function is testParseAndFormatNwsForecast(){
		local String is sample: '{"properties":{"updateTime":"2026-11-19T06:30:00Z","periods":[{"name":"Today","temperature":68,"temperatureUnit":"F","windSpeed":"5 mph","windDirection":"NE","shortForecast":"Sunny"}]}}';
		local Any is rootAny: Json:parse(text: sample);
		Assert:isFalse(Json:hasError());
		local Map is root: rootAny as Map;
		local Map is props: Json:getObject(obj: root, key: 'properties');
		Assert:areEqualString('2026-11-19T06:30:00Z', Json:getString(obj: props, key: 'updateTime', default: ''));
		local Array is periods: Json:getArray(obj: props, key: 'periods');
		Assert:areEqualInt(1, periods:length());
		local Map is p: Json:getObjectAt(arr: periods, index: 0);
		Assert:areEqualString('Today', Json:getString(obj: p, key: 'name', default: ''));
		Assert:areEqualInt(68, Json:getInt(obj: p, key: 'temperature', default: 0));
		Assert:areEqualString('Sunny', Json:getString(obj: p, key: 'shortForecast', default: ''));
	}
}
