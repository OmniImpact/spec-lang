#! specunit: suite

Class of SpecUnitTest is TestNegativeReceivers{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', Assert]
	];

	## N1: Calling own members through the class name is banned (must use self).
	Function is testOwnNameReceiverInsideClass(){
		Assert:compilerRejects(
			source: '''
Class is N1SelfRead{
	local Int is count: 5;
	Function of Int is bump(){ return self:count + 1; }
	replace Function is init(Map of String to String is args){
		local Int is v: N1SelfRead:bump();
	}
}
''',
			expect: "through the class name inside 'N1SelfRead' itself; use self"
		);
	}

	## N2: Bare call with zero providers is rejected.
	Function is testUndefinedBareCall(){
		Assert:compilerRejects(
			source: '''
Class is N2UndefinedBare{
	replace Function is init(Map of String to String is args){
		nope();
	}
}
''',
			expect: "Undefined function 'nope' on class 'N2UndefinedBare'"
		);
	}

	## N3: Bare call with multiple providers must qualify.
	Function is testAmbiguousBareCollision(){
		Assert:compilerRejects(
			source: '''
Class is N3Collision{
	replace Array of Array of String is using: [
		['base', 'math', as Math()]
	];
	Function of Int is round(){ return 1; }
	replace Function is init(Map of String to String is args){
		round();
	}
}
''',
			expect: "provided by the enclosing class and Math; qualify the call"
		);
	}

	## N10: Calling init on an instance is banned (construct-only).
	Function is testInitOnInstanceReceiver(){
		Assert:compilerRejects(
			source: '''
Class is N10InitOnInstance{
	replace Function is init(Map of String to String is args){
		local N10InitOnInstance is again: N10InitOnInstance:init();
		again:init();
	}
}
''',
			expect: "'init' is construct-only"
		);
	}

	## N11: Fields are not reachable through a class-name prefix.
	Function is testFieldThroughClassPrefix(){
		Assert:compilerRejects(
			source: '''
Class is Target{
	Int is n: 5;
}
Class is N11PrefixField{
	replace Function is init(Map of String to String is args){
		local Int is x: Target:n;
	}
}
''',
			expect: "Fields are not reachable through the class-name prefix"
		);
	}
}
