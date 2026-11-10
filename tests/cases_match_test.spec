#! Cases:match (PLAN-ENUM Stage 3): `when` without the keyword. Match
#! is identity dispatch over class instances: keys resolve against the
#! subject class's held members (bare and qualified spellings, array
#! keys matching several), `else` names the fallback, and arm closures
#! are inlined as statement blocks — value forms yield, statement
#! forms fall through. Exhaustiveness keys on the Enum root.

Class of Enum is MachineState{
	namespace: ['test'];

	held MachineState is idle: MachineState:init();
	held MachineState is running: MachineState:init();
	held MachineState is failed: MachineState:init();

	replace Function of String is toString(){
		return 'MachineState';
	}
}

Class is JobKind{
	namespace: ['test'];

	held JobKind is sync: JobKind:init();
	held JobKind is async: JobKind:init();
	held String is label: 'jobs';
}

Class is CasesMatchTest{
	namespace: ['test'];

	replace Function is init(Map of String to String is args){
		local Int is failures: 0;

		# Exhaustive over an Enum-rooted subject: no else needed.
		# Bare and qualified keys mix; the match yields String.
		local MachineState is s: MachineState:running;
		local String is label: Cases:match(on: s, arms: [
			idle:   { 'waiting' },
			MachineState:running: { 'go' },
			MachineState:failed: { 'down' }
		]);
		Conditional:if(check: { label == 'go' }, then: {
		}, else: {
			Output:line('[FAIL] value match over Enum-rooted subject: ' . label);
			failures: failures + 1;
		});

		# Identity: a different variant takes a different arm; the
		# subject may be a held path directly.
		local String is label2: Cases:match(on: MachineState:failed, arms: [
			idle:   { 'waiting' },
			running: { 'go' },
			failed: { 'down' }
		]);
		Conditional:if(check: { label2 == 'down' }, then: {
		}, else: {
			Output:line('[FAIL] match on a held path subject: ' . label2);
			failures: failures + 1;
		});

		# Array keys: several cases, one body — the subject is failed.
		local String is label3: Cases:match(on: MachineState:failed, arms: [
			[idle, failed]: { 'not-going' },
			running: { 'go' }
		]);
		Conditional:if(check: { label3 == 'not-going' }, then: {
		}, else: {
			Output:line('[FAIL] array-key multiple matching: ' . label3);
			failures: failures + 1;
		});

		# else arm over an Enum-rooted subject is legal: a fresh
		# instance matches no held singleton.
		local MachineState is ghost: MachineState:init();
		local String is label4: Cases:match(on: ghost, arms: [
			idle: { 'waiting' },
			running: { 'go' },
			failed: { 'down' },
			else: { '?' }
		]);
		Conditional:if(check: { label4 == '?' }, then: {
		}, else: {
			Output:line('[FAIL] else over a fresh instance: ' . label4);
			failures: failures + 1;
		});

		# Non-Enum subject, value form: else required, and present.
		local JobKind is j: JobKind:async;
		local String is kind: Cases:match(on: j, arms: [
			JobKind:sync: { 'blocking' },
			JobKind:async: { 'queued' },
			else: { 'mixed' }
		]);
		Conditional:if(check: { kind == 'queued' }, then: {
		}, else: {
			Output:line('[FAIL] non-Enum subject match: ' . kind);
			failures: failures + 1;
		});

		# Statement form: partial coverage falls through, arms mutate
		# the enclosing scope.
		local Int is hits: 0;
		match(on: JobKind:sync, arms: [
			JobKind:async: { hits: hits + 1; }
		]);
		Conditional:if(check: { hits == 0 }, then: {
		}, else: {
			Output:line('[FAIL] unmatched statement match must fall through');
			failures: failures + 1;
		});
		match(on: JobKind:sync, arms: [
			JobKind:sync: { hits: hits + 1; },
			JobKind:async: { hits: hits + 10; }
		]);
		Conditional:if(check: { hits == 1 }, then: {
		}, else: {
			Output:line('[FAIL] matched statement arm must run: ' . (hits as String));
			failures: failures + 1;
		});

		Conditional:if(check: { failures == 0 }, then: {
			Output:line('[PASS] cases match test complete');
		}, else: {
			Output:line('[FAIL] cases match test: ' . (failures as String) . ' failures');
		});
	}

	replace Array of Array of String is using: [
		['base', 'io', as Output()],
		['base', 'sys', as Conditional()],
		['base', 'cases', as Cases()]
	];
}
