#! specunit: suite

Class of SpecUnitTest is TestNegativeControlFlow{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', Assert]
	];

	## N19: Scoped region without open slot is rejected.
	Function is testScopedRegionNoOpenSlot(){
		Assert:compilerRejects(
			source: '''
Class is App{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		as: if(check: true, then: {});
	}
}
''',
			expect: "has no open scope slot"
		);
	}

	## N20: Value branch yield types must unify.
	Function is testValueBranchMismatch(){
		Assert:compilerRejects(
			source: '''
Class is App{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		local String is x: if({ 1 > 0 }, { 'text' }, { 42 });
	}
}
''',
			expect: "Branch yields mismatched types: 'String' and 'Int'"
		);
	}

	## N33: Keys in Cases:match must resolve to held members of the subject's class.
	Function is testCasesMatchForeignClassKey(){
		Assert:compilerRejects(
			source: '''
Class of Enum is Mode{
	held Mode is on: Mode:init();
	held Mode is off: Mode:init();
}
Class is Sink{
	held String is file: 'log.txt';
}
Class is App{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		local Sink is s: Sink:file;
		local String is wrong: match(on: s, when: [
			Mode:on: { 'x' },
			else: { 'y' }
		]);
	}
}
''',
			expect: "is not a held member of 'Sink'"
		);
	}

	## N33: Enum-rooted matches must be exhaustive.
	Function is testCasesMatchNonExhaustive(){
		Assert:compilerRejects(
			source: '''
Class of Enum is Mode{
	held Mode is on: Mode:init();
	held Mode is off: Mode:init();
}
Class is App{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		local String is partial: match(on: Mode:on, when: [
			Mode:on: { 'on' }
		]);
	}
}
''',
			expect: "Non-exhaustive match: missing arm(s) Mode:off"
		);
	}

	## N34: Loop vars require inline literal closures.
	Function is testLoopVarsRequireLiterals(){
		Assert:compilerRejects(
			source: '''
Class is App{
	replace Array of Array of String is using: [
		['base', 'sys', as Loops()]
	];
	replace Function is init(Map of String to String is args){
		local Function of Boolean is cond: local Function of Boolean(){ return true; };
		local Function is body: local Function(){};
		while([Int is i: 0], cond, body);
	}
}
''',
			expect: "requires inline literal closures"
		);
	}

	## N35: Predicate match table must be a compile-time literal.
	Function is testPredicateTableMustBeLiteral(){
		Assert:compilerRejects(
			source: '''
Class is App{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		local Map of Any to Any is table: [:];
		match(when: table);
	}
}
''',
			expect: "predicate match table is compile-time"
		);
	}

	## N36: Predicate match arms take no parameters.
	Function is testPredicateArmsTakeNoParameters(){
		Assert:compilerRejects(
			source: '''
Class is App{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		local Int is n: 5;
		match(when: [
			{ n > 1 }: local Function(Int is x){},
			else: {}
		]);
	}
}
''',
			expect: "Predicate match arms take no parameters"
		);
	}
}
