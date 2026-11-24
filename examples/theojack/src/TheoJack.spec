#! Package theojack
#! CLI entry point for TheoJack: a Theo TUI Blackjack game.

Class is TheoJack{
	replace [String] is namespace: ['theojack'];

	merge [[String]] is using: [
		['base', 'theo', [TheoApp, TheoScreen]],
		['base', 'struct', Map],
		['theojack', 'view', HomeFrame]
	];

	replace Function is init(Map of String to String is args){
		local TheoApp is app: TheoApp();
		local HomeFrame is home: HomeFrame(onQuit: { app:quit(); });
		local TheoScreen is screen: TheoScreen(root: home);
		app:run(screen: screen);
	}
}
