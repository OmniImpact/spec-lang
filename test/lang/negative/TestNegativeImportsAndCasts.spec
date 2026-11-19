#! specunit: negative-suite

#! case: testTypeImportNonInitMember
#! expect: Members of 'Math' are callable only through an instance
Class is N4{
	replace Array of Array of String is using: [
		['base', 'math', Math]
	];
	replace Function is init(Map of String to String is args){
		Math:abs(-1);
	}
}

#! case: testDuplicateAsImport
#! expect: instance-imports 'Math' more than once
Class is N5{
	replace Array of Array of String is using: [
		['base', 'math', as Math()],
		['base', 'math', as Math()]
	];
	replace Function is init(Map of String to String is args){}
}

#! case: testNonLiteralAsArgument
#! expect: must be direct literal values
Class is N7{
	local Int is seed: 3;
	replace Array of Array of String is using: [
		['base', 'math', as Math(seed)]
	];
	replace Function is init(Map of String to String is args){}
}

#! case: testCannotAsImportEnum
#! expect: Cannot instance-import enum 'MemberKind'
Class is N8{
	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', as MemberKind()]
	];
	replace Function is init(Map of String to String is args){}
}

#! case: testInnerImportDoesNotLeak
#! expect: Undefined function 'floor' on class 'N27'
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

#! case: testCastBetweenUnrelatedClasses
#! expect: Cannot cast 'Cat' to unrelated class 'Dog'
Class is Dog{}
Class is Cat{}
Class is App{
	replace Function is init(Map of String to String is args){
		local Cat is c: Cat:init();
		local Dog is d: c as Dog;
	}
}

#! case: testChainedAsCastsRejected
#! expect: Chained 'as' casts are not supported
Class is App{
	replace Function is init(Map of String to String is args){
		local Float is f: 4 as Int as Float;
	}
}
