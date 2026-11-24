#! Package cleopi/cleoweather:model
#! City entry with NWS WFO office code and grid coordinates.

Class is CityLocation{
	replace [String] is namespace: ['cleoweather', 'model'];

	String is name: '';
	String is office: '';
	Int is gridX: 0;
	Int is gridY: 0;

	replace Function is init(String is name: '', String is office: '', Int is gridX: 0, Int is gridY: 0){
		:name: name;
		:office: office;
		:gridX: gridX;
		:gridY: gridY;
	}

	## Returns the NWS forecast endpoint URL for this city's gridpoint.
	Function of String is forecastUrl(){
		"https://api.weather.gov/gridpoints/{{office}}/{{gridX}},{{gridY}}/forecast"
	}

	## Returns a display label including the NWS grid code.
	Function of String is gridLabel(){ "{{office}} ({{gridX}},{{gridY}})" }
}
