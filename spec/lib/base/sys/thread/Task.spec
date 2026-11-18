#! Package base:sys:thread
#! A concurrent task spawned within a ThreadScope.
##
## Holds the OS thread handle, completion state (`0 = PENDING`, `1 = RUNNING`,
## `2 = DONE`, `3 = FAILED`), synchronization primitives (`mutex` + `cond`) for
## non-spinning multi-waiter `await()`, the result slot `T`, and any captured
## error value.

Class is Task of T{
	namespace: ['base', 'sys', 'thread'];

	replace Array of Array of String is using: [
		['base', 'sys', as Thread()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Int is handle: 0;
	local Int is stateAddr: 0;
	local Int is mutex: 0;
	local Int is cond: 0;
	local Boolean is joined: false;
	local Boolean is arcManaged: false;
	local T is resultVal;
	local Any is errorVal: '';
	local Boolean is hasError: false;

	replace Function is init(Boolean is isArc: false){
		:arcManaged: isArc;
		:stateAddr: Mem:alloc(bytes: 8);
		Mem:storeI64(ptr: :stateAddr, byteOffset: 0, val: 0);
		:mutex: Thread:mutexCreate();
		:cond: Thread:condCreate();
		:joined: false;
		:hasError: false;
	}

	## Spawns [worker] on an OS thread and records its handle under `:mutex`.
	Function is start(Function is worker){
		Thread:mutexLock(handle: :mutex);
		:handle: Thread:threadSpawn(task: worker);
		if({ :handle == 0 }, {
			:joined: true;
		});
		Thread:mutexUnlock(handle: :mutex);
	}

	## Marks this task as running (`1`) if still pending (`0`).
	Function is markRunning(){
		Mem:atomicCasI64(addr: :stateAddr, expected: 0, desired: 1);
	}

	## Completes this task with [value] and wakes all waiting threads.
	Function is complete(T is value){
		Thread:mutexLock(handle: :mutex);
		if({ :arcManaged }, {
			local Int is addr: Mem:objToAddr(obj: value);
			if({ addr != 0 }, {
				Mem:retainAddr(objAddr: addr);
			});
		});
		:resultVal: value;
		Mem:atomicStoreI64(addr: :stateAddr, val: 2);
		Thread:condBroadcast(cond: :cond);
		Thread:mutexUnlock(handle: :mutex);
	}

	## Marks this task as failed with [err] and wakes all waiting threads.
	Function is fail(Any is err){
		Thread:mutexLock(handle: :mutex);
		local Int is addr: Mem:objToAddr(obj: err);
		if({ addr != 0 }, {
			Mem:retainAddr(objAddr: addr);
		});
		:errorVal: err;
		:hasError: true;
		Mem:atomicStoreI64(addr: :stateAddr, val: 3);
		Thread:condBroadcast(cond: :cond);
		Thread:mutexUnlock(handle: :mutex);
	}

	## True when the task has completed (either normally or with an error).
	Function of Boolean is isDone(){
		if({ :stateAddr == 0 }, { return true; });
		return Mem:atomicLoadI64(addr: :stateAddr) >= 2;
	}

	## True when the task terminated with an unhandled error.
	Function of Boolean is isFailed(){
		if({ :stateAddr == 0 }, { return false; });
		return Mem:atomicLoadI64(addr: :stateAddr) == 3;
	}

	## Returns any captured error object from the worker thread.
	Function of Any is getError(){
		return :errorVal;
	}

	## Waits for the task to finish and joins the underlying OS thread once.
	Function is joinOnly(){
		if({ :stateAddr == 0 }, { return; });
		Thread:mutexLock(handle: :mutex);
		while({ Mem:atomicLoadI64(addr: :stateAddr) < 2 }, {
			Thread:condWait(cond: :cond, mutex: :mutex);
		});
		if({ !:joined }, {
			:joined: true;
			if({ :handle != 0 }, {
				Thread:threadJoin(handle: :handle);
				:handle: 0;
			});
		});
		Thread:mutexUnlock(handle: :mutex);
	}

	## Waits for the task to finish and returns its result [T].
	Function of T is await(){
		:joinOnly();
		if({ :arcManaged }, {
			local Int is addr: Mem:objToAddr(obj: :resultVal);
			if({ addr != 0 }, {
				Mem:retainAddr(objAddr: addr);
				Mem:claimPoolAddr(objAddr: addr);
			});
		});
		return :resultVal;
	}

	Function is destroy(){
		if({ :stateAddr != 0 }, {
			if({ !:joined && :handle != 0 }, {
				Thread:threadJoin(handle: :handle);
				:handle: 0;
				:joined: true;
			});
			if({ :arcManaged }, {
				local Int is rAddr: Mem:objToAddr(obj: :resultVal);
				if({ rAddr != 0 }, {
					Mem:releaseAddr(objAddr: rAddr);
					:resultVal: Mem:addrToObj(addr: 0);
				});
			});
			if({ :hasError }, {
				local Int is eAddr: Mem:objToAddr(obj: :errorVal);
				if({ eAddr != 0 }, {
					Mem:releaseAddr(objAddr: eAddr);
					:errorVal: Mem:addrToObj(addr: 0);
				});
			});
			if({ :cond != 0 }, {
				Thread:condDestroy(handle: :cond);
				:cond: 0;
			});
			if({ :mutex != 0 }, {
				Thread:mutexDestroy(handle: :mutex);
				:mutex: 0;
			});
			Mem:free(ptr: :stateAddr);
			:stateAddr: 0;
		});
	}
}
