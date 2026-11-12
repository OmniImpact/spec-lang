#! SpecUnit sweep (from cases_match_test.spec): Cases:match — identity
#! dispatch over class instances, array keys, else fallbacks, statement
#! forms, the today's-enum bridge, and string-literal keys.

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

Enum of String is Legacy{
	namespace: ['test'],
	A: 'a',
	B: 'b'
}

Class of SpecUnitTest is TestCasesMatch{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()]
	];

	Function is testValueMatchOverEnum(){
		local MachineState is s: MachineState:running;
		local String is label: Conditional:match(on: s, when: [
			idle:   { 'waiting' },
			MachineState:running: { 'go' },
			MachineState:failed: { 'down' }
		]);
		Assert:areEqualString('go', label);
	}

	Function is testHeldPathSubject(){
		local String is label2: Conditional:match(on: MachineState:failed, when: [
			idle:   { 'waiting' },
			running: { 'go' },
			failed: { 'down' }
		]);
		Assert:areEqualString('down', label2);
	}

	Function is testArrayKeys(){
		local String is label3: Conditional:match(on: MachineState:failed, when: [
			[idle, failed]: { 'not-going' },
			running: { 'go' }
		]);
		Assert:areEqualString('not-going', label3);
	}

	Function is testElseOverFreshInstance(){
		local MachineState is ghost: MachineState:init();
		local String is label4: Conditional:match(on: ghost, when: [
			idle: { 'waiting' },
			running: { 'go' },
			failed: { 'down' },
			else: { '?' }
		]);
		Assert:areEqualString('?', label4);
	}

	Function is testNonEnumSubject(){
		local JobKind is j: JobKind:async;
		local String is kind: Conditional:match(on: j, when: [
			JobKind:sync: { 'blocking' },
			JobKind:async: { 'queued' },
			else: { 'mixed' }
		]);
		Assert:areEqualString('queued', kind);
	}

	Function is testStatementForm(){
		local Int is hits: 0;
		match(on: JobKind:sync, when: [
			JobKind:async: { hits: hits + 1; }
		]);
		Assert:areEqualInt(0, hits);
		match(on: JobKind:sync, when: [
			JobKind:sync: { hits: hits + 1; },
			JobKind:async: { hits: hits + 10; }
		]);
		Assert:areEqualInt(1, hits);
	}

	Function is testLegacyEnumBridge(){
		local Legacy is lv: Legacy:B;
		local String is bl: Conditional:match(on: lv, when: [
			Legacy:A: { 'ay' },
			B: { 'bee' }
		]);
		Assert:areEqualString('bee', bl);
	}

	Function is testStringLiteralKeys(){
		local String is esc: Conditional:match(on: 'n', when: [
			'r': { 'carriage' },
			'n': { 'newline' },
			else: { 'plain' }
		]);
		Assert:areEqualString('newline', esc);
	}
}
