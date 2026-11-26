#! Package theojack
#! CLI entry point for TheoJack: a Theo TUI Blackjack game.

Class is TheoJack{
	replace [String] is namespace: ['theojack'];

	merge [[String]] is using: [
		['base', 'cli', Cli],
		['base', 'theo', [TheoApp, TheoScreen]],
		['base', 'struct', Map],
		['base', 'sys', [as Conditional(), as Process()]],
		['theojack', 'model', CardStyle],
		['theojack', 'util', OptionsStorage],
		['theojack', 'vm', [GameViewModel, HomeViewModel, OptionsViewModel, RulesViewModel]],
		['theojack', 'view', [HomeFrame, OptionsFrame, RulesFrame, GameFrame]]
	];

	replace Function is init(Map of String to String is args){
		local Cli is cli: Cli():loadFromBundle(bundlePath: 'cli.json', fallbackPath: 'examples/theojack/cli.json');
		cli:parseOrExit();
		local TheoApp is app: TheoApp();
		local OptionsStorage is storage: OptionsStorage();
		local [HomeViewModel] is homeVms: [];
		local [TheoScreen] is screens: [];
		local HomeViewModel is homeVm: HomeViewModel(
			initialStyle: storage:cardStyle,
			onOpenPlay: {
				if({ screens:length() > 0 && homeVms:length() > 0 }, {
					local TheoScreen is scr: screens:get(index: 0);
					local HomeViewModel is hvm: homeVms:get(index: 0);
					local GameViewModel is gvm: GameViewModel(
						startingAmount: storage:startingAmount,
						maxRounds: storage:numRounds,
						cardStyle: hvm:cardStyle:current(),
						onHome: { scr:pop(); }
					);
					scr:push(frame: GameFrame(vm: gvm));
				});
			},
			onOpenRules: {
				if({ screens:length() > 0 && homeVms:length() > 0 }, {
					local TheoScreen is scr: screens:get(index: 0);
					local HomeViewModel is hvm: homeVms:get(index: 0);
					local RulesViewModel is rvm: RulesViewModel(
						cardStyle: hvm:cardStyle:current(),
						onDone: { scr:pop(); }
					);
					scr:push(frame: RulesFrame(vm: rvm));
				});
			},
			onOpenOptions: {
				if({ screens:length() > 0 && homeVms:length() > 0 }, {
					local TheoScreen is scr: screens:get(index: 0);
					local HomeViewModel is hvm: homeVms:get(index: 0);
					local OptionsViewModel is ovm: OptionsViewModel(
						storage: storage,
						initialStyle: hvm:cardStyle:current(),
						initialAmount: storage:startingAmount,
						initialRounds: storage:numRounds,
						onCancel: { scr:pop(); },
						onSave: local Function(CardStyle is saved){
							hvm:setCardStyle(next: saved);
							scr:pop();
						}
					);
					scr:push(frame: OptionsFrame(vm: ovm));
				});
			},
			onQuit: { app:quit(); }
		);
		homeVms:push(item: homeVm);
		local HomeFrame is home: HomeFrame(vm: homeVm);
		local TheoScreen is screen: TheoScreen(root: home);
		screens:push(item: screen);
		app:run(screen: screen);
	}
}
