#! Package theojack:view
#! Home screen for TheoJack: pure view delegating card rotation, style, About state, and navigation to [HomeViewModel].

Class of Frame is HomeFrame{
	replace [String] is namespace: ['theojack', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theojack', 'model', Card],
		['theojack', 'util', HomeStrings],
		['theojack', 'vm', HomeViewModel],
		['theojack', 'view', CardView]
	];

	HomeViewModel is vm: HomeViewModel();
	FocusTarget is playFocus: FocusTarget(initial: true);
	FocusTarget is rulesFocus: FocusTarget();
	FocusTarget is optionsFocus: FocusTarget();
	FocusTarget is aboutFocus: FocusTarget();
	FocusTarget is quitFocus: FocusTarget();
	FocusTarget is aboutCloseFocus: FocusTarget();
	CardView is heroCard: CardView();
	Array of Overlay is aboutOverlays: Array();
	Array of Button is aboutButtons: Array();

	replace Function is init(HomeViewModel is vm: HomeViewModel()){
		:vm: vm;
		:heroCard: CardView(card: vm:heroCard, style: vm:cardStyle:current());
		vm:onCardChanged: local Function(Card is next){
			heroCard:setCard(next: next);
		};
		vm:cardStyle:collect(onEmit: {
			heroCard:setStyle(next: vm:cardStyle:current());
		});

		local Overlay is aboutOv: Overlay(
			closeOnEsc: true,
			closeOnBackdrop: false,
			onClose: { vm:closeAbout(); },
			content: Center(
				child: Surface(
					child: Panel(
						border: true,
						padX: 2,
						padY: 1,
						topTitle: HomeStrings:ABOUT_TITLE,
						topTitleAlign: 'center',
						child: Col(
							gap: 1,
							children: Array([
								TextGraphic(graphic: HomeStrings:ABOUT_BODY),
								Row(
									children: Array([
										Spacer(weight: 1.0),
										Button(
											label: HomeStrings:ABOUT_CLOSE,
											shortcut: ShortcutKey:ctrl(key: 'c'),
											width: 9,
											focusTarget: aboutCloseFocus,
											onClick: { vm:closeAbout(); }
										),
										Spacer(weight: 1.0)
									])
								)
							])
						)
					)
				)
			)
		);
		aboutOverlays: Array([aboutOv]);
		addOverlay(overlay: aboutOv);

		vm:aboutOpen:collect(onEmit: {
			if({ aboutOverlays:length() == 0 }, { return; });
			local Overlay is ov: aboutOverlays:get(index: 0);
			if({ vm:aboutOpen:current() }, {
				if({ !ov:open }, {
					local Widget is anchor: if({ aboutButtons:length() > 0 }, { aboutButtons:get(index: 0) }, { Widget() });
					showOverlay(overlay: ov, anchor: anchor);
				});
			}, {
				if({ ov:open }, {
					closeOverlay(overlay: ov);
				});
			});
		});
	}

	Function of Boolean is isAboutOpen(){
		return vm:aboutOpen:current();
	}

	replace Function of Boolean is onTick(){
		return vm:onTick();
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:isEsc() || (event:isChar() && event:key:toLower() == 'q') }, {
			vm:quit();
			return true;
		});
		return false;
	}

	replace Function of Widget is ui(){
		local Int is w: HomeStrings:CARD_WIDTH;
		local Button is aboutBtn: Button(
			label: HomeStrings:MENU_ABOUT,
			shortcut: ShortcutKey:ctrl(key: 'a'),
			width: w,
			focusTarget: aboutFocus,
			onClick: { vm:openAbout(); }
		);
		aboutButtons: Array([aboutBtn]);
		Grid(
			orientation: 'vertical',
			panes: Array([
				Grid:weight(
					weight: 1.0,
					child: Panel(
						border: true,
						padX: 2,
						padY: 1,
						topTitle: HomeStrings:HOME_TITLE,
						topTitleAlign: 'center',
						child: Center(
							child: Row(
								gap: 3,
								align: 'center',
								children: Array([
									heroCard,
									Col(
										gap: 1,
										arrowFocus: true,
										children: Array([
											Button(
												label: HomeStrings:MENU_PLAY,
												shortcut: ShortcutKey:ctrl(key: 'p'),
												width: w,
												focusTarget: playFocus,
												onClick: { vm:play(); }
											),
											Button(
												label: HomeStrings:MENU_RULES,
												shortcut: ShortcutKey:ctrl(key: 'r'),
												width: w,
												focusTarget: rulesFocus,
												onClick: { vm:openRules(); }
											),
											Button(
												label: HomeStrings:MENU_OPTIONS,
												shortcut: ShortcutKey:ctrl(key: 'o'),
												width: w,
												focusTarget: optionsFocus,
												onClick: { vm:openOptions(); }
											),
											aboutBtn
										])
									)
								])
							)
						)
					)
				),
				Grid:fixed(
					size: 3,
					child: Panel(
						border: true,
						padX: 1,
						padY: 0,
						child: Row(
							children: Array([
								Button(
									label: HomeStrings:MENU_QUIT,
									shortcut: ShortcutKey:ctrl(key: 'q'),
									focusTarget: quitFocus,
									onClick: { vm:quit(); }
								),
								Spacer(weight: 1.0)
							])
						)
					)
				)
			])
		);
	}
}
