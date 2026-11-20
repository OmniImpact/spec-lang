#! Package base:signal
#! Boolean-specialized [Collector] convenience subclass.

Class of Collector is BoolCollector{
	namespace: ['base', 'signal'];

	replace Array of Array of String is using: [
		['base', 'signal', Collector],
		['base', 'sys', as Conditional()]
	];

	Function is cb;

	replace Function is init(Function is onEmit){
		:active: true;
		:cb: onEmit;
	}

	replace Function is onSignal(Any is _value){
		if({ active }, {
			local Function is f: cb;
			f();
		});
	}
}
