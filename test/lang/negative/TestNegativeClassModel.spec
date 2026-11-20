#! specunit: negative-suite

#! case: testEntryBadInit
#! expect: requires an init
Class is EntryBadInit{
	replace Function is init(String is name){
	}
}

#! case: testEntryEnumOnly
#! expect: No entry class found in
Enum of Int is ModeOnly{
	ON: 1,
	OFF: 0
}

#! case: testDiamondConflict
#! expect: inherits conflicting implementations of 'value' from 'DiamondA' and 'DiamondB'
Class is DiamondA{
	Function of Int is value(){
		return 1;
	}
}

Class is DiamondB{
	Function of Int is value(){
		return 2;
	}
}

Class of DiamondA, DiamondB is DiamondBadChild{
	replace Function is init(Map of String to String is args){
	}
}

#! case: testVisibilityLocalMember
#! expect: Member 'secret' is local to class 'VisBase'
Class is VisBase{
	local Function of Int is secret(){
		return 1;
	}
}

Class is VisBreaker{
	replace Function is init(Map of String to String is args){
		local VisBase is b: VisBase:init();
		b:secret();
	}
}

#! case: testVisibilityContainedMember
#! expect: Member 'helper' is contained in class 'VisBase'
Class is VisBase{
	contained Function of Int is helper(){
		return 2;
	}
}

Class is VisUnrelated{
	replace Function is init(Map of String to String is args){
		local VisBase is b: VisBase:init();
		b:helper();
	}
}

#! case: testVisibilityReplaceLocal
#! expect: Member 'secret' is local in ancestor 'VisBase' and cannot be replaced or merged
Class is VisBase{
	local Function of Int is secret(){
		return 1;
	}
}

Class of VisBase is VisOverrideAttempt{
	replace Function of Int is secret(){
		return 9;
	}
}

#! case: testVisibilityShadowLocal
#! expect: Member 'counter' is local in ancestor 'ShadowedLocal' and cannot be replaced or merged
Class is ShadowedLocal{
	local Int is counter: 0;
}

Class of ShadowedLocal is ShadowChild{
	local Int is counter: 1;
}

#! case: testVisibilityContradictoryModifiers
#! expect: combines 'replace'/'merge' with a visibility modifier
Class is ContradictoryModifiers{
	replace local Function of Int is broken(){
		return 1;
	}
}

#! case: testGroupRetired
#! expect: Undefined identifier 'N21GroupTarget'
Class is N21GroupFragment{
	Array of String is group: [N21GroupTarget];
}

Class is N21GroupCaller{
	replace Function is init(Map of String to String is args){
		local N21GroupTarget is t: N21GroupTarget:init();
	}
}

#! case: testUnconstructibleSpecUnit
#! expect: does not implement abstract member 'init' required by parent 'SpecUnitTest'
Class of SpecUnitTest is TestUnconstructible{
	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner]
	];

	replace Function is init(Int is seed){
	}
}
