#! Package theoedit
#! CLI entry point for theoedit: parses command-line options and launches TheoApp.

Class is TheoEdit{
	replace [String] is namespace: ['theoedit'];

	merge [[String]] is using: [
		['base', 'cli', Cli],
		['base', 'theo', [TheoApp, TheoScreen]],
		['base', 'struct', Map],
		['base', 'sys', [as Output(), as Process()]],
		['base', 'sys', as Conditional()],
		['theoedit', 'vm', EditorViewModel],
		['theoedit', 'view', EditorFrame]
	];

	replace Function is init(Map of String to String is args){
		local Cli is cli: Cli():loadFromBundle(bundlePath: 'cli.json', fallbackPath: 'examples/theoedit/cli.json');
		if({ !cli:parse(rawArgs: rawArgs()) }, {
			if({ cli:helpRequested || cli:versionRequested }, { return; });
			exit(status: 1);
		});

		local String is filePath: cli:positionals():get(index: 0, default: '');
		local TheoApp is app: TheoApp();
		local EditorViewModel is vm: EditorViewModel(filePath: filePath);
		local EditorFrame is rootFrame: EditorFrame(
			vm: vm,
			onQuit: { app:quit(); }
		);
		local TheoScreen is screen: TheoScreen(root: rootFrame);
		rootFrame:bindScreen(screen: screen);
		app:run(screen: screen);
	}

	local Function is printUsage(){
		line(text: 'theoedit — Theo TUI text editor');
		line(text: 'Usage: theoedit [options] [file]');
		line(text: '  -h, --help     Show this help message');
		line(text: '  -v, --version  Show version information');
	}
}
