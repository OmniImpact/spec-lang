#! specunit: suite

Class of SpecUnitTest is TestNegativeHeld{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', Assert]
	];

	## N30: Held members are read-only single copies.
	Function is testHeldMembersReadOnly(){
		Assert:compilerRejects(
			source: '''
Class is N30Walls{
	held String is label: 'wall';
	replace Function is init(){
		N30Walls:label: 'mutated';
	}
}
''',
			expect: "is read-only: held members are class-scoped single copies"
		);
	}

	## N30: Held members cannot be replaced.
	Function is testHeldCannotBeReplaced(){
		Assert:compilerRejects(
			source: '''
Class is N30Base{
	held String is label: 'base';
}
Class of N30Base is N30Child{
	held replace String is label: 'sub';
}
Class is App{ replace Function is init(Map of String to String is args){} }
''',
			expect: "combines 'held' with 'replace'/'merge'"
		);
	}

	## N30: Self inside a held initializer is forbidden.
	Function is testSelfInsideHeldInitializer(){
		Assert:compilerRejects(
			source: '''
Class is N30Self{
	held String is label: 'seed';
	held String is fromSelf: self:label;
	replace Function is init(Map of String to String is args){}
}
''',
			expect: "'self' is not available"
		);
	}

	## N30: Same-class held reference inside held initializer deadlocks once-guards.
	Function is testSameClassHeldCycle(){
		Assert:compilerRejects(
			source: '''
Class is N30Cycle{
	held String is a: N30Cycle:b . '!';
	held String is b: 'seed';
	replace Function is init(Map of String to String is args){}
}
''',
			expect: "of the same class; the once-guards would deadlock"
		);
	}

	## N30: Held member reached through an instance receiver is rejected.
	Function is testHeldInstanceReceiverStrictness(){
		Assert:compilerRejects(
			source: '''
Class is Target{
	held String is label: 'target';
}
Class is Probe{
	replace Function is init(Target is t){
		local String is s: t:label;
	}
}
''',
			expect: "reach it through the class name, not an instance"
		);
	}

	## N31: Held functions cannot overload.
	Function is testHeldFunctionsDoNotOverload(){
		Assert:compilerRejects(
			source: '''
Class is N31Fn{
	held Function of Int is twice(Int is a){ return a * 2; }
	held Function of Int is twice(Int is a, Int is b){ return a + b; }
	replace Function is init(Map of String to String is args){}
}
''',
			expect: "held functions do not overload"
		);
	}

	## N31: Held function body has no instance: self is not available.
	Function is testHeldFunctionNoSelf(){
		Assert:compilerRejects(
			source: '''
Class is N31NoSelf{
	held Int is scale: 2;
	held Function of Int is usesSelf(){
		return self:scale;
	}
	replace Function is init(Map of String to String is args){}
}
''',
			expect: "A held member body has no instance: 'self' is not available"
		);
	}

	## N32: Held resolver contract signature must be exact.
	Function is testHeldResolverSignature(){
		Assert:compilerRejects(
			source: '''
Class is N32Bad{
	held Function of Int is resolveHeld(String is name, Function of String is missing){
		return 1;
	}
	replace Function is init(Map of String to String is args){}
}
''',
			expect: "must be declared exactly 'held Function of <T> is resolveHeld(String is name, Function of <T> is missing)'"
		);
	}

	## N32: Held resolver cannot resolve through its own class prefix.
	Function is testHeldResolverSelfLoop(){
		Assert:compilerRejects(
			source: '''
Class is N32Loop{
	held Function of Int is resolveHeld(String is name, Function of Int is missing){
		return N32Loop:neverDeclared;
	}
	replace Function is init(Map of String to String is args){}
}
''',
			expect: "The resolution hook cannot resolve through its own class prefix"
		);
	}
}
