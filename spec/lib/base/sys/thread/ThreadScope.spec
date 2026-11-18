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
		['base', 'core', SpecError],
		['base', 'sys', 'thread', Task],
		['base', 'sys', as Reflection()],
		['base', 'sys', as Thread()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array]
	];

	local Array of Task is tasks: [];
	local Int is mutex: 0;
	local Int is cancelledAddr: 0;
	local Int is errorHandlerAddr: 0;
	local Boolean is hasErrorHandler: false;

	local Function of Boolean is hasClosure(Function is cb){
		local Int is addr: Mem:objToAddr(obj: cb);
		if({ addr == 0 }, { return false; });
		return Mem:loadI64(ptr: addr, byteOffset: 0) != 0;
	}

	local Function of Boolean is invokeErrorHandler(Function is cb, Any is err){
		return cb(err);
	}

	local Function of Int is mergeUnhandledError(Int is primaryAddr, Int is nextAddr){
		if({ nextAddr == 0 }, { return primaryAddr; });
		if({ primaryAddr == 0 }, { return nextAddr; });
		if({ primaryAddr != nextAddr }, {
			local SpecError is primaryErr: Mem:addrToObj(addr: primaryAddr) as SpecError;
			local SpecError is nextErr: Mem:addrToObj(addr: nextAddr) as SpecError;
			primaryErr:addSecondary(error: nextErr);
		});
		Mem:releaseAddr(objAddr: nextAddr);
		return primaryAddr;
	}

	local Function of Int is handleSingleErrorAddr(Int is errAddr){
		if({ errAddr == 0 }, { return 0; });
		if({ !:hasErrorHandler || :errorHandlerAddr == 0 }, {
			Mem:retainAddr(objAddr: errAddr);
			return errAddr;
		});
		local Boolean is handled: false;
		local Int is raisedAddr: Mem:callCatching(action: local Function(){
			handled: :invokeErrorHandler(cb: Mem:addrToObj(addr: :errorHandlerAddr), err: Mem:addrToObj(addr: errAddr));
		});
		if({ raisedAddr != 0 }, {
			return raisedAddr;
		});
		if({ handled }, {
			return 0;
		});
		Mem:retainAddr(objAddr: errAddr);
		return errAddr;
	}

	local Function of Int is handleErrorAddr(Int is errAddr){
		if({ errAddr == 0 }, { return 0; });
		local SpecError is errObj: Mem:addrToObj(addr: errAddr) as SpecError;
		local Array of SpecError is secs: errObj:getSecondaryErrors();
		if({ secs:length() == 0 }, {
			return :handleSingleErrorAddr(errAddr: errAddr);
		});
		local Array of SpecError is savedSecs: [];
		local Int is i: 0;
		while({ i < secs:length() }, {
			savedSecs:add(item: secs:get(index: i));
			i: i + 1;
		});
		secs:clear();
		local Int is mergedAddr: :handleSingleErrorAddr(errAddr: errAddr);
		i: 0;
		while({ i < savedSecs:length() }, {
			local SpecError is sErr: savedSecs:get(index: i);
			local Int is uSecAddr: :handleSingleErrorAddr(errAddr: Mem:objToAddr(obj: sErr));
			mergedAddr: :mergeUnhandledError(primaryAddr: mergedAddr, nextAddr: uSecAddr);
			i: i + 1;
		});
		return mergedAddr;
	}

	replace Function is init(Function is onError: local Function of Boolean(SpecError is _err){ return false; }){
		:tasks: [];
		:mutex: Thread:mutexCreate();
		:cancelledAddr: Mem:alloc(bytes: 8);
		Mem:storeI64(ptr: :cancelledAddr, byteOffset: 0, val: 0);
		local Int is ehAddr: Mem:objToAddr(obj: onError);
		if({ ehAddr != 0 }, {
			Mem:retainAddr(objAddr: ehAddr);
		});
		:errorHandlerAddr: ehAddr;
		:hasErrorHandler: :hasClosure(cb: onError);
	}

	## Opens a structured concurrency scope, executes [body] with the scope,
	## and joins all spawned tasks before returning.
	held Function is open(Function is body, Function is onError: local Function of Boolean(SpecError is _err){ return false; }){
		local ThreadScope is scope: ThreadScope:init(onError: onError);
		scope:runOpen(body: body);
	}

	local Function is runOpen(Function is body){
		local Int is bodyErrAddr: Mem:callCatching(action: local Function(){
			if({ :hasClosure(cb: body) }, {
				body(:);
			});
		});
		if({ bodyErrAddr != 0 }, {
			:cancel();
		});
		local Int is joinErrAddr: Mem:callCatching(action: local Function(){
			:joinAll();
		});
		local Int is finalUnhandledAddr: 0;
		if({ bodyErrAddr != 0 }, {
			local Int is uBodyAddr: :handleErrorAddr(errAddr: bodyErrAddr);
			Mem:releaseAddr(objAddr: bodyErrAddr);
			finalUnhandledAddr: :mergeUnhandledError(primaryAddr: finalUnhandledAddr, nextAddr: uBodyAddr);
		});
		if({ joinErrAddr != 0 }, {
			finalUnhandledAddr: :mergeUnhandledError(primaryAddr: finalUnhandledAddr, nextAddr: joinErrAddr);
		});
		if({ finalUnhandledAddr != 0 }, {
			Mem:raisePendingErrorAddr(addr: finalUnhandledAddr);
			Mem:releaseAddr(objAddr: finalUnhandledAddr);
		});
	}

	## Spawns [task] on a new thread bound to this scope and returns a [Task].
	## [kind] is supplied by the compiler (`0` = Int/Bool/Byte, `1` = ARC ptr, `2` = Float, `3` = Void).
	Function of Task is spawn(Function is task, Int is kind: Reflection:closureReturnKind()){
		local Task is t: Task:init(isArc: kind == 1);
		Thread:mutexLock(handle: :mutex);
		:tasks:add(item: t);
		Thread:mutexUnlock(handle: :mutex);

		local Function is worker: local Function(){
			t:markRunning();
			if({ kind == 3 }, {
				local Int is errAddr: Mem:callCatching(action: local Function(){
					task();
				});
				if({ errAddr != 0 }, {
					:cancel();
					t:failAddr(errAddr: errAddr);
					Mem:releaseAddr(objAddr: errAddr);
				}, {
					t:complete(value: Mem:addrToObj(addr: 0));
				});
			}, {
				local Int is errAddr: Mem:callCatching(action: local Function(){
					local Any is res: task();
					if({ !Mem:hasPendingError() }, {
						t:complete(value: res);
					});
				});
				if({ errAddr != 0 }, {
					:cancel();
					t:failAddr(errAddr: errAddr);
					Mem:releaseAddr(objAddr: errAddr);
				});
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
	## If any tasks in [group] fail, merges their errors (attaching secondary errors)
	## and raises the failure immediately without executing [then].
	Function is awaitAll(Array of Task is group, Function is then: local Function(){}){
		local Int is primaryErrAddr: 0;
		local Int is i: 0;
		while({ i < group:length() }, {
			local Task is t: group:get(index: i);
			if({ Mem:objToAddr(obj: t) != 0 }, {
				t:joinOnly();
				if({ t:isFailed() && !t:isErrorConsumed() }, {
					t:markErrorConsumed();
					:cancel();
					local Int is tErrAddr: t:getErrorAddr();
					if({ tErrAddr != 0 }, {
						Mem:retainAddr(objAddr: tErrAddr);
						primaryErrAddr: :mergeUnhandledError(primaryAddr: primaryErrAddr, nextAddr: tErrAddr);
					});
				});
			});
			i: i + 1;
		});
		if({ primaryErrAddr != 0 }, {
			Mem:raisePendingErrorAddr(addr: primaryErrAddr);
			Mem:releaseAddr(objAddr: primaryErrAddr);
			return;
		});
		if({ :hasClosure(cb: then) }, {
			then();
		});
	}

	## Joins all tasks currently in the scope and invokes [then] if no unhandled errors occurred.
	Function is onComplete(Function is then){
		:joinAll();
		if({ !Mem:hasPendingError() && :hasClosure(cb: then) }, {
			then();
		});
	}

	## Joins all tasks spawned in this scope (including tasks spawned dynamically by children).
	Function is joinAll(){
		if({ :mutex == 0 }, { return; });
		local Int is idx: 0;
		local Boolean is more: true;
		local Int is primaryUnhandledAddr: 0;
		while({ more }, {
			Thread:mutexLock(handle: :mutex);
			local Int is total: :tasks:length();
			local Boolean is hasNext: idx < total;
			local Task is nextTask: if({ hasNext }, { :tasks:get(index: idx) }, { Mem:addrToObj(addr: 0) as Task });
			Thread:mutexUnlock(handle: :mutex);
			if({ hasNext }, {
				if({ Mem:objToAddr(obj: nextTask) != 0 }, {
					nextTask:joinOnly();
					if({ nextTask:isFailed() && !nextTask:isErrorConsumed() }, {
						nextTask:markErrorConsumed();
						:cancel();
						local Int is uAddr: :handleErrorAddr(errAddr: nextTask:getErrorAddr());
						primaryUnhandledAddr: :mergeUnhandledError(primaryAddr: primaryUnhandledAddr, nextAddr: uAddr);
					});
				});
				idx: idx + 1;
			}, {
				more: false;
			});
		});
		if({ primaryUnhandledAddr != 0 }, {
			Mem:raisePendingErrorAddr(addr: primaryUnhandledAddr);
			Mem:releaseAddr(objAddr: primaryUnhandledAddr);
		});
	}

	Function is destroy(){
		:joinAll();
		if({ :errorHandlerAddr != 0 }, {
			Mem:releaseAddr(objAddr: :errorHandlerAddr);
			:errorHandlerAddr: 0;
		});
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
