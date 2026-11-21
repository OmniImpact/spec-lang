#! base:sys wrapper over the sysinternal Defer floor.
#! Deferred actions run when the calling frame exits — newest-first among
#! that frame's registrations, on normal and unwind exits alike. A
#! registration belongs to the frame whose body performed the push (the
#! emitter gives wrapper/floor frames no cleanup barrier of their own).

Class is Defer{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Cleanup]
	];

	## Registers [action] to run when the calling frame exits. The
	## registration owns its own reference to [action], so the action may
	## outlive the local binding it came from.
	Function is push(Function is action){
		base:sysinternal:Cleanup:pushCleanup(action: action);
	}
}
