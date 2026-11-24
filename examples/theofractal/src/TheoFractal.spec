#! Package theofractal
#! CLI entry point for TheoFractal: an interactive terminal fractal explorer built with Theo.

Class is TheoFractal{
	replace [String] is namespace: ['theofractal'];

	replace [[String]] is using: [
		['base', 'theo', [TheoApp, TheoScreen, TheoTheme]],
		['base', 'struct', Map],
		['theofractal', 'vm', ExplorerViewModel],
		['theofractal', 'view', ExplorerFrame]
	];

	replace Function is init(Map of String to String is args){
		local TheoApp is app: TheoApp(theme: TheoTheme());
		local ExplorerViewModel is vm: ExplorerViewModel();
		local ExplorerFrame is mainFrame: ExplorerFrame(app: app, vm: vm);
		local TheoScreen is screen: TheoScreen(root: mainFrame);
		app:run(screen: screen);
	}
}
