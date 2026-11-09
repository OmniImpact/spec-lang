#! Package base:sysinternal
#! The introspection floor: runtime identity and type queries.

## Floor bindings for object introspection. Methods bind to their C
## implementations per the naming convention (`spec_<snake_case>`); only
## the same-name base:sys wrapper may call them.

Class is Introspection{
	namespace: ['base', 'sysinternal'];

	## The identity hash of an object: a stable per-object value derived
	## from its address (mixed so neighboring allocations differ).
	##
	## @param obj: The object.
	## @return: The hash.
	Function of Int is objectHash(Any is obj);
}
