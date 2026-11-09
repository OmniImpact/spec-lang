#! Package base:sys
#! Public wrapper over the sysinternal introspection floor.

## Object introspection: identity hashes and runtime type queries.
## The ONLY class allowed to call base:sysinternal:Introspection is the
## same-name wrapper (the sysinternal discipline).

Class is Introspection{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sysinternal', Introspection]
	];

	## The identity hash of an object: a stable per-object value derived
	## from its address (mixed so neighboring allocations differ).
	##
	## @param obj: The object.
	## @return: The hash.
	Function of Int is objectHash(Any is obj){
		return base:sysinternal:Introspection:objectHash(obj: obj);
	}
}
