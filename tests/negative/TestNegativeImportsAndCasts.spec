#! specunit: suite

Class of SpecUnitTest is TestNegativeImportsAndCasts{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', Assert]
	];

	## N4: Calling non-init members through type-imported class name is rejected.
	Function is testTypeImportNonInitMember(){
		Assert:compilerRejects(
			source: '''
Class is N4{
	replace Array of Array of String is using: [
		['base', 'math', Math]
	];
	replace Function is init(Map of String to String is args){
		Math:abs(-1);
	}
}
''',
			expect: "Members of 'Math' are callable only through an instance"
		);
	}

	## N5: Duplicate as-import bindings are rejected.
	Function is testDuplicateAsImport(){
		Assert:compilerRejects(
			source: '''
Class is N5{
	replace Array of Array of String is using: [
		['base', 'math', as Math()],
		['base', 'math', as Math()]
	];
	replace Function is init(Map of String to String is args){}
}
''',
			expect: "instance-imports 'Math' more than once"
		);
	}

	## N7: Non-literal argument in as-import is rejected.
	Function is testNonLiteralAsArgument(){
		Assert:compilerRejects(
			source: '''
Class is N7{
	local Int is seed: 3;
	replace Array of Array of String is using: [
		['base', 'math', as Math(seed)]
	];
	replace Function is init(Map of String to String is args){}
}
''',
			expect: "must be direct literal values"
		);
	}

	## N8: Cannot instance-import enums.
	Function is testCannotAsImportEnum(){
		Assert:compilerRejects(
			source: '''
Class is N8{
	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', as ExpressionKind()]
	];
	replace Function is init(Map of String to String is args){}
}
''',
			expect: "Cannot instance-import enum 'ExpressionKind'"
		);
	}

	## N27: Inner class's own as-import does not leak outward.
	Function is testInnerImportDoesNotLeak(){
		Assert:compilerRejects(
			source: '''
Class is N27{
	Class is Inner{
		replace Array of Array of String is using: [
			['base', 'math', as Math()]
		];
		replace Function is init(){}
	}
	replace Function is init(Map of String to String is args){
		floor(value: 2.7);
	}
}
''',
			expect: "Undefined function 'floor' on class 'N27'"
		);
	}

	## N28: as-form import does not grant construction.
	Function is testAsFormCannotConstruct(){
		Assert:compilerRejects(
			source: '''
Class is N28{
	replace Array of Array of String is using: [
		['base', 'math', as Math()]
	];
	replace Function is init(Map of String to String is args){
		local Math is m: Math:init();
	}
}
''',
			expect: "'Math' is not imported by 'N28'; add it to the using declaration"
		);
	}

	## as_cast: Cast between unrelated classes is rejected.
	Function is testCastBetweenUnrelatedClasses(){
		Assert:compilerRejects(
			source: '''
Class is Dog{}
Class is Cat{}
Class is App{
	replace Function is init(Map of String to String is args){
		local Cat is c: Cat:init();
		local Dog is d: c as Dog;
	}
}
''',
			expect: "Cannot cast 'Cat' to unrelated class 'Dog'"
		);
	}

	## as_chained: Chained as casts are rejected.
	Function is testChainedAsCastsRejected(){
		Assert:compilerRejects(
			source: '''
Class is App{
	replace Function is init(Map of String to String is args){
		local Float is f: 4 as Int as Float;
	}
}
''',
			expect: "Chained 'as' casts are not supported"
		);
	}
}
