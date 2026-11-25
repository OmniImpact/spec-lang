#! Package suitdemo
#! Minimal Suit demo opening a native Wayland window titled "Suit Demo".

Class is SuitDemo{
	replace [String] is namespace: ['suitdemo'];

	merge [[String]] is using: [
		['base', 'suit', SuitWindow],
		['base', 'struct', Map],
		['base', 'sys', [as Output(), as Time()]],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	replace Function is init(Map of String to String is args){
		local Int is durationMs: args:getString(key: 'duration-ms', default: '0'):parseInt(default: 0);
		local SuitWindow is win: SuitWindow(title: 'Suit Demo', width: 800, height: 600, decorated: true);
		if({ !win:open() }, {
			line(text: 'SuitDemo failed to open window: ' . win:lastError());
			return;
		});

		local Int is startMs: monotonicMs();
		while({ win:poll() }, {
			if({ durationMs > 0 && (monotonicMs() - startMs) >= durationMs }, {
				win:close();
			});
		});
	}
}
