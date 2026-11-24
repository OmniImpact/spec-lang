#! specunit: negative-suite

#! case: testScopedRegionNoOpenSlot
#! expect: has no open scope slot
Class is App{
	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		as: if(check: true, then: {});
	}
}

#! case: testValueBranchMismatch
#! expect: Branch yields mismatched types: 'String' and 'Int'
Class is App{
	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		local String is x: if({ 1 > 0 }, { 'text' }, { 42 });
	}
}

#! case: testCasesMatchForeignClassKey
#! expect: is not a held member of 'Sink'
Class of Enum is Mode{
	held Mode is on: Mode:init();
	held Mode is off: Mode:init();
}
Class is Sink{
	held String is file: 'log.txt';
}
Class is App{
	replace [[String]] is using: [
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

#! case: testCasesMatchNonExhaustive
#! expect: Non-exhaustive match: missing arm(s) Mode:off
Class of Enum is Mode{
	held Mode is on: Mode:init();
	held Mode is off: Mode:init();
}
Class is App{
	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		local String is partial: match(on: Mode:on, when: [
			Mode:on: { 'on' }
		]);
	}
}

#! case: testVoidEnumMatchNonExhaustive
#! expect: Non-exhaustive match: missing arm(s) Mode:off
Class of Enum is Mode{
	held Mode is on: Mode:init();
	held Mode is off: Mode:init();
}
Class is App{
	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		match(on: Mode:on, when: [
			Mode:on: {}
		]);
	}
}

#! case: testRedundantElseOnEnumMatch
#! expect: Redundant else arm in exhaustive match on 'Mode'
Class of Enum is Mode{
	held Mode is on: Mode:init();
	held Mode is off: Mode:init();
}
Class is App{
	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		local String is s: match(on: Mode:on, when: [
			Mode:on: { 'on' },
			Mode:off: { 'off' },
			else: { '?' }
		]);
	}
}

#! case: testTaggedPayloadArityMismatch
#! expect: binds 2 parameter(s), but the variant declares 1
Enum is Shape{
	Circle(Int is r),
	Point
}
Class is App{
	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		local Shape is sh: Shape:Circle(r: 5);
		local Int is x: match(on: sh, when: [
			Shape:Circle: local Function of Int(Int is r, Int is extra){ return r; },
			Shape:Point: { 0 }
		]);
	}
}

#! case: testTaggedPayloadTypeMismatch
#! expect: has type 'String', expected 'Int'
Enum is Shape{
	Circle(Int is r),
	Point
}
Class is App{
	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		local Shape is sh: Shape:Circle(r: 5);
		local Int is x: match(on: sh, when: [
			Shape:Circle: local Function of Int(String is r){ return 1; },
			Shape:Point: { 0 }
		]);
	}
}

#! case: testLoopVarsRequireLiterals
#! expect: requires inline literal closures
Class is App{
	replace [[String]] is using: [
		['base', 'sys', as Loops()]
	];
	replace Function is init(Map of String to String is args){
		local Function of Boolean is cond: local Function of Boolean(){ return true; };
		local Function is body: local Function(){};
		while([Int is i: 0], cond, body);
	}
}

#! case: testPredicateTableMustBeLiteral
#! expect: predicate match table is compile-time
Class is App{
	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		local Map of Any to Any is table: [:];
		match(when: table);
	}
}

#! case: testPredicateArmsTakeNoParameters
#! expect: Predicate match arms take no parameters
Class is App{
	replace [[String]] is using: [
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

#! case: testTaggedPayloadNonExhaustive
#! expect: Non-exhaustive match: missing arm(s) Shape:Dot
Enum is Shape{
	Circle(Int is r),
	Rect(Int is w, Int is h),
	Dot
}
Class is App{
	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		local Shape is sh: Shape:Dot;
		local String is r: match(on: sh, when: [
			Shape:Circle: local Function(Int is r){ return 'circle'; },
			Shape:Rect:  local Function(Int is w, Int is h){ return 'rect'; }
		]);
	}
}

#! case: testValuePredicateMatchRequiresElse
#! expect: A value-yielding predicate match requires an else arm
Class is App{
	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
	];
	replace Function is init(Map of String to String is args){
		local Int is score: 50;
		local String is r: match(when: [
			{ score >= 90 }: { 'excellent' },
			{ score >= 70 }: { 'good' }
		]);
	}
}
