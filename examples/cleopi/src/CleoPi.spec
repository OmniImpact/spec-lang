#! Package cleopi
#! CLI entry point for CleoPi: Monte Carlo Pi benchmark with live Cleo MVVM dashboard.

Class is CleoPi{
	replace [String] is namespace: ['cleopi'];

	merge [[String]] is using: [
		['base', 'cli', Cli],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Process()],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'struct', Map],
		['cleopi', 'vm', CleoPiViewModel],
		['cleopi', 'view', CleoDashboard]
	];

	## Entry point; reads optional [args] (`threads`, `points`, `refresh`) and runs the benchmark.
	replace Function is init(Map of String to String is args){
		local Cli is cli: Cli():loadFromBundle(bundlePath: 'cli.json', fallbackPath: 'examples/cleopi/cli.json');
		cli:parseOrExit();
		local CleoPiViewModel is vm: CleoPiViewModel(
			threads: cli:getInt(name: 'threads', default: 4),
			points: cli:getInt(name: 'points', default: 1_000_000_000),
			refreshMs: cli:getInt(name: 'refresh', default: 40)
		);
		local CleoDashboard is dashboard: CleoDashboard(vm: vm);
		vm:run(
			onStart: local Function(ThreadScope is scope){ dashboard:start(scope: scope); },
			onFinish: { dashboard:finish(); }
		);
	}
}
