#! specunit: negative-suite

#! case: testHeldMembersReadOnly
#! expect: is read-only: held members are class-scoped single copies
Class is N30Walls{
	held String is label: 'wall';
	replace Function is init(){
		N30Walls:label: 'mutated';
	}
}

#! case: testHeldCannotBeReplaced
#! expect: combines 'held' with 'replace'/'merge'
Class is N30Base{
	held String is label: 'base';
}
Class of N30Base is N30Child{
	held replace String is label: 'sub';
}
Class is App{ replace Function is init(Map of String to String is args){} }

#! case: testSelfInsideHeldInitializer
#! expect: ':' is not available
Class is N30Self{
	held String is label: 'seed';
	held String is fromSelf: :label;
	replace Function is init(Map of String to String is args){}
}

#! case: testSameClassHeldCycle
#! expect: of the same class; the once-guards would deadlock
Class is N30Cycle{
	held String is a: N30Cycle:b . '!';
	held String is b: 'seed';
	replace Function is init(Map of String to String is args){}
}

#! case: testHeldInstanceReceiverStrictness
#! expect: reach it through the class name, not an instance
Class is Target{
	held String is label: 'target';
}
Class is Probe{
	replace Function is init(Target is t){
		local String is s: t:label;
	}
}

#! case: testHeldFunctionsDoNotOverload
#! expect: held functions do not overload
Class is N31Fn{
	held Function of Int is twice(Int is a){ return a * 2; }
	held Function of Int is twice(Int is a, Int is b){ return a + b; }
	replace Function is init(Map of String to String is args){}
}

#! case: testHeldFunctionNoSelf
#! expect: A held member body has no instance: ':' is not available
Class is N31NoSelf{
	held Int is scale: 2;
	held Function of Int is usesSelf(){
		return :scale;
	}
	replace Function is init(Map of String to String is args){}
}

#! case: testHeldResolverSignature
#! expect: must be declared exactly 'held Function of <T> is resolveHeld(String is name, Function of <T> is missing)'
Class is N32Bad{
	held Function of Int is resolveHeld(String is name, Function of String is missing){
		return 1;
	}
	replace Function is init(Map of String to String is args){}
}

#! case: testHeldResolverSelfLoop
#! expect: The resolution hook cannot resolve through its own class prefix
Class is N32Loop{
	held Function of Int is resolveHeld(String is name, Function of Int is missing){
		return N32Loop:neverDeclared;
	}
	replace Function is init(Map of String to String is args){}
}
