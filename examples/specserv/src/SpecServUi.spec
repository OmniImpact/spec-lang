#! Package specserv
#! Theo TUI application (`specservui`) to configure `specserv` JSON files and start/stop `specserv`.

Class is SpecServUi{
	replace [String] is namespace: ['specserv'];

	merge [[String]] is using: [
		['base', 'cli', Cli],
		['base', 'core', SpecError],
		['base', 'theo', [TheoApp, TheoScreen, TheoTheme]],
		['base', 'struct', Map],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', [as Conditional(), as Process()]],
		['specserv', 'vm', SpecServViewModel],
		['specserv', 'view', SpecServFrame]
	];

	replace Function is init(Map of String to String is args){
		local Cli is cli: Cli():parseOrExit();
		local String is cfgPath: cli:getString(name: 'config', default: 'specserv.json');
		local String is logFilePath: cli:getString(name: 'log-file', default: '');

		ThreadScope:open(
			onError: local Function of Boolean(SpecError is _err){ true },
			body: local Function(ThreadScope is _scope){
				local TheoApp is app: TheoApp(theme: TheoTheme());
				local SpecServViewModel is vm: SpecServViewModel(
					allowThreads: true,
					configPath: cfgPath,
					onQuit: { app:quit(); }
				);
				vm:logFilePath: logFilePath;
				local SpecServFrame is frame: SpecServFrame(vm: vm);
				local TheoScreen is screen: TheoScreen(root: frame);
				app:run(screen: screen);
				if({ !vm:attachedExternal }, {
					vm:stopServers();
				});
			}
		);
	}
}
