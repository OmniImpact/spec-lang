#! Package specserv
#! Entry point for SpecServ: Theo TUI web server manager and headless `--serve` runner.

Class is SpecServ{
	replace [String] is namespace: ['specserv'];

	merge [[String]] is using: [
		['base', 'core', SpecError],
		['base', 'theo', [TheoApp, TheoScreen, TheoTheme]],
		['base', 'struct', Map],
		['base', 'sys', [as Output(), as Process()]],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', as Conditional()],
		['specserv', 'vm', SpecServViewModel],
		['specserv', 'view', SpecServFrame]
	];

	replace Function is init(Map of String to String is args){
		local String is cfgPath: args:getString(key: 'config', default: 'specserv.json');
		local Boolean is headless: args:has(key: 'serve') || args:has(key: 'headless');

		ThreadScope:open(
			onError: local Function of Boolean(SpecError is _err){ true },
			body: local Function(ThreadScope is _scope){
				if({ headless }, {
					local SpecServViewModel is vm: SpecServViewModel(allowThreads: true, configPath: cfgPath);
					vm:startServers();
					if({ !vm:serversRunning }, {
						line(text: 'SpecServ: no enabled sites to serve.');
						return;
					});
					line(text: 'SpecServ running (' . vm:statusMessage . '). Press Ctrl-C to stop.');
					while({ vm:serversRunning }, {
						sleep(milliseconds: 200);
					});
				}, {
					local TheoApp is app: TheoApp(theme: TheoTheme());
					local SpecServViewModel is vm: SpecServViewModel(
						allowThreads: true,
						configPath: cfgPath,
						onQuit: { app:quit(); }
					);
					local SpecServFrame is frame: SpecServFrame(vm: vm);
					local TheoScreen is screen: TheoScreen(root: frame);
					app:run(screen: screen);
					vm:stopServers();
				});
			}
		);
	}
}
