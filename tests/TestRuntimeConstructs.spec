#! SpecUnit sweep (from runtime_constructs_test.spec): the runtime paths
#! of the control-flow providers — the wrapper implementations composed
#! from the floor primitives serve the shapes the compile-time inlines
#! refuse: closures held as variables flowing to while/until/repeat, and
#! an arm table built at runtime flowing to match.
#!
#! Shared mutable state rides the instance (self): the runtime closures
#! capture frame locals by value with per-closure write-back, so a
#! counter shared between a loop's predicate and its step must live on
#! the receiver. Each test resets its field up front, so the suite is
#! order-independent.

Class of SpecUnitTest is TestRuntimeConstructs{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', Output],
		['base', 'sys', as Output()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	local Int is ticks: 0;
	local Int is tries: 0;
	local Int is hits: 0;
	local String is log: '';

	## Verifies the runtime while: closures held as variables flow to
	## the wrapper body composed from the floor while.
	Function is testRuntimeWhile(){
		self:ticks: 0;
		local Function of Boolean is keepGoing: local Function of Boolean(){ return self:ticks < 3; };
		local Function is step: local Function(){ self:ticks: self:ticks + 1; };
		Loops:while(evaluate: keepGoing, iteration: step);
		Assert:areEqualInt(3, self:ticks);
	}

	## Verifies the runtime until: one unconditional run, then the
	## negated predicate — the do-while composition.
	Function is testRuntimeUntil(){
		self:tries: 0;
		local Function of Boolean is enough: local Function of Boolean(){ return self:tries >= 2; };
		local Function is attempt: local Function(){ self:tries: self:tries + 1; };
		Loops:until(evaluate: enough, iteration: attempt);
		Assert:areEqualInt(2, self:tries);
	}

	## Verifies the runtime repeat: the counting composition over the
	## floor while (the counter rides a reference cell).
	Function is testRuntimeRepeat(){
		self:hits: 0;
		local Function is strike: local Function(){ self:hits: self:hits + 1; };
		Loops:repeat(count: 4, worker: strike);
		Assert:areEqualInt(4, self:hits);
	}

	## Verifies the runtime match: a table built with set() flows to
	## the held dispatch scan — string keys, the else fallback, and
	## first-match-wins.
	Function is testRuntimeMatch(){
		self:log: '';
		local Map of Any to Any is table: [:];
		table:set(key: 'a', value: local Function(){ self:log: self:log . 'A'; });
		table:set(key: 'b', value: local Function(){ self:log: self:log . 'B'; });
		table:set(key: 'else', value: local Function(){ self:log: self:log . '?'; });
		Conditional:match(on: 'b', when: table);
		Conditional:match(on: 'zzz', when: table);
		Assert:areEqualString('B?', self:log);
	}
}

Enum is MachineState {
	IDLE,
	RUNNING,
	FAILED
}
