#! Package base:sys:thread
#! Cold and concurrent asynchronous event streams (`Flow of T`) layered over
#! `ThreadScope` and monomorphized `Channel of T`.

Class is Flow of T{
	replace [String] is namespace: ['base', 'sys', 'thread'];

	replace [[String]] is using: [
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task],
		['base', 'sys', 'thread', Channel],
		['base', 'sys', as Mem()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array]
	];

	local Int is producerAddr: 0;

	local Function is invokeProducer(Function is prod, Function is emit){
		prod(emit);
	}

	local Function is invokeEmit(Function is emit, T is item){
		emit(item);
	}

	local Function of Any is invokeTransform(Function is fn, T is item){
		return fn(item);
	}

	local Function of Boolean is invokePredicate(Function is pred, T is item){
		local Any is r: pred(item);
		return (Mem:objToAddr(obj: r) & 1) != 0;
	}

	replace Function is init(Function is producer: local Function(Function is _emit){}){
		local Int is pAddr: Mem:objToAddr(obj: producer);
		if({ pAddr != 0 }, {
			Mem:retainAddr(objAddr: pAddr);
		});
		:producerAddr: pAddr;
	}

	local Function of Flow of T is setProducer(Function is producer){
		local Int is pAddr: Mem:objToAddr(obj: producer);
		if({ pAddr != 0 }, {
			Mem:retainAddr(objAddr: pAddr);
		});
		if({ :producerAddr != 0 }, {
			Mem:releaseAddr(objAddr: :producerAddr);
		});
		:producerAddr: pAddr;
		return :;
	}

	Function is destroy(){
		if({ :producerAddr != 0 }, {
			Mem:releaseAddr(objAddr: :producerAddr);
			:producerAddr: 0;
		});
	}

	## Creates a cold [Flow] that emits each element of [items] in order.
	held Function of Flow of T is fromArray(Array of T is items){
		local Flow of T is fl: Flow:init();
		return fl:buildFromArray(items: items);
	}

	local Function of Flow of T is buildFromArray(Array of T is items){
		return :setProducer(producer: local Function(Function is emit){
			local Int is i: 0;
			while({ i < items:length() && !Mem:hasPendingError() }, {
				emit(items:get(index: i));
				i: i + 1;
			});
		});
	}

	## Collects all items emitted by this flow on the calling thread.
	Function is collect(Function is onItem){
		if({ :producerAddr != 0 }, {
			local Function is prod: Mem:addrToObj(addr: :producerAddr);
			if({ Mem:hasClosure(cb: prod) }, {
				:invokeProducer(prod: prod, emit: onItem);
			});
		});
	}

	## Transforms each emitted item using [transform].
	Function of Flow of R is map(Function of R is transform){
		local Flow of T is upstream: :;
		local Flow of R is out: Flow:init();
		return out:setProducer(producer: local Function(Function is emit){
			upstream:collect(onItem: local Function(T is item){
				if({ !Mem:hasPendingError() }, {
					local R is mapped: transform(item);
					if({ !Mem:hasPendingError() }, {
						emit(mapped);
					});
				});
			});
		});
	}

	## Emits only items for which [predicate] returns `true`.
	Function of Flow of T is filter(Function is predicate){
		local Flow of T is upstream: :;
		return Flow:init(producer: local Function(Function is emit){
			upstream:collect(onItem: local Function(T is item){
				if({ !Mem:hasPendingError() }, {
					if({ upstream:invokePredicate(pred: predicate, item: item) && !Mem:hasPendingError() }, {
						upstream:invokeEmit(emit: emit, item: item);
					});
				});
			});
		});
	}

	## Emits at most the first [count] items from this flow.
	Function of Flow of T is take(Int is count){
		local Flow of T is upstream: :;
		return Flow:init(producer: local Function(Function is emit){
			local Int is taken: 0;
			upstream:collect(onItem: local Function(T is item){
				if({ taken < count && !Mem:hasPendingError() }, {
					taken: taken + 1;
					upstream:invokeEmit(emit: emit, item: item);
				});
			});
		});
	}

	## Invokes [action] on each item before forwarding it downstream.
	Function of Flow of T is onEach(Function is action){
		local Flow of T is upstream: :;
		return Flow:init(producer: local Function(Function is emit){
			upstream:collect(onItem: local Function(T is item){
				if({ !Mem:hasPendingError() }, {
					upstream:invokeEmit(emit: action, item: item);
					if({ !Mem:hasPendingError() }, {
						upstream:invokeEmit(emit: emit, item: item);
					});
				});
			});
		});
	}

	## Invokes [action] after upstream collection completes.
	Function of Flow of T is onCompletion(Function is action){
		local Flow of T is upstream: :;
		return Flow:init(producer: local Function(Function is emit){
			upstream:collect(onItem: emit);
			if({ !Mem:hasPendingError() && Mem:hasClosure(cb: action) }, {
				action();
			});
		});
	}

	## Runs this flow's producer concurrently inside a [ThreadScope] writing into a
	## [Channel] of [capacity] (unbounded when `capacity <= 0`), draining on the collector thread.
	Function of Flow of T is buffer(Int is capacity: 0){
		local Flow of T is upstream: :;
		return Flow:init(producer: local Function(Function is emit){
			local Channel of T is chan: if({ capacity > 0 }, {
				Channel:bounded(capacity: capacity)
			}, {
				Channel:unbounded()
			});
			ThreadScope:open(body: local Function(ThreadScope is scope){
				scope:spawn(task: local Function(){
					upstream:collect(onItem: local Function(T is item){
						chan:send(item: item);
					});
					chan:close();
				});
				chan:collect(onItem: emit);
			});
		});
	}

	## Creates a concurrent [Flow of T] whose [producer] receives `(ThreadScope is scope, Channel of T is channel)`.
	## When all tasks spawned in `scope` by `producer` finish, `channel` is closed automatically.
	held Function of Flow of T is channelFlow(Function is producer, Int is capacity: 0){
		local Flow of T is fl: Flow:init();
		return fl:buildChannelFlow(producer: producer, capacity: capacity);
	}

	local Function of Flow of T is buildChannelFlow(Function is producer, Int is capacity){
		return :setProducer(producer: local Function(Function is emit){
			local Channel of T is chan: if({ capacity > 0 }, {
				Channel:bounded(capacity: capacity)
			}, {
				Channel:unbounded()
			});
			ThreadScope:open(
				body: local Function(ThreadScope is outerScope){
					outerScope:spawn(task: local Function(){
						ThreadScope:open(
							body: local Function(ThreadScope is innerScope){
								producer(innerScope, chan);
							},
							onError: local Function of Boolean(Any is _err){
								return false;
							}
						);
						chan:close();
					});
					chan:collect(onItem: emit);
				},
				onError: local Function of Boolean(Any is _err){
					return false;
				}
			);
		});
	}

	## Merges multiple [flows] concurrently inside a [ThreadScope] into a single [Flow of T].
	held Function of Flow of T is merge(Array of Flow is flows, Int is capacity: 0){
		local Flow of T is fl: Flow:init();
		return fl:buildMerge(flows: flows, capacity: capacity);
	}

	local Function of Flow of T is buildMerge(Array of Flow is flows, Int is capacity){
		return :setProducer(producer: local Function(Function is emit){
			local Channel of T is chan: if({ capacity > 0 }, {
				Channel:bounded(capacity: capacity)
			}, {
				Channel:unbounded()
			});
			ThreadScope:open(
				body: local Function(ThreadScope is scope){
					local Array of Task is producers: Array();
					local Int is i: 0;
					while({ i < flows:length() }, {
						local Flow of T is f: flows:get(index: i);
						local Task is pt: scope:spawn(task: local Function(){
							f:collect(onItem: local Function(T is item){
								chan:send(item: item);
							});
						});
						producers:add(item: pt);
						i: i + 1;
					});
					scope:spawn(task: local Function(){
						scope:awaitAll(group: producers);
						chan:close();
					});
					chan:collect(onItem: emit);
				},
				onError: local Function of Boolean(Any is _err){
					return false;
				}
			);
		});
	}
}
