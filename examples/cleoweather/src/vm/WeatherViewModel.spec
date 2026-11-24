#! Package cleoweather:vm
#! ViewModel managing US state/city selection, NWS forecast fetching, and presentation state.

Class is WeatherViewModel{
	replace [String] is namespace: ['cleoweather', 'vm'];

	merge [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'net', [HttpError, HttpResponse, as Http()]],
		['base', 'sys', 'thread', ThreadScope],
		['cleoweather', 'model', [CityLocation, ForecastParser, ForecastPeriod, ForecastReport, LocationLoader, StateGroup]]
	];

	[StateGroup] is states: [];
	Int is selectedStateIdx: -1;
	Int is selectedCityIdx: -1;
	Int is httpStatusCode: 0;
	String is fetchError: '';
	ForecastReport is report: ForecastReport();
	local ForecastParser is parser: ForecastParser();

	replace Function is init(String is locationsPath: 'locations.json'){
		local LocationLoader is loader: LocationLoader(filePath: locationsPath);
		states: loader:loadStates();
		if({ states:length() > 0 }, {
			selectedStateIdx: 0;
			if({ states:get(index: 0):cities:length() > 0 }, {
				selectedCityIdx: 0;
			});
		});
	}

	Function of Boolean is hasStates(){ states:length() > 0 }

	Function of StateGroup is selectedState(){
		if({ selectedStateIdx >= 0 && selectedStateIdx < states:length() }, {
			return states:get(index: selectedStateIdx);
		});
		return StateGroup();
	}

	Function of CityLocation is selectedCity(){
		local StateGroup is st: selectedState();
		if({ selectedCityIdx >= 0 && selectedCityIdx < st:cities:length() }, {
			return st:cities:get(index: selectedCityIdx);
		});
		return CityLocation();
	}

	Function of String is forecastUrl(){ selectedCity():forecastUrl() }

	Function of String is forecastTitle(){
		local StateGroup is st: selectedState();
		local CityLocation is city: selectedCity();
		return " {{city:name}}, {{st:code}} · {{city:gridLabel()}} Forecast ";
	}

	local Function of Int is parseOneBasedIndex(String is raw, Int is limit){
		local String is trimmed: raw:trim();
		if({ trimmed == '' }, { return -1; });
		local Int is n: trimmed:parseInt(default: 0);
		if({ n >= 1 && n <= limit }, { return n - 1; });
		return -1;
	}

	## Selects a state by 1-based number, 2-letter code, or full name. Returns true on match.
	Function of Boolean is selectStateByInput(String is input){
		local String is q: input:trim():toLower();
		if({ q == '' }, { return false; });
		local Int is idx: parseOneBasedIndex(raw: q, limit: states:length());
		if({ idx >= 0 }, {
			selectedStateIdx: idx;
			selectedCityIdx: 0;
			return true;
		});
		local Int is i: 0;
		while({ i < states:length() }, {
			local StateGroup is st: states:get(index: i);
			if({ st:code:toLower() == q || st:name:toLower() == q }, {
				selectedStateIdx: i;
				selectedCityIdx: 0;
				return true;
			});
			i: i + 1;
		});
		return false;
	}

	## Selects a city in the current state by 1-based number or name. Returns true on match.
	Function of Boolean is selectCityByInput(String is input){
		local StateGroup is st: selectedState();
		local String is q: input:trim():toLower();
		if({ q == '' }, { return false; });
		local Int is idx: parseOneBasedIndex(raw: q, limit: st:cities:length());
		if({ idx >= 0 }, {
			selectedCityIdx: idx;
			return true;
		});
		local Int is i: 0;
		while({ i < st:cities:length() }, {
			if({ st:cities:get(index: i):name:toLower() == q }, {
				selectedCityIdx: i;
				return true;
			});
			i: i + 1;
		});
		return false;
	}

	## Fetches the NWS forecast for the selected city on [scope] and invokes [onDone].
	Function is fetchForecast(ThreadScope is scope, Function is onDone){
		local String is url: forecastUrl();
		httpStatusCode: 0;
		fetchError: '';
		get(
			scope: scope,
			url: url,
			onSuccess: local Function(HttpResponse is resp){
				httpStatusCode: resp:statusCode;
				report: parser:parse(rawJson: resp:body);
				onDone();
			},
			onError: local Function(SpecError of HttpError is err){
				fetchError: err:description;
				onDone();
			}
		);
	}
}
