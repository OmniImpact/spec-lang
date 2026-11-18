Class of SpecUnitTest is TestNegativeClassModel{
	replace Array of Array of String is using: [
		['specunit', Assert],
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner]
	];

	Function is testEntryBadInit(){
		Assert:compilerRejects(
			source: '''
Class is EntryBadInit{
	Function is init(String is name){
	}
}
''',
			expect: "requires an init"
		);
	}

	Function is testEntryEnumOnly(){
		Assert:compilerRejects(
			source: '''
Enum of Int is ModeOnly{
	ON: 1,
	OFF: 0
}
''',
			expect: "No entry class found in"
		);
	}

	Function is testDiamondConflict(){
		Assert:compilerRejects(
			source: '''
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
''',
			expect: "inherits conflicting implementations of 'value' from 'DiamondA' and 'DiamondB'"
		);
	}

	Function is testVisibilityLocalMember(){
		Assert:compilerRejects(
			source: '''
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
''',
			expect: "Member 'secret' is local to class 'VisBase'"
		);
	}

	Function is testVisibilityContainedMember(){
		Assert:compilerRejects(
			source: '''
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
''',
			expect: "Member 'helper' is contained in class 'VisBase'"
		);
	}

	Function is testVisibilityReplaceLocal(){
		Assert:compilerRejects(
			source: '''
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
''',
			expect: "Member 'secret' is local in ancestor 'VisBase' and cannot be replaced or merged"
		);
	}

	Function is testVisibilityShadowLocal(){
		Assert:compilerRejects(
			source: '''
Class is ShadowedLocal{
	local Int is counter: 0;
}

Class of ShadowedLocal is ShadowChild{
	local Int is counter: 1;
}
''',
			expect: "Member 'counter' is local in ancestor 'ShadowedLocal' and cannot be replaced or merged"
		);
	}

	Function is testVisibilityContradictoryModifiers(){
		Assert:compilerRejects(
			source: '''
Class is ContradictoryModifiers{
	replace local Function of Int is broken(){
		return 1;
	}
}
''',
			expect: "combines 'replace'/'merge' with a visibility modifier"
		);
	}

	Function is testGroupRetired(){
		Assert:compilerRejects(
			source: '''
Class is N21GroupFragment{
	Array of String is group: [N21GroupTarget];
}

Class is N21GroupCaller{
	replace Function is init(Map of String to String is args){
		local N21GroupTarget is t: N21GroupTarget:init();
	}
}
''',
			expect: "Undefined identifier 'N21GroupTarget'"
		);
	}

	Function is testUnconstructibleSpecUnit(){
		Assert:compilerRejects(
			source: '''
Class of SpecUnitTest is TestUnconstructible{
	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner]
	];

	replace Function is init(Int is seed){
	}
}
''',
			expect: "does not implement abstract member 'init' required by parent 'SpecUnitTest'"
		);
	}
}
