#! Package cleoweather
#! CLI entry point for CleoWeather: two-step US state & city NWS forecast viewer using Cleo + MVVM.

Class is CleoWeather{
	replace [String] is namespace: ['cleoweather'];

	merge [[String]] is using: [
		['base', 'struct', Map],
		['base', 'sys', as Output()],
		['cleoweather', 'vm', WeatherViewModel],
		['cleoweather', 'view', [CleoForecastView, CleoSelectorView]]
	];

	replace Function is init(Map of String to String is args){
		local WeatherViewModel is vm: WeatherViewModel();
		if({ !vm:hasStates() }, {
			line('Error: could not load locations.json');
			return;
		});

		local String is stateArg: args:getString(key: 'state', default: '');
		local String is cityArg: args:getString(key: 'city', default: '');
		local CleoSelectorView is selector: CleoSelectorView();

		if({ stateArg != '' && vm:selectStateByInput(input: stateArg) }, {
			if({ cityArg == '' || !vm:selectCityByInput(input: cityArg) }, {
				selector:chooseCity(vm: vm);
			});
		}, {
			selector:chooseState(vm: vm);
			selector:chooseCity(vm: vm);
		});

		local CleoForecastView is forecastView: CleoForecastView();
		forecastView:show(vm: vm);
	}
}
