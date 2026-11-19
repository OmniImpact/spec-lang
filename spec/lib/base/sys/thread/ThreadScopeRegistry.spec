#! Package base:sys:thread
#! Thread-safe per-thread stack of active `ThreadScope` addresses.

Class is ThreadScopeRegistry{
	namespace: ['base', 'sys', 'thread'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Thread()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Int is mutex: 0;
	local Array of Int is threadIds: [];
	local Array of Int is scopeAddrs: [];

	replace Function is init(){
		:mutex: Thread:mutexCreate();
		:threadIds: [];
		:scopeAddrs: [];
	}

	Function is push(Int is tid, Int is scopeAddr){
		Thread:mutexLock(handle: :mutex);
		:threadIds:add(item: tid);
		:scopeAddrs:add(item: scopeAddr);
		Thread:mutexUnlock(handle: :mutex);
	}

	Function is pop(Int is tid){
		Thread:mutexLock(handle: :mutex);
		local Int is i: :threadIds:length() - 1;
		while({ i >= 0 }, {
			if({ :threadIds:get(index: i) == tid }, {
				:threadIds:removeAt(index: i);
				:scopeAddrs:removeAt(index: i);
				i: -1;
			}, {
				i: i - 1;
			});
		});
		Thread:mutexUnlock(handle: :mutex);
	}

	Function of Int is current(){
		local Int is tid: Thread:currentId();
		local Int is found: 0;
		Thread:mutexLock(handle: :mutex);
		local Int is i: :threadIds:length() - 1;
		while({ i >= 0 }, {
			if({ :threadIds:get(index: i) == tid }, {
				found: :scopeAddrs:get(index: i);
				i: -1;
			}, {
				i: i - 1;
			});
		});
		Thread:mutexUnlock(handle: :mutex);
		return found;
	}
}
