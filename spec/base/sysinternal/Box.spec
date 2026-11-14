#! Package base:sysinternal
#! The heap cell floor: primitive operations on managed reference cells.
##
## Body-less, interface-style declarations bound to the runtime's C floor.
## The namespace IS the binding annotation: every method compiles to
## spec_<snake_case(method)> per the floor naming convention. These are the
## ONLY methods in the system allowed to touch C; all other classes reach
## the floor through this class. Ownership follows the standard claim/retain
## conventions.

Class is Box{
	namespace: ['base', 'sysinternal'];

	## Allocates a new heap box initialized with [val].
	##
	## @param val: The initial value (stored as 64-bit int or pointer).
	## @param isArc: True if [val] is an ARC-managed heap object.
	## @return: The newly allocated box pointer.
	Function of Any is boxNew(Any is val, Boolean is isArc);

	## Retrieves the value currently stored in box [b].
	##
	## @param b: The box.
	## @return: The stored value.
	Function of Any is boxGet(Any is b);

	## Stores [newVal] into box [b], releasing previous ARC value if applicable.
	##
	## @param b: The box.
	## @param newVal: The new value to store.
	Function is boxSet(Any is b, Any is newVal);

	## True if box [b] holds an ARC-managed reference.
	##
	## @param b: The box.
	## @return: True if ARC managed.
	Function of Boolean is boxIsArc(Any is b);

	## Formats box [b] as a string representation.
	##
	## @param b: The box.
	## @return: Formatted string representation.
	Function of String is boxToString(Any is b);
}
