#! Package theojack
#! CLI entry point for TheoJack: a Theo TUI Blackjack game.

Class is TheoJack{
	replace [String] is namespace: ['theojack'];

	merge [[String]] is using: [
		['base', 'theo', [TheoApp, TheoScreen]],
		['base', 'struct', Map],
		['theojack', 'model', CardStyle],
		['theojack', 'util', OptionsStorage],
		['theojack', 'view', [HomeFrame, OptionsFrame, RulesFrame, GameFrame]]
	];

	replace Function is init(Map of String to String is args){
		local TheoApp is app: TheoApp();
		local OptionsStorage is storage: OptionsStorage();
		local CardStyle is initialStyle: storage:cardStyle;
		local [HomeFrame] is homes: [];
		local [TheoScreen] is screens: [];
		local HomeFrame is home: HomeFrame(
			initialStyle: initialStyle,
			onOpenPlay: {
				if({ screens:length() > 0 && homes:length() > 0 }, {
					local TheoScreen is scr: screens:get(index: 0);
					local HomeFrame is h: homes:get(index: 0);
					local GameFrame is game: GameFrame(
						startingAmount: storage:startingAmount,
						maxRounds: storage:numRounds,
						cardStyle: h:heroCard:style,
						onHome: { scr:pop(); }
					);
					scr:push(frame: game);
				});
			},
			onOpenRules: {
				if({ screens:length() > 0 && homes:length() > 0 }, {
					local TheoScreen is scr: screens:get(index: 0);
					local HomeFrame is h: homes:get(index: 0);
					local RulesFrame is rules: RulesFrame(
						cardStyle: h:heroCard:style,
						onDone: { scr:pop(); }
					);
					scr:push(frame: rules);
				});
			},
			onOpenOptions: {
				if({ screens:length() > 0 && homes:length() > 0 }, {
					local TheoScreen is scr: screens:get(index: 0);
					local HomeFrame is h: homes:get(index: 0);
					local OptionsFrame is opts: OptionsFrame(
						storage: storage,
						initialStyle: h:heroCard:style,
						initialAmount: storage:startingAmount,
						initialRounds: storage:numRounds,
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
