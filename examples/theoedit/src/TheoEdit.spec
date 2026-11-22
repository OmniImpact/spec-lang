#! Package theoedit
#! CLI entry point for theoedit: parses command-line options and launches TheoApp.

Class is TheoEdit{
	namespace: ['theoedit'];

	merge Array of Array of String is using: [
		['base', 'theo', [TheoApp, TheoScreen]],
		['base', 'struct', Map],
		['base', 'sys', as Output()],
		['theoedit', 'vm', EditorViewModel],
		['theoedit', 'view', EditorFrame]
	];

	replace Function is init(Map of String to String is args){
		if({ args:has(key: 'h') || args:has(key: 'help') }, {
			printUsage();
			return;
		});
		if({ args:has(key: 'v') || args:has(key: 'version') }, {
			line(text: 'theoedit 0.1.0');
			return;
		});

		local String is filePath: args:getString(key: '0', default: '');
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
