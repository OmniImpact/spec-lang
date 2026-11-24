#! specunit: suite
#! Tests for compiler-lowered `lazy({ ... })` on local variables, instance fields,
#! assign-before-read, assign-after-read, concurrent access, and read-only external state.

Class of SpecUnitTest is TestLazy{

	replace [[String]] is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'core', SpecError],
		['base', 'sys', as Lazy()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Parallel()],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'struct', Array]
	];

	## 1. Unread local lazy binding never executes its initializer.
	Function is testUnreadLocalLazyNeverRuns(){
		local LazyCounter is c: LazyCounter:init();
		local Int is unused: lazy({
			return c:bump(delta: 99);
		});
		Assert:areEqualInt(0, c:calls);
	}

	## 2. Local lazy binding runs once on first read, caches result, and allows mutating inner locals.
	Function is testLocalLazyRunsOnceAndCaches(){
		local LazyCounter is c: LazyCounter:init();
		local Int is base: 5;
		local String is msg: lazy({
			local Int is step: c:bump(delta: base);
			step: step + 10;
			return 'val=' . (step as String);
		});
		Assert:areEqualInt(0, c:calls);
		Assert:areEqualString('val=15', msg);
		Assert:areEqualInt(1, c:calls);
		Assert:areEqualString('val=15', msg);
		Assert:areEqualInt(1, c:calls);
	}

	## 3. Assigning to a local lazy variable before reading it skips the lazy initializer.
	Function is testLocalLazyAssignBeforeReadSkipsInit(){
		local LazyCounter is c: LazyCounter:init();
		local Int is val: lazy({
			return c:bump(delta: 500);
		});
		Assert:areEqualInt(0, c:calls);
		val: 42;
		Assert:areEqualInt(42, val);
		Assert:areEqualInt(0, c:calls);
	}

	## 4. Assigning to a local lazy variable after reading overwrites the cached value.
	Function is testLocalLazyAssignAfterReadOverwrites(){
		local LazyCounter is c: LazyCounter:init();
		local String is s: lazy({
			local Int is n: c:bump(delta: 7);
			return 'init-' . (n as String);
		});
		Assert:areEqualString('init-7', s);
		Assert:areEqualInt(1, c:calls);
		s: 'updated';
		Assert:areEqualString('updated', s);
		Assert:areEqualInt(1, c:calls);
	}

	## 5. Instance lazy fields do not run during init, evaluate once on first read, and cache across reads.
	Function is testInstanceFieldLazyEvaluation(){
		local LazySample is sample: LazySample:init(seed: 20);
		Assert:areEqualInt(0, sample:counter:calls);

		Assert:areEqualInt(30, sample:readIntViaColon());
		Assert:areEqualInt(1, sample:counter:calls);
		Assert:areEqualInt(30, sample:readIntBare());
		Assert:areEqualInt(30, sample:computedInt);
		Assert:areEqualInt(1, sample:counter:calls);

		Assert:areEqualString('label-1-20', sample:computedLabel);
		Assert:areEqualInt(2, sample:counter:calls);
		Assert:areEqualString('label-1-20', sample:computedLabel);
		Assert:areEqualInt(2, sample:counter:calls);

		Assert:areEqualInt(3, sample:computedArray:length());
		Assert:areEqualInt(100, sample:computedArray:get(index: 0, default: 0));
		Assert:areEqualInt(102, sample:computedArray:get(index: 2, default: 0));
		Assert:areEqualInt(3, sample:counter:calls);
	}

	## 6. Assigning to a lazy instance field before reading skips its initializer; assigning after updates it.
	Function is testInstanceFieldLazyAssignBeforeAndAfterRead(){
		local LazySample is s1: LazySample:init(seed: 10);
		s1:overwriteInt(v: 999);
		Assert:areEqualInt(0, s1:counter:calls);
		Assert:areEqualInt(999, s1:computedInt);
		Assert:areEqualInt(0, s1:counter:calls);

		local LazySample is s2: LazySample:init(seed: 10);
		Assert:areEqualInt(20, s2:computedInt);
		Assert:areEqualInt(1, s2:counter:calls);
		s2:computedInt: 777;
		Assert:areEqualInt(777, s2:computedInt);
		Assert:areEqualInt(1, s2:counter:calls);
	}

	## 7. Concurrent reads of a lazy instance field across threads initialize once and return consistent values.
	Function is testConcurrentLazyFieldInit(){
		local LazySample is shared: LazySample:init(seed: 50);
		local Array of Int is results: Array([0, 0, 0, 0]);
		local Int is sum: 0;
		ThreadScope:open(body: local Function(ThreadScope is scope){
			sum: Parallel:run(
				scope: scope,
				threads: 4,
				iterations: 4,
				worker: local Function of Int(Int is threadIdx, Int is _count){
					local Int is v: shared:computedInt;
					results:set(index: threadIdx, item: v);
					return v;
				}
			);
		});
		Assert:areEqualInt(1, shared:counter:calls);
		Assert:areEqualInt(240, sum);
		while([Int is i: 0], { i < 4 }, {
			Assert:areEqualInt(60, results:get(index: i, default: 0));
			i++;
		});
	}

	## 8. Mutating an outer local variable or instance field inside `lazy({ ... })` is rejected by the compiler.
	Function is testLazyRejectsExternalMutation(){
		Assert:compilerRejects(
			source: '''
Class is BadLazyLocal{
	replace [[String]] is using: [
		['base', 'sys', as Lazy()]
	];
	replace Function is init(){
		local Int is outer: 1;
		local Int is x: lazy({
			outer: 2;
			return outer;
		});
	}
}
''',
			expect: "Cannot modify external state inside a 'lazy' initializer"
		);

		Assert:compilerRejects(
			source: '''
Class is BadLazyInc{
	replace [[String]] is using: [
		['base', 'sys', as Lazy()]
	];
	replace Function is init(){
		local Int is outer: 1;
		local Int is x: lazy({
			outer++;
			return outer;
		});
	}
}
''',
			expect: "Cannot modify external state inside a 'lazy' initializer"
		);

		Assert:compilerRejects(
			source: '''
Class is BadLazyField{
	replace [[String]] is using: [
		['base', 'sys', as Lazy()]
	];
	Int is count: 0;
	Int is val: lazy({
		:count: 1;
		return :count;
	});
	replace Function is init(){
	}
}
''',
			expect: "Cannot modify external state inside a 'lazy' initializer"
		);
	}
}

Class is LazyCounter{
	Int is calls: 0;

	replace Function is init(){
	}

	Function of Int is bump(Int is delta){
		:calls: :calls + 1;
		return delta;
	}
}

Class is LazySample{
	replace [[String]] is using: [
		['base', 'sys', as Lazy()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array]
	];

	LazyCounter is counter: LazyCounter:init();
	Int is seed: 10;

	Int is computedInt: lazy({
		local Int is acc: :counter:bump(delta: :seed);
		while([Int is i: 1], { i <= 4 }, {
			acc: acc + i;
			i++;
		});
		return acc;
	});

	String is computedLabel: lazy({
		local Int is c: :counter:bump(delta: 1);
		return 'label-' . (c as String) . '-' . (:seed as String);
	});

	Array of Int is computedArray: lazy({
		local Int is b: :counter:bump(delta: 100);
		return Array([b, b + 1, b + 2]);
	});

	replace Function is init(:seed){
		:counter: LazyCounter:init();
	}

	Function of Int is readIntViaColon(){
		return :computedInt;
	}

	Function of Int is readIntBare(){
		return computedInt;
	}

	Function is overwriteInt(Int is v){
		:computedInt: v;
	}

## A lazy initializer that unwinds resets the once-state, so the next
	## read retries the initializer instead of spinning forever on the
	## in-progress state.
	Function is testFailedInitRetriesOnNextRead(){
		local FailingLazy is f: FailingLazy:init();
		local Int is first: try(
			body: local Function of Int(){ return f:prized; },
			guard: local Function of Int(SpecError is e){ return 0 - 1; }
		);
		Assert:areEqualInt(0 - 1, first);
		local Int is second: try(
			body: local Function of Int(){ return f:prized; },
			guard: local Function of Int(SpecError is e){ return 0 - 2; }
		);
		Assert:areEqualInt(0 - 2, second);
	}
}

Enum is LazyProbeKind{
	INIT_FAILED
}

Class is FailingLazy{
	Int is prized: lazy({ 
		:raiseError(error: SpecError:init(kind: LazyProbeKind:INIT_FAILED, description: 'init boom'));
		return 0;
	});

	replace [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'sys', as Lazy()],
		['base', 'struct', Map]
	];
}
