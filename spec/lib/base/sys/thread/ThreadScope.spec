#! Package base:sys:thread
#! Structured concurrency scope: manages task lifetimes, cancellation, and barriers.
##
## Every concurrent task in Spec must be spawned inside a `ThreadScope:open`
## block. `ThreadScope:open` guarantees that all tasks spawned within the scope
## are joined before `open` returns. Constructing `ThreadScope` directly outside
## `ThreadScope` is rejected at compile time.

Class is ThreadScope{
	namespace: ['base', 'sys', 'thread'];

	replace Array of Array of String is using: [
		['base', 'sys', 'thread', Task],
		['base', 'sys', as Thread()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array]
	];

	local Array of Task is tasks: [];
	local Int is mutex: 0;
	local Int is cancelledAddr: 0;
	local Any is errorHandler: '';
	local Boolean is hasErrorHandler: false;

	local Function of Boolean is hasClosure(Function is cb){
		local Int is addr: Mem:objToAddr(obj: cb);
		if({ addr == 0 }, { return false; });
		return Mem:loadI64(ptr: addr, byteOffset: 0) != 0;
	}

	local Function is invokeErrorHandler(Function is cb, Any is err){
		cb(err);
	}

	replace Function is init(Function is onError: local Function(Any is _err){}){
		:tasks: [];
		:mutex: Thread:mutexCreate();
		:cancelledAddr: Mem:alloc(bytes: 8);
		Mem:storeI64(ptr: :cancelledAddr, byteOffset: 0, val: 0);
		:errorHandler: Mem:addrToObj(addr: Mem:objToAddr(obj: onError));
		:hasErrorHandler: :hasClosure(cb: onError);
	}

	## Opens a structured concurrency scope, executes [body] with the scope,
	## and joins all spawned tasks before returning.
	Function is open(Function is body, Function is onError: local Function(Any is _err){}){
		local ThreadScope is scope: ThreadScope:init(onError: onError);
		if({ :hasClosure(cb: body) }, {
			body(scope);
		});
		scope:joinAll();
	}

	## Spawns [task] on a new thread bound to this scope and returns a [Task].
	## [kind] is supplied by the compiler (`0` = Int/Bool/Byte, `1` = ARC ptr, `2` = Float, `3` = Void).
	Function of Task is spawn(Function is task, Int is kind: 0){
		local Task is t: Task:init(isArc: kind == 1);
		Thread:mutexLock(handle: :mutex);
		:tasks:add(item: t);
		Thread:mutexUnlock(handle: :mutex);

		local Function is worker: local Function(){
			t:markRunning();
			if({ kind == 3 }, {
				task();
				t:complete(value: Mem:addrToObj(addr: 0));
			}, {
				local Any is res: task();
				t:complete(value: res);
			});
		};
		t:start(worker: worker);
		return t;
	}

	## Marks this scope as cooperatively cancelled.
	Function is cancel(){
		if({ :cancelledAddr != 0 }, {
			Mem:atomicStoreI64(addr: :cancelledAddr, val: 1);
		});
	}

	## True when this scope has been cancelled.
	Function of Boolean is isCancelled(){
		if({ :cancelledAddr == 0 }, { return false; });
		return Mem:atomicLoadI64(addr: :cancelledAddr) != 0;
	}

	## Waits for all tasks in [group] to complete, then invokes [then] if provided.
	Function is awaitAll(Array of Task is group, Function is then: local Function(){}){
		local Int is i: 0;
		while({ i < group:length() }, {
			local Task is t: group:get(index: i);
			t:joinOnly();
			i: i + 1;
		});
		if({ :hasClosure(cb: then) }, {
			then();
		});
	}

	## Joins all tasks currently in the scope and invokes [then].
	Function is onComplete(Function is then){
		:joinAll();
		if({ :hasClosure(cb: then) }, {
			then();
		});
	}

	## Joins all tasks spawned in this scope (including tasks spawned dynamically by children).
	Function is joinAll(){
		if({ :mutex == 0 }, { return; });
		local Int is idx: 0;
		local Boolean is more: true;
		while({ more }, {
			Thread:mutexLock(handle: :mutex);
			local Int is total: :tasks:length();
			local Boolean is hasNext: idx < total;
			local Task is nextTask: if({ hasNext }, { :tasks:get(index: idx) }, { Mem:addrToObj(addr: 0) as Task });
			Thread:mutexUnlock(handle: :mutex);
			if({ hasNext }, {
				if({ Mem:objToAddr(obj: nextTask) != 0 }, {
					nextTask:joinOnly();
					if({ nextTask:isFailed() }, {
						:cancel();
						if({ :hasErrorHandler }, {
							:invokeErrorHandler(cb: :errorHandler, err: nextTask:getError());
						});
					});
				});
				idx: idx + 1;
			}, {
				more: false;
			});
		});
	}

	Function is destroy(){
		:joinAll();
		if({ :mutex != 0 }, {
			Thread:mutexDestroy(handle: :mutex);
			:mutex: 0;
		});
		if({ :cancelledAddr != 0 }, {
			Mem:free(ptr: :cancelledAddr);
			:cancelledAddr: 0;
		});
	}
}
