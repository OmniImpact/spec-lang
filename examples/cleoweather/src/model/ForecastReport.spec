#! Package cleoweather:model
#! Parsed NWS forecast response containing update timestamp, periods, and optional error message.

Class is ForecastReport{
	replace [String] is namespace: ['cleoweather', 'model'];

	merge [[String]] is using: [
		['cleoweather', 'model', ForecastPeriod]
	];

	String is updatedAt: '';
	[ForecastPeriod] is periods: [];
	String is errorMessage: '';

	replace Function is init(String is updatedAt: '', [ForecastPeriod] is periods: [], String is errorMessage: ''){
		:updatedAt: updatedAt;
		:periods: periods;
		:errorMessage: errorMessage;
	}

	Function of Boolean is isOk(){ errorMessage == '' }
}
