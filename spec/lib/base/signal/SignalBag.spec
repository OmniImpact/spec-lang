#! Package base:signal
#! Keyed subscription registry that auto-detaches replaced slots and cleans up on clear.

Class is SignalBag{
	replace [String] is namespace: ['base', 'signal'];

	replace [[String]] is using: [
		['base', 'signal', [Emitter, Collector]],
		['base', 'sys', as Conditional()]
	];

	[String] is slots: [];
	[Emitter] is emitters: [];
	[Collector] is collectors: [];

	## Registers [collector] on [emitter] under [slot], detaching any prior binding for [slot].
	Function is track(String is slot, Emitter is emitter, Collector is collector){
		local Int is i: 0;
		while({ i < slots:length() }, {
			if({ slots:get(index: i) == slot }, {
				emitters:get(index: i):detach(collector: collectors:get(index: i));
				emitters:set(index: i, item: emitter);
				collectors:set(index: i, item: collector);
				return;
			});
			i: i + 1;
		});
		slots:push(item: slot);
		emitters:push(item: emitter);
		collectors:push(item: collector);
	}

	## Detaches all tracked collectors and empties the bag.
	Function is clear(){
		local Int is i: 0;
		while({ i < slots:length() }, {
			emitters:get(index: i):detach(collector: collectors:get(index: i));
			i: i + 1;
		});
		:slots: [];
		:emitters: [];
		:collectors: [];
	}

	## Number of active tracked bindings.
	Function of Int is count(){
		return slots:length();
	}
}
