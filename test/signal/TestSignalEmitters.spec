#! specunit: suite

Class of SpecUnitTest is TestSignalEmitters{
	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', as Assert()],
		['base', 'signal', TextEmitter],
		['base', 'signal', TextCollector],
		['base', 'signal', IntEmitter],
		['base', 'signal', IntCollector],
		['base', 'signal', BoolEmitter],
		['base', 'signal', BoolCollector]
	];

	Function is testTextEmitterReplayAndEmit(){
		local TextEmitter is e: TextEmitter(initial: 'init', replay: 2);
		e:emit(value: 'one');
		e:emit(value: 'two');

		local Array of String is seen: [];
		local TextCollector is c: e:collect(onEmit: local Function(String is v){
			seen:add(item: v);
		});
		Assert:areEqualInt(2, seen:length());
		Assert:areEqualString('one', seen:get(index: 0));
		Assert:areEqualString('two', seen:get(index: 1));

		e:emit(value: 'three');
		Assert:areEqualInt(3, seen:length());
		Assert:areEqualString('three', seen:get(index: 2));

		e:detach(collector: c);
		e:emit(value: 'four');
		Assert:areEqualInt(3, seen:length());
		Assert:areEqualString('four', e:current());
	}

	Function is testIntMapAndCombineAndZip(){
		local IntEmitter is count: IntEmitter(initial: 0);
		local TextEmitter is label: count:mapText(prefix: 'Count: ');
		Assert:areEqualString('Count: 0', label:current());
		count:emit(value: 5);
		Assert:areEqualString('Count: 5', label:current());

		local TextEmitter is a: TextEmitter(initial: 'A');
		local TextEmitter is b: TextEmitter(initial: '1');
		local TextEmitter is combined: a:combineText(other: b, transform: local Function of String(String is x, String is y){
			"{{x}}-{{y}}";
		});
		Assert:areEqualString('A-1', combined:current());
		a:emit(value: 'B');
		Assert:areEqualString('B-1', combined:current());
		b:emit(value: '2');
		Assert:areEqualString('B-2', combined:current());

		local TextEmitter is z1: TextEmitter(initial: 'z0');
		local TextEmitter is z2: TextEmitter(initial: 'w0');
		local TextEmitter is zipped: z1:zipText(other: z2, combine: local Function of String(String is x, String is y){
			"{{x}}:{{y}}";
		});
		z1:emit(value: 'hello');
		Assert:areEqualString('', zipped:current());
		z2:emit(value: 'world');
		Assert:areEqualString('hello:world', zipped:current());
	}

	Function is testBoolEmitter(){
		local BoolEmitter is flag: BoolEmitter(initial: false);
		local Boolean is latest: false;
		local BoolCollector is c: flag:collect(onEmit: {
			latest: flag:current();
		});
		Assert:isFalse(latest);
		flag:emit(value: true);
		Assert:isTrue(latest);
		flag:detach(collector: c);
	}
}
