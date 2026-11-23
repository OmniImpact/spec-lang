#! Package base:signal
#! Base reactive signal source managing [Collector] subscriptions.

Class is Emitter{
	namespace: ['base', 'signal'];

	replace Array of Array of String is using: [
		['base', 'signal', Collector],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Int is replayCount: 1;
	Array of Collector is collectors: Array();

	Function is initEmitter(Int is replay: 1){
		:replayCount: replay;
		:collectors: Array();
	}

	replace Function is init(Int is replay: 1){
		initEmitter(replay: replay);
	}

	## Notifies all active collectors with [value] and prunes disposed ones.
	Function is notifyCollectors(Any is value){
		local Int is i: 0;
		while({ i < collectors:length() }, {
			local Collector is c: collectors:get(index: i);
			if({ c:active }, {
				c:onSignal(value: value);
				i: i + 1;
			}, {
				collectors:removeAt(index: i);
			});
		});
	}

	## Override in subclasses to replay buffered values into [collector].
	Function is replayInto(Collector is collector){
	}

	## Attaches [collector], replays buffered emissions immediately, and returns it.
	Function of Collector is attach(Collector is collector){
		collectors:add(item: collector);
		replayInto(collector: collector);
		return collector;
	}

	## Detaches and disposes [collector].
	Function is detach(Collector is collector){
		collector:dispose();
		local Int is i: 0;
		while({ i < collectors:length() }, {
			if({ collectors:get(index: i) == collector }, {
				collectors:removeAt(index: i);
				return;
			});
			i: i + 1;
		});
	}
}
