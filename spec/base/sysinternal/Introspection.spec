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

	## The number of HELD members the object's class declares
	## (PLAN-ENUM Stage 1) — the declaring class's own held surface, in
	## declaration order (the ordinal index).
	##
	## @param obj: The object.
	## @return: The held-member count.
	Function of Int is heldCount(Any is obj);

	## The name of the object's class's held member at the ordinal
	## index (declaration order); an empty string when the index is out
	## of range or the class holds none.
	##
	## @param obj: The object.
	## @param index: The ordinal index.
	## @return: The member name.
	Function of String is heldName(Any is obj, Int is index);

	## Whether the name is a held member of the object's class.
	##
	## @param obj: The object.
	## @param name: The member name.
	## @return: true when held.
	Function of Boolean is hasHeld(Any is obj, String is name);
}
