#! Package base:signal
#! Generic enum-specialized [Emitter] convenience subclass.

Class of Emitter is EnumEmitter of T{
	replace [String] is namespace: ['base', 'signal'];

	replace [[String]] is using: [
		['base', 'signal', Emitter],
		['base', 'signal', Collector],
		['base', 'signal', BoolCollector],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	T is enumValue;
	Array of T is replayBuffer: Array();

	replace Function is init(T is initial, Int is replay: 1){
		initEmitter(replay: replay);
		:enumValue: initial;
		:replayBuffer: Array();
		if({ replay != 0 }, {
			:replayBuffer:add(item: initial);
		});
	}

	## Returns the most recent enum value.
	Function of T is current(){
		return enumValue;
	}

	## Emits a new enum [value].
	Function is emit(T is value){
		:enumValue: value;
		if({ replayCount != 0 }, {
			replayBuffer:add(item: value);
			if({ replayCount > 0 && replayBuffer:length() > replayCount }, {
				replayBuffer:removeAt(index: 0);
			});
		});
		notifyCollectors(value: value);
	}

	replace Function is replayInto(Collector is collector){
		local Int is i: 0;
		while({ i < replayBuffer:length() }, {
			if({ collector:active }, {
				collector:onSignal(value: replayBuffer:get(index: i));
			});
			i: i + 1;
		});
	}

	## Attaches a zero-argument change callback as a [BoolCollector] and returns it.
	Function of BoolCollector is collect(Function is onEmit){
		local BoolCollector is c: BoolCollector(onEmit: onEmit);
		attach(collector: c);
		return c;
	}
}
