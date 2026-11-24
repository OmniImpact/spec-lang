#! Package cleopi
#! CLI entry point for CleoPi: Monte Carlo Pi benchmark with live Cleo MVVM dashboard.

Class is CleoPi{
	replace [String] is namespace: ['cleopi'];

	merge [[String]] is using: [
		['base', 'sys', 'thread', ThreadScope],
		['base', 'struct', Map],
		['cleopi', 'vm', CleoPiViewModel],
		['cleopi', 'view', CleoDashboard]
	];

	## Entry point; reads optional [args] (`threads`, `points`, `refresh`) and runs the benchmark.
	replace Function is init(Map of String to String is args){
		local CleoPiViewModel is vm: CleoPiViewModel(
			threads: args:getInt(key: 'threads', default: 4),
			points: args:getInt(key: 'points', default: 1_000_000_000),
			refreshMs: args:getInt(key: 'refresh', default: 40)
		);
		local CleoDashboard is dashboard: CleoDashboard(vm: vm);
		vm:run(
			onStart: local Function(ThreadScope is scope){ dashboard:start(scope: scope); },
			onFinish: { dashboard:finish(); }
		);
	}
}
