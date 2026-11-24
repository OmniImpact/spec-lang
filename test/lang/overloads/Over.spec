#! Package ovl:lib
#! Overload fixture (§I): arity-distinct, type-distinct,
#! and constructor overloads on one class.

Class is Over{
	replace [String] is namespace: ['ovl', 'lib'];
	local Int is seed: 0;

	Function of Int is twice(Int is v){
		return v * 2;
	}

	Function of String is twice(String is s){
		return s . s;
	}

	Function of Int is sum(Int is a){
		return a;
	}

	Function of Int is sum(Int is a, Int is b){
		return a + b;
	}

	replace Function is init(){
	}

	replace Function is init(Int is start){
		:seed: start;
	}

	Function of Int is seedValue(){
		return :seed;
	}
}
