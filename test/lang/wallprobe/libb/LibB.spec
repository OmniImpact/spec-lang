#! Package wallprobe:libb

Class is LibB{
	namespace: ['wallprobe', 'libb'];

	## The function the as-import grants bare.
	Function of Int is quad(Int is n){
		return n * 4;
	}

	Class is Helper{
		Function of Int is value(){
			return 2;
		}
	}
}
