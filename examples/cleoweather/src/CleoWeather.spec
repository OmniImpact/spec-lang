#! Package cleoweather
#! CLI entry point for CleoWeather: two-step US state & city NWS forecast viewer using Cleo + MVVM.

Class is CleoWeather{
	replace [String] is namespace: ['cleoweather'];

	merge [[String]] is using: [
		['base', 'cli', Cli],
		['base', 'struct', Map],
		['base', 'sys', [as Output(), as Process()]],
		['base', 'sys', as Conditional()],
		['cleoweather', 'vm', WeatherViewModel],
		['cleoweather', 'view', [CleoForecastView, CleoSelectorView]]
	];

	replace Function is init(Map of String to String is args){
		local Cli is cli: Cli():loadFromBundle(bundlePath: 'cli.json', fallbackPath: 'examples/cleoweather/cli.json');
		cli:parseOrExit();

		local WeatherViewModel is vm: WeatherViewModel();
		if({ !vm:hasStates() }, {
			line('Error: could not load locations.json');
			return;
		});

		local String is stateArg: cli:getString(name: 'state', default: '');
		local String is cityArg: cli:getString(name: 'city', default: '');
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
