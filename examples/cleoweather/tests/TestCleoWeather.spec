#! specunit: suite

Class of SpecUnitTest is TestCleoWeather{
	replace [String] is namespace: ['cleoweather', 'tests'];

	merge [[String]] is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['cleoweather', 'model', [CityLocation, ForecastParser, ForecastPeriod, ForecastReport, LocationLoader, StateGroup]],
		['cleoweather', 'vm', WeatherViewModel]
	];

	Function is testLoadLocationsJson(){
		local LocationLoader is loader: LocationLoader();
		local [StateGroup] is states: loader:loadStates();
		Assert:isTrue(states:length() >= 10);

		local StateGroup is first: states:get(index: 0);
		Assert:isTrue(first:code != '');
		Assert:isTrue(first:cities:length() >= 3);
		local CityLocation is city: first:cities:get(index: 0);
		Assert:isTrue(city:forecastUrl():startsWith(prefix: 'https://api.weather.gov/gridpoints/'));
	}

	Function is testStateAndCitySelection(){
		local WeatherViewModel is vm: WeatherViewModel();
		Assert:isTrue(vm:hasStates());
		Assert:isTrue(vm:selectStateByInput(input: 'NC'));
		Assert:areEqualString('NC', vm:selectedState():code);
		Assert:isTrue(vm:selectCityByInput(input: 'Raleigh'));
		Assert:areEqualString('Raleigh', vm:selectedCity():name);
		Assert:areEqualString('https://api.weather.gov/gridpoints/RAH/74,58/forecast', vm:forecastUrl());
		Assert:areEqualString(' Raleigh, NC · RAH (74,58) Forecast ', vm:forecastTitle());

		Assert:isFalse(vm:selectStateByInput(input: 'ZZ'));
		Assert:isFalse(vm:selectCityByInput(input: 'Atlantis'));
	}

	Function is testParseAndFormatNwsForecast(){
		local String is sample: '{"properties":{"updateTime":"2026-11-19T06:30:00Z","periods":[{"name":"Today","temperature":68,"temperatureUnit":"F","windSpeed":"5 mph","windDirection":"NE","shortForecast":"Sunny"}]}}';
		local ForecastParser is parser: ForecastParser();
		local ForecastReport is report: parser:parse(rawJson: sample);
		Assert:isTrue(report:isOk());
		Assert:areEqualString('2026-11-19T06:30:00Z', report:updatedAt);
		Assert:areEqualInt(1, report:periods:length());
		local ForecastPeriod is p: report:periods:get(index: 0);
		Assert:areEqualString('Today: 68°F · Sunny', p:summaryText());
		Assert:areEqualString('Wind NE 5 mph', p:windText());
	}
}
