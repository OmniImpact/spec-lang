#! Package wallprobe:liba

Class is LibA{
	namespace: ['wallprobe', 'liba'];

	## The nested class: importable through LibA's as-import.
	Class is Helper{
		Function of Int is value(){
			return 1;
		}
	}
}
