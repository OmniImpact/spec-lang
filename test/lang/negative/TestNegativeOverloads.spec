#! specunit: negative-suite

#! case: testIdenticalSignaturesDuplicate
#! expect: declare identical signatures
Class is N12Identical{
	Function of Int is f(Int is v){ return v; }
	Function of Int is f(Int is v){ return v + 1; }
	replace Function is init(Map of String to String is args){}
}

#! case: testAmbiguousPositionalCall
#! expect: the arguments match multiple overloads; use named arguments
Class is N13Ambiguous{
	Function of Int is f(Int is a){ return a; }
	Function of Int is f(Int is b){ return b; }
	replace Function is init(Map of String to String is args){
		local Int is x: f(1);
	}
}

#! case: testNoExactMatchForAny
#! expect: No exact overload of 'N14NoExact.f' for (Any)
Class is N14NoExact{
	Function of Int is f(Int is v){ return v; }
	Function of Float is f(Float is v){ return v; }
	replace Function is init(Map of String to String is args){
		local Any is anything: 1;
		local Int is x: f(anything);
	}
}

#! case: testMixedPositionalAndNamed
#! expect: Mixed positional and named arguments are not supported
Class is N15Mixed{
	Function of Int is f(Int is a, Int is b){ return a + b; }
	replace Function is init(Map of String to String is args){
		local Int is x: f(1, b: 2);
	}
}

#! case: testCannotReplaceOverloadedMethod
#! expect: Cannot replace or merge an overloaded method
Class is N16Parent{
	Function of Int is f(Int is v){ return v; }
	Function of String is f(String is v){ return v; }
	replace Function is init(Map of String to String is args){}
}
Class of N16Parent is N16Child{
	replace Function of Int is f(Int is v){ return v; }
	replace Function is init(Map of String to String is args){}
}

#! case: testMergeRequirements
#! expect: must contain a forward statement
Class is MergeBase{
	replace Function of Int is signal(){ return 1; }
	local Int is count: 1;
}
Class of MergeBase is MergeChild{
	merge Function of Int is signal(){ return 2; }
	merge Int is count: 2;
	merge Function is orphan(){ (); }
}
Class is App{
	replace Function is init(Map of String to String is args){}
}

#! case: testMergeFunctionValidation
#! expect: cannot assign 'String' to 'Int'
Class is FwdBase{
	replace Function of Int is double(Int is n){ return n * 2; }
}
Class of FwdBase is FwdChild{
	merge Function of Int is double(Int is n){
		(n: 'not-a-number');
	}
}
Class is App{
	replace Function is init(Map of String to String is args){}
}
