#! Package base:signal
#! String-specialized [Emitter] convenience subclass with text combinators.

Class of Emitter is TextEmitter{
	replace [String] is namespace: ['base', 'signal'];

	replace [[String]] is using: [
		['base', 'signal', Emitter],
		['base', 'signal', Collector],
		['base', 'signal', TextCollector],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	String is textValue: '';
	Array of String is replayBuffer: Array();

	replace Function is init(String is initial: '', Int is replay: 1){
		initEmitter(replay: replay);
		:textValue: initial;
		:replayBuffer: Array();
		if({ replay != 0 }, {
			:replayBuffer:add(item: initial);
		});
	}

	## Returns the most recent string value.
	Function of String is current(){
		return textValue;
	}

	## Emits a new string [value].
	Function is emit(String is value){
		:textValue: value;
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

	## Attaches a callback directly as a [TextCollector] and returns it.
	Function of TextCollector is collect(Function is onEmit){
		local TextCollector is c: TextCollector(onEmit: onEmit);
		attach(collector: c);
		return c;
	}

	## Transforms each emitted string with [transform] into a derived [TextEmitter].
	Function of TextEmitter is mapText(Function of String is transform){
		local Function of String is fn: transform;
		local String is initVal: fn(textValue);
		local TextEmitter is out: TextEmitter(initial: initVal, replay: replayCount);
		local Boolean is first: true;
		attach(collector: TextCollector(onEmit: local Function(String is v){
			if({ first }, {
				first: false;
				return;
			});
			local String is mapped: fn(v);
			out:emit(value: mapped);
		}));
		return out;
	}

	## Combines latest values from this emitter and [other] whenever either emits.
	Function of TextEmitter is combineText(TextEmitter is other, Function of String is transform){
		local Function of String is fn: transform;
		local String is initVal: fn(textValue, other:current());
		local TextEmitter is out: TextEmitter(initial: initVal, replay: replayCount);
		local Boolean is firstA: true;
		local Boolean is firstB: true;
		attach(collector: TextCollector(onEmit: local Function(String is a){
			if({ firstA }, {
				firstA: false;
				return;
			});
			local String is res: fn(a, other:current());
			out:emit(value: res);
		}));
		other:attach(collector: TextCollector(onEmit: local Function(String is b){
			if({ firstB }, {
				firstB: false;
				return;
			});
			local String is res: fn(current(), b);
			out:emit(value: res);
		}));
		return out;
	}

	## Pairs sequential emissions from this emitter and [other] one-for-one.
	Function of TextEmitter is zipText(TextEmitter is other, Function of String is combine){
		local Function of String is fn: combine;
		local TextEmitter is out: TextEmitter(initial: '', replay: replayCount);
		local Array of String is qA: Array();
		local Array of String is qB: Array();
		local Boolean is firstA: true;
		local Boolean is firstB: true;
		attach(collector: TextCollector(onEmit: local Function(String is a){
			if({ firstA }, {
				firstA: false;
				return;
			});
			qA:add(item: a);
			if({ qB:length() > 0 }, {
				local String is av: qA:get(index: 0);
				local String is bv: qB:get(index: 0);
				qA:removeAt(index: 0);
				qB:removeAt(index: 0);
				local String is res: fn(av, bv);
				out:emit(value: res);
			});
		}));
		other:attach(collector: TextCollector(onEmit: local Function(String is b){
			if({ firstB }, {
				firstB: false;
				return;
			});
			qB:add(item: b);
			if({ qA:length() > 0 }, {
				local String is av: qA:get(index: 0);
				local String is bv: qB:get(index: 0);
				qA:removeAt(index: 0);
				qB:removeAt(index: 0);
				local String is res: fn(av, bv);
				out:emit(value: res);
			});
		}));
		return out;
	}
}
