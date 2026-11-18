#! Package base:sys
#! Heap-allocated reference cell for shared mutable state.
##
## A Box holds a single value of type T on the heap. Multiple references
## to the same Box share access to the wrapped value, enabling shared mutable
## state across scopes, closure captures, and pass-by-reference patterns.
##
## ARC memory discipline:
## For ARC-managed types (String, Array, Map, List, custom class instances),
## [isArc] defaults to true so values are retained and released properly.
## For unmanaged primitives (Int, Boolean, Byte), [isArc] should be false.

Class is Box of T{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()]
	];

	local T is val;
	local Boolean is arcManaged: false;

	## Creates a new heap-allocated box containing [value].
	##
	## @param value: The initial value to store in the box.
	## @param isArc: True if [value] is an ARC-managed reference (default: true).
	## @return: The initialized Box instance.
	replace Function is init(T is value, Boolean is isArc: true){
		:arcManaged: isArc;
		if({ isArc }, {
			local Int is addr: Mem:objToAddr(obj: value);
			if({ addr != 0 }, {
				Mem:retainAddr(objAddr: addr);
			});
		});
		:val: value;
	}

	## Retrieves the current value stored in the box.
	##
	## @return: The wrapped value.
	Function of T is get(){
		if({ :arcManaged }, {
			local Int is addr: Mem:objToAddr(obj: :val);
			if({ addr != 0 }, {
				Mem:retainAddr(objAddr: addr);
				Mem:claimPoolAddr(objAddr: addr);
			});
		});
		return :val;
	}

	## Updates the value stored in the box.
	##
	## @param value: The new value.
	Function is set(T is value){
		if({ :arcManaged }, {
			local Int is newAddr: Mem:objToAddr(obj: value);
			local Int is oldAddr: Mem:objToAddr(obj: :val);
			if({ newAddr != 0 }, {
				Mem:retainAddr(objAddr: newAddr);
			});
			if({ oldAddr != 0 }, {
				Mem:releaseAddr(objAddr: oldAddr);
			});
		});
		:val: value;
	}

	## True if the box is configured for ARC-managed references.
	##
	## @return: True if ARC managed.
	Function of Boolean is isArc(){
		return :arcManaged;
	}

	## Releases the boxed reference when this Box is destroyed.
	Function is destroy(){
		if({ :arcManaged }, {
			local Int is oldAddr: Mem:objToAddr(obj: :val);
			if({ oldAddr != 0 }, {
				Mem:releaseAddr(objAddr: oldAddr);
				:val: Mem:addrToObj(addr: 0);
			});
		});
	}

	## String representation of the box.
	##
	## @return: String representation.
	replace Function of String is toString(){
		local Int is raw: Mem:objToAddr(obj: :val);
		if({ !:arcManaged }, {
			return 'Box(' . (raw as String) . ')';
		});
		if({ raw == 0 }, {
			return 'Box(null)';
		});
		local Any is obj: Mem:addrToObj(addr: raw);
		return 'Box(' . obj . ')';
	}
}
