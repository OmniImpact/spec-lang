#! Package wallprobe:liba

Class is LibA{
	namespace: ['wallprobe', 'liba'];

	## The function the as-import grants bare.
	Function of Int is triple(Int is n){
		return n * 3;
	}

	## The nested class: importable through LibA's as-import.
	Class is Helper{
		Function of Int is value(){
			return 1;
		}
	}
}
