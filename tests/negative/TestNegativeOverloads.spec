#! specunit: suite

Class of SpecUnitTest is TestNegativeOverloads{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', Assert]
	];

	## N12: Identical-signature overloads are rejected as duplicate declarations.
	Function is testIdenticalSignaturesDuplicate(){
		Assert:compilerRejects(
			source: '''
Class is N12Identical{
	Function of Int is f(Int is v){ return v; }
	Function of Int is f(Int is v){ return v + 1; }
	replace Function is init(Map of String to String is args){}
}
''',
			expect: "declare identical signatures"
		);
	}

	## N13: Same-arity overloads sharing types are ambiguous for positional calls.
	Function is testAmbiguousPositionalCall(){
		Assert:compilerRejects(
			source: '''
Class is N13Ambiguous{
	Function of Int is f(Int is a){ return a; }
	Function of Int is f(Int is b){ return b; }
	replace Function is init(Map of String to String is args){
		local Int is x: f(1);
	}
}
''',
			expect: "the arguments match multiple overloads; use named arguments"
		);
	}

	## N14: Any-typed argument matches no overload exactly.
	Function is testNoExactMatchForAny(){
		Assert:compilerRejects(
			source: '''
Class is N14NoExact{
	Function of Int is f(Int is v){ return v; }
	Function of Float is f(Float is v){ return v; }
	replace Function is init(Map of String to String is args){
		local Any is anything: 1;
		local Int is x: f(anything);
	}
}
''',
			expect: "No exact overload of 'N14NoExact.f' for (Any)"
		);
	}

	## N15: Mixing positional and named arguments is rejected.
	Function is testMixedPositionalAndNamed(){
		Assert:compilerRejects(
			source: '''
Class is N15Mixed{
	Function of Int is f(Int is a, Int is b){ return a + b; }
	replace Function is init(Map of String to String is args){
		local Int is x: f(1, b: 2);
	}
}
''',
			expect: "Mixed positional and named arguments are not supported"
		);
	}

	## N16: Parent's overloaded method cannot be replaced.
	Function is testCannotReplaceOverloadedMethod(){
		Assert:compilerRejects(
			source: '''
Class is N16Parent{
	Function of Int is f(Int is v){ return v; }
	Function of String is f(String is v){ return v; }
	replace Function is init(Map of String to String is args){}
}
Class of N16Parent is N16Child{
	replace Function of Int is f(Int is v){ return v; }
	replace Function is init(Map of String to String is args){}
}
''',
			expect: "Cannot replace or merge an overloaded method"
		);
	}

	## Merge rules: forward statement required, array required, parent exists.
	Function is testMergeRequirements(){
		Assert:compilerRejects(
			source: '''
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
''',
			expect: "must contain a forward statement"
		);
	}

	## Merge function validation: forwarding checks and argument types.
	Function is testMergeFunctionValidation(){
		Assert:compilerRejects(
			source: '''
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
''',
			expect: "cannot assign 'String' to 'Int'"
		);
	}
}
