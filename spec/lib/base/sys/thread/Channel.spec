#! Package base:sys:thread
#! Thread-safe bounded and unbounded producer/consumer channels (`Channel of T`).
##
## Built directly over the `base:sys:Thread` mutex and condition-variable floor
## using a dynamically growing ring buffer (no fixed caps on unbounded channels).

Class is Channel of T{
	namespace: ['base', 'sys', 'thread'];

	replace Array of Array of String is using: [
		['base', 'sys', as Thread()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Int is bufAddr: 0;
	local Int is bufCap: 0;
	local Int is maxCapacity: 0;
	local Int is head: 0;
	local Int is tail: 0;
	local Int is count: 0;
	local Boolean is closed: false;
	local Boolean is arcManaged: false;
	local Int is mutex: 0;
	local Int is notEmpty: 0;
	local Int is notFull: 0;

	replace Function is init(Int is maxCap: 0, Boolean is isArc: false){
		:maxCapacity: if({ maxCap > 0 }, { maxCap }, { 0 });
		:arcManaged: isArc;
		local Int is initCap: if({ :maxCapacity > 0 && :maxCapacity < 16 }, { :maxCapacity }, { 16 });
		:bufCap: initCap;
		:bufAddr: Mem:alloc(bytes: initCap * 8);
		:head: 0;
		:tail: 0;
		:count: 0;
		:closed: false;
		:mutex: Thread:mutexCreate();
		:notEmpty: Thread:condCreate();
		:notFull: Thread:condCreate();
	}

	## Creates an unbounded channel whose ring buffer grows dynamically as needed.
	Function of Channel is unbounded(Boolean is isArc: false){
		return Channel:init(maxCap: 0, isArc: isArc);
	}

	## Creates a bounded channel with backpressure capacity [capacity] (`>= 1`).
	Function of Channel is bounded(Int is capacity, Boolean is isArc: false){
		local Int is cap: if({ capacity < 1 }, { 1 }, { capacity });
		return Channel:init(maxCap: cap, isArc: isArc);
	}

	local Function is growBuffer(){
		local Int is newCap: :bufCap * 2;
		if({ :maxCapacity > 0 && newCap > :maxCapacity }, {
			newCap: :maxCapacity;
		});
		if({ newCap <= :bufCap }, { return; });
		local Int is newBuf: Mem:alloc(bytes: newCap * 8);
		local Int is i: 0;
		while({ i < :count }, {
			local Int is slotIdx: (:head + i) % :bufCap;
			local Int is valBits: Mem:loadI64(ptr: :bufAddr, byteOffset: slotIdx * 8);
			Mem:storeI64(ptr: newBuf, byteOffset: i * 8, val: valBits);
			i: i + 1;
		});
		Mem:free(ptr: :bufAddr);
		:bufAddr: newBuf;
		:bufCap: newCap;
		:head: 0;
		:tail: :count;
	}

	## Enqueues [item] into the channel, blocking if the channel is bounded and full.
	## Returns `false` if the channel is closed.
	Function of Boolean is send(T is item){
		Thread:mutexLock(handle: :mutex);
		while({ !:closed && :maxCapacity > 0 && :count >= :maxCapacity }, {
			Thread:condWait(cond: :notFull, mutex: :mutex);
		});
		if({ :closed }, {
			Thread:mutexUnlock(handle: :mutex);
			return false;
		});
		if({ :count >= :bufCap }, {
			:growBuffer();
		});
		local Int is bits: Mem:objToAddr(obj: item);
		if({ :arcManaged && bits != 0 }, {
			Mem:retainAddr(objAddr: bits);
		});
		Mem:storeI64(ptr: :bufAddr, byteOffset: :tail * 8, val: bits);
		:tail: (:tail + 1) % :bufCap;
		:count: :count + 1;
		Thread:condSignal(cond: :notEmpty);
		Thread:mutexUnlock(handle: :mutex);
		return true;
	}

	## Dequeues and returns the next item, blocking until an item arrives or the
	## channel closes. Returns [default] when closed and empty.
	Function of T is receive(T is default){
		Thread:mutexLock(handle: :mutex);
		while({ :count == 0 && !:closed }, {
			Thread:condWait(cond: :notEmpty, mutex: :mutex);
		});
		if({ :count == 0 }, {
			Thread:mutexUnlock(handle: :mutex);
			return default;
		});
		local Int is bits: Mem:loadI64(ptr: :bufAddr, byteOffset: :head * 8);
		Mem:storeI64(ptr: :bufAddr, byteOffset: :head * 8, val: 0);
		:head: (:head + 1) % :bufCap;
		:count: :count - 1;
		if({ :maxCapacity > 0 }, {
			Thread:condSignal(cond: :notFull);
		});
		Thread:mutexUnlock(handle: :mutex);
		if({ :arcManaged && bits != 0 }, {
			Mem:claimPoolAddr(objAddr: bits);
		});
		return Mem:addrToObj(addr: bits);
	}

	## Non-blocking receive: dequeues and returns the next item if immediately
	## available, or returns [default] when empty.
	Function of T is tryReceive(T is default){
		Thread:mutexLock(handle: :mutex);
		if({ :count == 0 }, {
			Thread:mutexUnlock(handle: :mutex);
			return default;
		});
		local Int is bits: Mem:loadI64(ptr: :bufAddr, byteOffset: :head * 8);
		Mem:storeI64(ptr: :bufAddr, byteOffset: :head * 8, val: 0);
		:head: (:head + 1) % :bufCap;
		:count: :count - 1;
		if({ :maxCapacity > 0 }, {
			Thread:condSignal(cond: :notFull);
		});
		Thread:mutexUnlock(handle: :mutex);
		if({ :arcManaged && bits != 0 }, {
			Mem:claimPoolAddr(objAddr: bits);
		});
		return Mem:addrToObj(addr: bits);
	}

	## Marks the channel closed and wakes all waiting senders and receivers.
	Function is close(){
		Thread:mutexLock(handle: :mutex);
		:closed: true;
		Thread:condBroadcast(cond: :notEmpty);
		Thread:condBroadcast(cond: :notFull);
		Thread:mutexUnlock(handle: :mutex);
	}

	## True when the channel has been closed.
	Function of Boolean is isClosed(){
		Thread:mutexLock(handle: :mutex);
		local Boolean is c: :closed;
		Thread:mutexUnlock(handle: :mutex);
		return c;
	}

	## Number of buffered items currently in the channel.
	Function of Int is length(){
		Thread:mutexLock(handle: :mutex);
		local Int is n: :count;
		Thread:mutexUnlock(handle: :mutex);
		return n;
	}

	## Drains items from this channel, invoking [onItem] for each received value
	## until the channel is closed and empty.
	Function is collect(Function is onItem){
		local Boolean is active: true;
		while({ active }, {
			Thread:mutexLock(handle: :mutex);
			while({ :count == 0 && !:closed }, {
				Thread:condWait(cond: :notEmpty, mutex: :mutex);
			});
			if({ :count == 0 }, {
				Thread:mutexUnlock(handle: :mutex);
				active: false;
			}, {
				local Int is bits: Mem:loadI64(ptr: :bufAddr, byteOffset: :head * 8);
				Mem:storeI64(ptr: :bufAddr, byteOffset: :head * 8, val: 0);
				:head: (:head + 1) % :bufCap;
				:count: :count - 1;
				if({ :maxCapacity > 0 }, {
					Thread:condSignal(cond: :notFull);
				});
				Thread:mutexUnlock(handle: :mutex);
				if({ :arcManaged && bits != 0 }, {
					Mem:claimPoolAddr(objAddr: bits);
				});
				local T is item: Mem:addrToObj(addr: bits);
				onItem(item);
			});
		});
	}

	Function is destroy(){
		if({ :bufAddr != 0 }, {
			if({ :arcManaged }, {
				local Int is i: 0;
				while({ i < :count }, {
					local Int is slotIdx: (:head + i) % :bufCap;
					local Int is bits: Mem:loadI64(ptr: :bufAddr, byteOffset: slotIdx * 8);
					if({ bits != 0 }, {
						Mem:releaseAddr(objAddr: bits);
					});
					i: i + 1;
				});
			});
			Mem:free(ptr: :bufAddr);
			:bufAddr: 0;
		});
		if({ :notEmpty != 0 }, {
			Thread:condDestroy(handle: :notEmpty);
			:notEmpty: 0;
		});
		if({ :notFull != 0 }, {
			Thread:condDestroy(handle: :notFull);
			:notFull: 0;
		});
		if({ :mutex != 0 }, {
			Thread:mutexDestroy(handle: :mutex);
			:mutex: 0;
		});
	}
}
