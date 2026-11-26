#! Package theofractal
#! CLI entry point for TheoFractal: an interactive terminal fractal explorer built with Theo.

Class is TheoFractal{
	replace [String] is namespace: ['theofractal'];

	merge [[String]] is using: [
		['base', 'cli', Cli],
		['base', 'theo', [TheoApp, TheoScreen, TheoTheme]],
		['base', 'struct', Map],
		['base', 'sys', [as Conditional(), as Process()]],
		['theofractal', 'vm', ExplorerViewModel],
		['theofractal', 'view', ExplorerFrame]
	];

	replace Function is init(Map of String to String is args){
		local Cli is cli: Cli():loadFromBundle(bundlePath: 'cli.json', fallbackPath: 'examples/theofractal/cli.json');
		cli:parseOrExit();
		local TheoApp is app: TheoApp(theme: TheoTheme());
		local ExplorerViewModel is vm: ExplorerViewModel(onQuit: { app:quit(); });
		local ExplorerFrame is mainFrame: ExplorerFrame(vm: vm);
		local TheoScreen is screen: TheoScreen(root: mainFrame);
		app:run(screen: screen);
	}
}
