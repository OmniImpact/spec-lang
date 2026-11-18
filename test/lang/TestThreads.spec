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

			local Array of Task is group: [t1, t2];
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
			local Array of Task is producers: [];
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
		local Array of String is received: [];

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
	}
}
