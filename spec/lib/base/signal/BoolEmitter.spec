#! Package base:signal
#! Boolean-specialized [Emitter] convenience subclass.

Class of Emitter is BoolEmitter{
	replace [String] is namespace: ['base', 'signal'];

	replace [[String]] is using: [
		['base', 'signal', Emitter],
		['base', 'signal', Collector],
		['base', 'signal', BoolCollector],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Boolean is boolValue: false;
	Array of Boolean is replayBuffer: Array();

	replace Function is init(Boolean is initial: false, Int is replay: 1){
		initEmitter(replay: replay);
		:boolValue: initial;
		:replayBuffer: Array();
		if({ replay != 0 }, {
			:replayBuffer:add(item: initial);
		});
	}

	## Returns the most recent boolean value.
	Function of Boolean is current(){
		return boolValue;
	}

	## Emits a new boolean [value].
	Function is emit(Boolean is value){
		:boolValue: value;
		if({ replayCount != 0 }, {
			replayBuffer:add(item: value);
			if({ replayCount > 0 && replayBuffer:length() > replayCount }, {
				replayBuffer:removeAt(index: 0);
			});
		});
		local String is s: if({ value }, { 'true' }, { 'false' });
		notifyCollectors(value: s);
	}

	replace Function is replayInto(Collector is collector){
		local Int is i: 0;
		while({ i < replayBuffer:length() }, {
			if({ collector:active }, {
				local Boolean is bv: replayBuffer:get(index: i);
				local String is s: if({ bv }, { 'true' }, { 'false' });
				collector:onSignal(value: s);
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
