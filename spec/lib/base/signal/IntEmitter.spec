#! Package base:signal
#! Int-specialized [Emitter] convenience subclass.

Class of Emitter is IntEmitter{
	namespace: ['base', 'signal'];

	replace Array of Array of String is using: [
		['base', 'signal', Emitter],
		['base', 'signal', Collector],
		['base', 'signal', IntCollector],
		['base', 'signal', TextEmitter],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Int is intValue: 0;
	Array of Int is replayBuffer: Array();

	replace Function is init(Int is initial: 0, Int is replay: 1){
		initEmitter(replay: replay);
		:intValue: initial;
		:replayBuffer: Array();
		if({ replay != 0 }, {
			:replayBuffer:add(item: initial);
		});
	}

	## Returns the most recent integer value.
	Function of Int is current(){
		return intValue;
	}

	## Emits a new integer [value].
	Function is emit(Int is value){
		:intValue: value;
		if({ replayCount != 0 }, {
			replayBuffer:add(item: value);
			if({ replayCount > 0 && replayBuffer:length() > replayCount }, {
				replayBuffer:removeAt(index: 0);
			});
		});
		notifyCollectors(value: value as String);
	}

	replace Function is replayInto(Collector is collector){
		local Int is i: 0;
		while({ i < replayBuffer:length() }, {
			if({ collector:active }, {
				collector:onSignal(value: replayBuffer:get(index: i) as String);
			});
			i: i + 1;
		});
	}

	## Attaches a zero-argument change callback as an [IntCollector] and returns it.
	Function of IntCollector is collect(Function is onEmit){
		local IntCollector is c: IntCollector(onEmit: onEmit);
		attach(collector: c);
		return c;
	}

	## Maps this integer emitter into a derived [TextEmitter] using [prefix] and [suffix].
	Function of TextEmitter is mapText(String is prefix: '', String is suffix: ''){
		local TextEmitter is out: TextEmitter(initial: "{{prefix}}{{intValue}}{{suffix}}", replay: replayCount);
		local Boolean is first: true;
		attach(collector: IntCollector(onEmit: {
			if({ first }, {
				first: false;
				return;
			});
			out:emit(value: "{{prefix}}{{intValue}}{{suffix}}");
		}));
		return out;
	}
}
