#! Package cleoweather:model
#! Single NWS forecast period (e.g., Today, Tonight, Wednesday).

Class is ForecastPeriod{
	replace [String] is namespace: ['cleoweather', 'model'];

	String is name: '';
	Int is temperature: 0;
	String is temperatureUnit: 'F';
	String is windSpeed: '';
	String is windDirection: '';
	String is shortForecast: '';

	replace Function is init(
		String is name: '',
		Int is temperature: 0,
		String is temperatureUnit: 'F',
		String is windSpeed: '',
		String is windDirection: '',
		String is shortForecast: ''
	){
		:name: name;
		:temperature: temperature;
		:temperatureUnit: temperatureUnit;
		:windSpeed: windSpeed;
		:windDirection: windDirection;
		:shortForecast: shortForecast;
	}

	Function of String is summaryText(){ "{{name}}: {{temperature}}°{{temperatureUnit}} · {{shortForecast}}" }

	Function of String is windText(){
		if({ windSpeed == '' }, { return ''; });
		if({ windDirection == '' }, { return "Wind {{windSpeed}}"; });
		return "Wind {{windDirection}} {{windSpeed}}";
	}
}
