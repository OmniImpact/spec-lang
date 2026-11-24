#! Package cleoweather:model
#! US state entry containing major cities and their NWS grid coordinates.

Class is StateGroup{
	replace [String] is namespace: ['cleoweather', 'model'];

	merge [[String]] is using: [
		['cleoweather', 'model', CityLocation]
	];

	String is code: '';
	String is name: '';
	[CityLocation] is cities: [];

	replace Function is init(String is code: '', String is name: '', [CityLocation] is cities: []){
		:code: code;
		:name: name;
		:cities: cities;
	}

	Function of String is displayLabel(){ "{{code}} - {{name}}" }
}
