#! N16: a parent's overloaded method cannot be replaced — the virtual
#! machinery is name-keyed (§I.3).

Class is N16Parent {
	Function of Int is f(Int is v){
		return v;
	}

	Function of String is f(String is v){
		return v;
	}

	replace Function is init(Map of String to String is args){}
}

Class of N16Parent is N16Child {
	replace Function of Int is f(Int is v){
		return v;
	}

	replace Function is init(Map of String to String is args){}
}
