#! Package theojack
#! CLI entry point for TheoJack: a Theo TUI Blackjack game.

Class is TheoJack{
	replace [String] is namespace: ['theojack'];

	merge [[String]] is using: [
		['base', 'theo', [TheoApp, TheoScreen]],
		['base', 'struct', Map],
		['theojack', 'model', CardStyle],
		['theojack', 'util', OptionsStorage],
		['theojack', 'view', [HomeFrame, OptionsFrame]]
	];

	replace Function is init(Map of String to String is args){
		local TheoApp is app: TheoApp();
		local OptionsStorage is storage: OptionsStorage();
		local CardStyle is initialStyle: storage:loadCardStyle();
		local [HomeFrame] is homes: [];
		local [TheoScreen] is screens: [];
		local HomeFrame is home: HomeFrame(
			initialStyle: initialStyle,
			onOpenOptions: {
				if({ screens:length() > 0 && homes:length() > 0 }, {
					local TheoScreen is scr: screens:get(index: 0);
					local HomeFrame is h: homes:get(index: 0);
					local OptionsFrame is opts: OptionsFrame(
						storage: storage,
						initialStyle: h:heroCard:style,
						onCancel: { scr:pop(); },
						onSave: local Function(CardStyle is saved){
							h:setCardStyle(next: saved);
							scr:pop();
						}
					);
					scr:push(frame: opts);
				});
			},
			onQuit: { app:quit(); }
		);
		homes:push(item: home);
		local TheoScreen is screen: TheoScreen(root: home);
		screens:push(item: screen);
		app:run(screen: screen);
	}
}
