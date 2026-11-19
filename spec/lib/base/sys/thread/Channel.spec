#! Package base:sys:thread
#! Thread-safe bounded and unbounded producer/consumer channels (`Channel of T`).
##
## Built over the `base:sys:Thread` mutex and condition-variable floor and
## monomorphized `Array of T` storage (no fixed caps on unbounded channels).

Class is Channel of T{
	namespace: ['base', 'sys', 'thread'];

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Thread()],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	local Array of T is buf: [];
	local T is zeroDefault;
	local Int is maxCapacity: 0;
	local Int is head: 0;
	local Int is count: 0;
	local Boolean is closed: false;
	local Int is mutex: 0;
	local Int is notEmpty: 0;
	local Int is notFull: 0;

	replace Function is init(Int is maxCap: 0){
		:buf: [];
		:maxCapacity: if({ maxCap > 0 }, { maxCap }, { 0 });
		:head: 0;
		:count: 0;
		:closed: false;
		:mutex: Thread:mutexCreate();
		:notEmpty: Thread:condCreate();
		:notFull: Thread:condCreate();
	}

	## Creates an unbounded channel whose queue grows dynamically as needed.
	held Function of Channel of T is unbounded(){
		return Channel:init(maxCap: 0);
	}

	## Creates a bounded channel with backpressure capacity [capacity] (`>= 1`).
	held Function of Channel of T is bounded(Int is capacity){
		local Channel of T is ch: Channel:init(maxCap: capacity);
		return ch:ensureBounded();
	}

	local Function of Channel of T is ensureBounded(){
		if({ :maxCapacity < 1 }, {
			:maxCapacity: 1;
		});
		return :;
	}

	local Function is compactIfNeeded(){
		if({ :count == 0 }, {
			:buf:clear();
			:head: 0;
			return;
		});
		if({ :head >= 64 && :head * 2 >= :buf:length() }, {
			local Array of T is compact: [];
			local Int is ci: :head;
			while({ ci < :buf:length() }, {
				compact:add(item: :buf:get(index: ci, default: :zeroDefault));
				ci: ci + 1;
			});
			:buf: compact;
			:head: 0;
		});
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
		:buf:add(item: item);
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
		local T is val: :buf:get(index: :head, default: default);
		:head: :head + 1;
		:count: :count - 1;
		:compactIfNeeded();
		if({ :maxCapacity > 0 }, {
			Thread:condSignal(cond: :notFull);
		});
		Thread:mutexUnlock(handle: :mutex);
		return val;
	}

	## Non-blocking receive: dequeues and returns the next item if immediately
	## available, or returns [default] when empty.
	Function of T is tryReceive(T is default){
		Thread:mutexLock(handle: :mutex);
		if({ :count == 0 }, {
			Thread:mutexUnlock(handle: :mutex);
			return default;
		});
		local T is val: :buf:get(index: :head, default: default);
		:head: :head + 1;
		:count: :count - 1;
		:compactIfNeeded();
		if({ :maxCapacity > 0 }, {
			Thread:condSignal(cond: :notFull);
		});
		Thread:mutexUnlock(handle: :mutex);
		return val;
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
				local T is item: :buf:get(index: :head, default: :zeroDefault);
				:head: :head + 1;
				:count: :count - 1;
				:compactIfNeeded();
				if({ :maxCapacity > 0 }, {
					Thread:condSignal(cond: :notFull);
				});
				Thread:mutexUnlock(handle: :mutex);
				onItem(item);
				if({ Mem:hasPendingError() }, {
					active: false;
				});
			});
		});
	}

	Function is destroy(){
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
