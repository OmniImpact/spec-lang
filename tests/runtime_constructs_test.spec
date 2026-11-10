#! The runtime paths of the control-flow providers: the wrapper
#! implementations composed from the floor primitives serve the shapes
#! the compile-time inlines refuse — closures held as variables and
#! arm tables built at runtime.
#!
#! Shared mutable state rides the instance (self): the runtime
#! closures capture frame locals by value with per-closure write-back,
#! so a counter shared between a loop's predicate and its step must
#! live on the receiver (or a reference cell inside the composition).

Enum is MachineState {
	IDLE,
	RUNNING,
	FAILED
}

Class is RuntimeConstructsTest{
	namespace: ['test'];

	replace Array of Array of String is using: [
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
	local Function is testRuntimeWhile(){
		local Function of Boolean is keepGoing: local Function of Boolean(){ return self:ticks < 3; };
		local Function is step: local Function(){ self:ticks: self:ticks + 1; };
		Loops:while(evaluate: keepGoing, iteration: step);
		Conditional:if(check: { self:ticks == 3 }, then: {
			Output:line('[PASS] runtime while (variable closures)');
		}, else: {
			Output:line('[FAIL] runtime while: ticks=' . (self:ticks as String));
		});
	}

	## Verifies the runtime until: one unconditional run, then the
	## negated predicate — the do-while composition.
	local Function is testRuntimeUntil(){
		local Function of Boolean is enough: local Function of Boolean(){ return self:tries >= 2; };
		local Function is attempt: local Function(){ self:tries: self:tries + 1; };
		Loops:until(evaluate: enough, iteration: attempt);
		Conditional:if(check: { self:tries == 2 }, then: {
			Output:line('[PASS] runtime until (the body ran once, then twice)');
		}, else: {
			Output:line('[FAIL] runtime until: tries=' . (self:tries as String));
		});
	}

	## Verifies the runtime repeat: the counting composition over the
	## floor while (the counter rides a reference cell).
	local Function is testRuntimeRepeat(){
		local Function is strike: local Function(){ self:hits: self:hits + 1; };
		Loops:repeat(count: 4, worker: strike);
		Conditional:if(check: { self:hits == 4 }, then: {
			Output:line('[PASS] runtime repeat (variable worker)');
		}, else: {
			Output:line('[FAIL] runtime repeat: hits=' . (self:hits as String));
		});
	}

	## Verifies the runtime match: a table built with set() flows to
	## the held dispatch scan — string keys, the else fallback, and
	## first-match-wins.
	local Function is testRuntimeMatch(){
		local Map of Any to Any is table: [:];
		table:set(key: 'a', value: local Function(){ self:log: self:log . 'A'; });
		table:set(key: 'b', value: local Function(){ self:log: self:log . 'B'; });
		table:set(key: 'else', value: local Function(){ self:log: self:log . '?'; });
		Conditional:match(on: 'b', when: table);
		Conditional:match(on: 'zzz', when: table);
		Conditional:if(check: { self:log == 'B?' }, then: {
			Output:line('[PASS] runtime match (string keys, else fallback)');
		}, else: {
			Output:line('[FAIL] runtime match: log=' . self:log);
		});
	}

	## Entry point.
	##
	## @param args: Unused CLI arguments map.
	replace Function is init(Map of String to String is args){
		Output:line('=== Runtime Constructs Test ===');
		self:testRuntimeWhile();
		self:testRuntimeUntil();
		self:testRuntimeRepeat();
		self:testRuntimeMatch();
		Output:line('=== done ===');
	}
}
