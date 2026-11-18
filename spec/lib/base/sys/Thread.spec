#! Package base:sys
#! Same-name wrapper over the OS thread, mutex, and condition-variable floor (`base:sysinternal:Thread`).
##
## Raw thread creation (`threadSpawn` / `threadJoin`) is compiler-restricted to
## `base:sys:thread` (`ThreadScope` and `Task`); all user threads must run
## inside a `ThreadScope:open` block.

Class is Thread{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Thread]
	];

	## Spawns an OS thread executing [task] and returns its handle (`0` if run inline).
	## Restricted by the type checker to `base:sys:thread`.
	Function of Int is threadSpawn(Function is task){
		return base:sysinternal:Thread:thread_spawn(task: task);
	}

	## Joins the OS thread [handle] and frees its handle.
	## Restricted by the type checker to `base:sys:thread`.
	Function is threadJoin(Int is handle){
		base:sysinternal:Thread:thread_join(handle: handle);
	}

	## Returns a unique identifier for the calling OS thread.
	Function of Int is currentId(){
		return base:sysinternal:Thread:thread_current_id();
	}

	## Allocates and initializes an OS mutex.
	Function of Int is mutexCreate(){
		return base:sysinternal:Thread:mutex_create();
	}

	## Destroys and frees an OS mutex [handle].
	Function is mutexDestroy(Int is handle){
		base:sysinternal:Thread:mutex_destroy(handle: handle);
	}

	## Acquires an OS mutex [handle].
	Function is mutexLock(Int is handle){
		base:sysinternal:Thread:mutex_lock(handle: handle);
	}

	## Releases an OS mutex [handle].
	Function is mutexUnlock(Int is handle){
		base:sysinternal:Thread:mutex_unlock(handle: handle);
	}

	## Allocates and initializes an OS condition variable.
	Function of Int is condCreate(){
		return base:sysinternal:Thread:cond_create();
	}

	## Destroys and frees an OS condition variable [handle].
	Function is condDestroy(Int is handle){
		base:sysinternal:Thread:cond_destroy(handle: handle);
	}

	## Atomically releases [mutex] and waits on condition variable [cond], re-acquiring [mutex] before returning.
	Function is condWait(Int is cond, Int is mutex){
		base:sysinternal:Thread:cond_wait(cond: cond, mutex: mutex);
	}

	## Wakes one thread waiting on condition variable [cond].
	Function is condSignal(Int is cond){
		base:sysinternal:Thread:cond_signal(cond: cond);
	}

	## Wakes all threads waiting on condition variable [cond].
	Function is condBroadcast(Int is cond){
		base:sysinternal:Thread:cond_broadcast(cond: cond);
	}
}
