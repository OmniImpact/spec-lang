#! specunit: suite
#! Tests for Structured Concurrency: ThreadScope, Task of T, Channel of T,
#! Parallel:run migration, and compile-time scope enforcement.

Class of SpecUnitTest is TestThreads{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task],
		['base', 'sys', 'thread', Channel],
		['base', 'sys', 'thread', Flow],
		['base', 'sys', as Process()],
		['base', 'sys', as Time()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],
		['base', 'struct', Array]
	];

	## 1. ThreadScope:open joins all unawaited tasks before returning, and Task:await returns typed results.
	Function is testThreadScopeLifecycleAndTypedAwait(){
		Process:atomicPut(slot: 200, value: 0);

		ThreadScope:open(body: local Function(ThreadScope is scope){
			# Spawn unawaited background task; ThreadScope:open must join it before returning
			scope:spawn(task: local Function(){
				Time:sleepMs(ms: 15);
				Process:atomicAdd(slot: 200, value: 10);
			});

			# Spawn typed String task and Int task
			local Task of String is strTask: scope:spawn(task: {
				'hello-' . 'structured'
			});
			local Task of Int is intTask: scope:spawn(task: {
				21 * 2
			});

			# Multi-waiter / repeated await() returns the same result safely
			Assert:areEqualString('hello-structured', strTask:await());
			Assert:areEqualString('hello-structured', strTask:await());
			Assert:isTrue(strTask:isDone());

			Assert:areEqualInt(42, intTask:await());
			Assert:areEqualInt(42, intTask:await());
			Assert:isTrue(intTask:isDone());
		});

		# Because ThreadScope:open joined all tasks before exiting, slot 200 is guaranteed to be 10
		Assert:areEqualInt(10, Process:atomicGet(slot: 200));
	}

	## 2. Dynamic nested task spawning, cancellation, awaitAll, and onComplete barriers.
	Function is testCancellationAndBarriers(){
		Process:atomicPut(slot: 201, value: 0);
		Process:atomicPut(slot: 202, value: 0);

		ThreadScope:open(body: local Function(ThreadScope is scope){
			Assert:isFalse(scope:isCancelled());

			local Task of Int is t1: scope:spawn(task: {
				Process:atomicAdd(slot: 201, value: 1);
				return 10;
			});
			local Task of Int is t2: scope:spawn(task: {
				# Dynamically spawn a child task onto the same scope
				scope:spawn(task: local Function(){
					Process:atomicAdd(slot: 201, value: 100);
				});
				Process:atomicAdd(slot: 201, value: 2);
				return 20;
			});

			local Array of Task is group: Array([t1, t2]);
			scope:awaitAll(group: group, then: local Function(){
				# Both t1 and t2 have finished when `then` runs
				Process:atomicPut(slot: 202, value: t1:await() + t2:await());
			});

			scope:cancel();
			Assert:isTrue(scope:isCancelled());
		});

		Assert:areEqualInt(103, Process:atomicGet(slot: 201));
		Assert:areEqualInt(30, Process:atomicGet(slot: 202));
	}

	## 3. Unbounded Channel of Int and Channel of String with multiple producers and dynamic growth.
	Function is testUnboundedChannelMultiProducer(){
		local Channel of Int is intChan: Channel:unbounded();
		local Int is sum: 0;
		local Int is count: 0;

		ThreadScope:open(body: local Function(ThreadScope is scope){
			# 4 producers each sending 25 integers (total 100 items -> grows ring buffer past 16)
			local Array of Task is producers: Array();
			local Int is p: 0;
			while({ p < 4 }, {
				local Int is pIdx: p;
				local Task is pt: scope:spawn(task: local Function(){
					local Int is k: 1;
					while({ k <= 25 }, {
						intChan:send(item: (pIdx * 100) + k);
						k: k + 1;
					});
				});
				producers:add(item: pt);
				p: p + 1;
			});

			# Close channel once all producers finish
			scope:spawn(task: local Function(){
				scope:awaitAll(group: producers);
				intChan:close();
			});

			intChan:collect(onItem: local Function(Int is v){
				sum: sum + v;
				count: count + 1;
			});
		});

		# Each producer sends sum(1..25) = 325 plus 25 * (pIdx * 100)
		# Total = 4 * 325 + 25 * (0 + 100 + 200 + 300) = 1300 + 15000 = 16300
		Assert:areEqualInt(100, count);
		Assert:areEqualInt(16300, sum);
		Assert:isTrue(intChan:isClosed());
	}

	## 4. Bounded Channel of String with backpressure (capacity = 2).
	Function is testBoundedChannelBackpressure(){
		local Channel of String is strChan: Channel:bounded(capacity: 2);
		local Array of String is received: Array();

		ThreadScope:open(body: local Function(ThreadScope is scope){
			scope:spawn(task: local Function(){
				strChan:send(item: 'msg-1');
				strChan:send(item: 'msg-2');
				strChan:send(item: 'msg-3');
				strChan:send(item: 'msg-4');
				strChan:close();
			});

			strChan:collect(onItem: local Function(String is msg){
				received:add(item: msg);
			});
		});

		Assert:areEqualInt(4, received:length());
		Assert:areEqualString('msg-1', received:get(index: 0, default: ''));
		Assert:areEqualString('msg-2', received:get(index: 1, default: ''));
		Assert:areEqualString('msg-3', received:get(index: 2, default: ''));
		Assert:areEqualString('msg-4', received:get(index: 3, default: ''));
		Assert:areEqualString('empty', strChan:receive(default: 'empty'));
	}

	## 5. Compile-time enforcement: threads cannot be spawned or scopes constructed outside ThreadScope:open.
	Function is testCompilerEnforcesThreadScope(){
		Assert:compilerRejects(
			source: '''
Class is BadDirectScopeInit{
	replace Array of Array of String is using: [
		['base', 'sys', 'thread', ThreadScope]
	];
	replace Function is init(){
		local ThreadScope is s: ThreadScope:init();
	}
}
''',
			expect: "Cannot construct 'ThreadScope' directly"
		);

		Assert:compilerRejects(
			source: '''
Class is BadRawThreadSpawn{
	replace Array of Array of String is using: [
		['base', 'sys', as Thread()]
	];
	replace Function is init(){
		Thread:threadSpawn(task: local Function(){});
	}
}
''',
			expect: "restricted to 'base:sys:thread'"
		);

		Assert:compilerRejects(
			source: '''
Class is BadDirectTaskInit{
	replace Array of Array of String is using: [
		['base', 'sys', 'thread', Task]
	];
	replace Function is init(){
		local Task is t: Task:init();
	}
}
''',
			expect: "Method 'Task:init' is internal to 'base:sys:thread'"
		);

		Assert:compilerRejects(
			source: '''
Class is BadScopeFieldEscape{
	replace Array of Array of String is using: [
		['base', 'sys', 'thread', ThreadScope]
	];
	local ThreadScope is leakedScope;
	replace Function is init(){
	}
}
''',
			expect: "Cannot store 'ThreadScope' in field"
		);

		Assert:compilerRejects(
			source: '''
Class is BadScopeReturnEscape{
	replace Array of Array of String is using: [
		['base', 'sys', 'thread', ThreadScope]
	];
	Function of ThreadScope is leak(ThreadScope is scope){
		return scope;
	}
	replace Function is init(){
	}
}
''',
			expect: "cannot return 'ThreadScope'"
		);

		Assert:compilerRejects(
			source: '''
Class is BadUnscopedParallelRun{
	replace Array of Array of String is using: [
		['base', 'sys', as Parallel()]
	];
	replace Function is init(){
		Parallel:run(threads: 2, iterations: 10, worker: local Function of Int(Int is idx, Int is cnt){ return 0; });
	}
}
''',
			expect: "Parallel:run requires 'scope' (ThreadScope)"
		);
	}

	## 6. Cold Flow of T operators: fromArray, filter, map, take, onEach, onCompletion, and buffer.
	Function is testColdFlowAndBufferOperators(){
		local Array of Int is nums: Array([1, 2, 3, 4, 5, 6, 7, 8]);
		local Int is eachSum: 0;
		local Boolean is completed: false;
		local Array of String is out: Array();

		local Flow of Int is baseFlow: Flow:fromArray(items: nums);
		local Flow of Int is evens: baseFlow:filter(predicate: local Function of Boolean(Int is n){
			return (n % 2) == 0;
		});
		local Flow of Int is firstThreeEvens: evens:take(count: 3);
		local Flow of Int is tracked: firstThreeEvens:onEach(action: local Function(Int is n){
			eachSum: eachSum + n;
		});
		local Flow of String is mapped: tracked:map(transform: local Function of String(Int is n){
			return 'item-' . (n as String);
		});
		local Flow of String is finalFlow: mapped:buffer(capacity: 2):onCompletion(action: local Function(){
			completed: true;
		});

		finalFlow:collect(onItem: local Function(String is s){
			out:add(item: s);
		});

		# Evens are 2, 4, 6 -> sum = 12, strings = ['item-2', 'item-4', 'item-6']
		Assert:isTrue(completed);
		Assert:areEqualInt(12, eachSum);
		Assert:areEqualInt(3, out:length());
		Assert:areEqualString('item-2', out:get(index: 0, default: ''));
		Assert:areEqualString('item-4', out:get(index: 1, default: ''));
		Assert:areEqualString('item-6', out:get(index: 2, default: ''));
	}

	## 7. Concurrent Flow:channelFlow and Flow:merge over ThreadScope + Channel.
	Function is testConcurrentChannelFlowAndMerge(){
		local Flow of Int is cf: Flow:channelFlow(producer: local Function(ThreadScope is scope, Channel of Int is chan){
			scope:spawn(task: local Function(){
				chan:send(item: 10);
				chan:send(item: 20);
			});
			scope:spawn(task: local Function(){
				chan:send(item: 30);
				chan:send(item: 40);
			});
		});

		local Int is cfSum: 0;
		local Int is cfCount: 0;
		cf:collect(onItem: local Function(Int is v){
			cfSum: cfSum + v;
			cfCount: cfCount + 1;
		});
		Assert:areEqualInt(4, cfCount);
		Assert:areEqualInt(100, cfSum);

		local Flow of Int is f1: Flow:fromArray(items: Array([1, 2, 3]));
		local Flow of Int is f2: Flow:fromArray(items: Array([10, 20, 30]));
		local Array of Flow is both: Array([f1, f2]);
		local Flow of Int is merged: Flow:merge(flows: both);

		local Int is mSum: 0;
		local Int is mCount: 0;
		merged:collect(onItem: local Function(Int is v){
			mSum: mSum + v;
			mCount: mCount + 1;
		});
		Assert:areEqualInt(6, mCount);
		Assert:areEqualInt(66, mSum);
	}
}
