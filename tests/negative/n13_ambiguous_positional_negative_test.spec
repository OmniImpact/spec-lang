#! N13: same-arity overloads whose parameters share types are ambiguous
#! for positional calls (FUNCTIONS.md §I.2).

Class is N13Ambiguous {
	Function of Int is f(Int is a){
		return a;
	}

	Function of Int is f(Int is b){
		return b;
	}

	replace Function is init(Map of String to String is args){
		local Int is x: f(1);
		Output:line((x as String));
	}
}
