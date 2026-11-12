#! specunit: negative
#! expect: No exact overload of 'N14NoExact.f' for (Any)

#! N14: an Any-typed argument matches no overload exactly (§I.2).

Class is N14NoExact {
	Function of Int is f(Int is v){
		return v;
	}

	Function of Float is f(Float is v){
		return v;
	}

	replace Function is init(Map of String to String is args){
		local Any is anything: 1;
		local Int is x: f(anything);
		Output:line((x as String));
	}
}
