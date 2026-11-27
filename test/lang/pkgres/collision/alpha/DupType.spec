#! specunit: helper

Class is DupType{
	replace [String] is namespace: ['test', 'lang', 'pkgres', 'collision', 'alpha'];

	Int is x: 10;

	replace Function is init(Int is x: 10){
		:x: x;
	}

	Function of Int is value(){
		return x;
	}
}
