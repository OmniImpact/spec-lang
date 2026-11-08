#! N12: identical-signature overloads are the duplicate error (FUNCTIONS.md §I.1).

Class is N12Identical {
	Function of Int is f(Int is v){
		return v;
	}

	Function of Int is f(Int is v){
		return v + 1;
	}

	replace Function is init(Map of String to String is args){}
}
