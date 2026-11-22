#! Package base:sys
#! Lightweight atomic spinlock built over base:sys:Mem.

## A lightweight non-reentrant atomic spinlock for guarding concurrent
## mutations on shared runtime structures.
Class is SpinLock{
	namespace: ['base', 'sys'];

	replace Array of Array of String is using: [
		['base', 'sys', as Mem()],
		['base', 'sys', as Loops()]
	];

	local Int is state: 0;

	replace Function is init(){
	}

	## Acquires the spinlock, spinning until the lock becomes available.
	Function is lock(){
		local Int is slotAddr: Mem:objToAddr(obj: :) + 16;
		while({ !Mem:atomicCasI64(addr: slotAddr, expected: 0, desired: 1) }, {
		});
	}

	## Releases the spinlock.
	Function is unlock(){
		Mem:atomicStoreI64(addr: Mem:objToAddr(obj: :) + 16, val: 0);
	}
}
