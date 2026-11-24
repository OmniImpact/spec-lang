#! Package base:sysinternal
#! OS thread, mutex, and condition-variable floor declarations.

Class is Thread{
	replace [String] is namespace: ['base', 'sysinternal'];

	## Spawns an OS thread executing [task] and returns its thread handle (`0` if run inline).
	## Bound to `spec_thread_spawn`.
	Function of Int is thread_spawn(Function is task);

	## Waits for the OS thread [handle] to finish and frees its handle.
	## Bound to `spec_thread_join`.
	Function is thread_join(Int is handle);

	## Returns a unique identifier for the calling OS thread.
	## Bound to `spec_thread_current_id`.
	Function of Int is thread_current_id();

	## Allocates and initializes an OS mutex. Bound to `spec_mutex_create`.
	Function of Int is mutex_create();

	## Destroys and frees an OS mutex [handle]. Bound to `spec_mutex_destroy`.
	Function is mutex_destroy(Int is handle);

	## Acquires an OS mutex [handle]. Bound to `spec_mutex_lock`.
	Function is mutex_lock(Int is handle);

	## Releases an OS mutex [handle]. Bound to `spec_mutex_unlock`.
	Function is mutex_unlock(Int is handle);

	## Allocates and initializes an OS condition variable. Bound to `spec_cond_create`.
	Function of Int is cond_create();

	## Destroys and frees an OS condition variable [handle]. Bound to `spec_cond_destroy`.
	Function is cond_destroy(Int is handle);

	## Atomically releases [mutex] and waits on condition variable [cond], re-acquiring [mutex] before returning.
	## Bound to `spec_cond_wait`.
	Function is cond_wait(Int is cond, Int is mutex);

	## Wakes one thread waiting on condition variable [cond].
	## Bound to `spec_cond_signal`.
	Function is cond_signal(Int is cond);

	## Wakes all threads waiting on condition variable [cond].
	## Bound to `spec_cond_broadcast`.
	Function is cond_broadcast(Int is cond);
}
