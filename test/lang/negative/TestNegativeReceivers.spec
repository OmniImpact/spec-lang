#! specunit: negative-suite

#! case: testOwnNameReceiverInsideClass
#! expect: through the class name inside 'N1SelfRead' itself; use :
Class is N1SelfRead{
	local Int is count: 5;
	Function of Int is bump(){ return :count + 1; }
	replace Function is init(Map of String to String is args){
		local Int is v: N1SelfRead:bump();
	}
}

#! case: testUndefinedBareCall
#! expect: Undefined function 'nope' on class 'N2UndefinedBare'
Class is N2UndefinedBare{
	replace Function is init(Map of String to String is args){
		nope();
	}
}

#! case: testAmbiguousBareCollision
#! expect: provided by the enclosing class and Math; qualify the call
Class is N3Collision{
	replace Array of Array of String is using: [
		['base', 'math', as Math()]
	];
	Function of Int is round(){ return 1; }
	replace Function is init(Map of String to String is args){
		round();
	}
}

#! case: testInitOnInstanceReceiver
#! expect: 'init' is construct-only
Class is N10InitOnInstance{
	replace Function is init(Map of String to String is args){
		local N10InitOnInstance is again: N10InitOnInstance:init();
		again:init();
	}
}

#! case: testFieldThroughClassPrefix
#! expect: Fields are not reachable through the class-name prefix
Class is Target{
	Int is n: 5;
}
Class is N11PrefixField{
	replace Function is init(Map of String to String is args){
		local Int is x: Target:n;
	}
}

#! case: testColonReceiverExcludesMergedScope
#! expect: Undefined function 'round' on class 'N12NoMergedOnColon'
Class is N12NoMergedOnColon{
	replace Array of Array of String is using: [
		['base', 'math', as Math()]
	];
	replace Function is init(Map of String to String is args){
		local Int is x: :round(value: 1.5);
	}
}

#! case: testMagicSelfRemoved
#! expect: Undefined identifier 'self'
Class is N13NoMagicSelf{
	replace Function is init(Map of String to String is args){
		local N13NoMagicSelf is x: self;
	}
}
