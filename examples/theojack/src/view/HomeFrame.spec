#! Package theojack:view
#! Home screen for TheoJack: centered playing card beside the main menu.

Class of Frame is HomeFrame{
	replace [String] is namespace: ['theojack', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['base', 'sys', as Time()],
		['theojack', 'model', [Card, CardStyle]],
		['theojack', 'util', HomeStrings],
		['theojack', 'view', CardView]
	];

	FocusTarget is playFocus: FocusTarget(initial: true);
	FocusTarget is rulesFocus: FocusTarget();
	FocusTarget is optionsFocus: FocusTarget();
	FocusTarget is aboutFocus: FocusTarget();
	FocusTarget is quitFocus: FocusTarget();
	FocusTarget is aboutCloseFocus: FocusTarget();
	CardView is heroCard: CardView();
	Int is lastCardMs: 0;
	Function is onOpenRules: {};
	Function is onOpenOptions: {};
	Function is onQuit: {};
	Array of Overlay is aboutOverlays: Array();
	Array of Button is aboutButtons: Array();

	replace Function is init(
		CardStyle is initialStyle: CardStyle:WIREFRAME,
		Function is onOpenRules: {},
		Function is onOpenOptions: {},
		Function is onQuit: {}
	){
		:onOpenRules: onOpenRules;
		:onOpenOptions: onOpenOptions;
		:onQuit: onQuit;
		:heroCard: CardView(card: Card():randomCard(), style: initialStyle);
		:lastCardMs: monotonicMs();
		local Overlay is aboutOv: Overlay(
			closeOnEsc: true,
			closeOnBackdrop: false,
			content: Center(
				child: Surface(
					background: TheoColor:ansi(code: 235),
					child: Panel(
						border: true,
						padX: 2,
						padY: 1,
						topTitle: HomeStrings:ABOUT_TITLE,
						topTitleAlign: 'center',
						titleFg: TheoColor:ansi(code: 16),
						titleBg: TheoColor:ansi(code: 252),
						child: Col(
							gap: 1,
							children: Array([
								TextGraphic(graphic: HomeStrings:ABOUT_BODY),
								Row(
									children: Array([
										Spacer(weight: 1.0),
										Button(
											label: HomeStrings:ABOUT_CLOSE,
											shortcutKey: 'c',
											width: 9,
											focusTarget: aboutCloseFocus,
											onClick: { closeAbout(); }
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
	}

	Function is openAbout(){
		if({ aboutOverlays:length() > 0 && aboutButtons:length() > 0 }, {
			showOverlay(overlay: aboutOverlays:get(index: 0), anchor: aboutButtons:get(index: 0));
		});
	}

	Function is closeAbout(){
		if({ aboutOverlays:length() > 0 }, {
			closeOverlay(overlay: aboutOverlays:get(index: 0));
		});
	}

	Function of Boolean is isAboutOpen(){
		if({ aboutOverlays:length() > 0 }, {
			return aboutOverlays:get(index: 0):open;
		});
		return false;
	}

	Function is setCardStyle(CardStyle is next){
		heroCard:setStyle(next: next);
	}

	Function is randomizeCard(){
		heroCard:setCard(next: Card():randomCard());
		:lastCardMs: monotonicMs();
	}

	replace Function of Boolean is onTick(){
		if({ hasOpenOverlay() }, { return false; });
		local Int is now: monotonicMs();
		if({ now - lastCardMs >= 1000 }, {
			randomizeCard();
			return true;
		});
		return false;
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:isEsc() || (event:isChar() && event:key:toLower() == 'q') }, {
			onQuit();
			return true;
		});
		return false;
	}

	replace Function of Widget is ui(){
		local Int is w: HomeStrings:CARD_WIDTH;
		local Button is aboutBtn: Button(
			label: HomeStrings:MENU_ABOUT,
			shortcutKey: 'a',
			width: w,
			focusTarget: aboutFocus,
			onClick: { openAbout(); }
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
						titleFg: TheoColor:ansi(code: 16),
						titleBg: TheoColor:ansi(code: 252),
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
												shortcutKey: 'p',
												width: w,
												focusTarget: playFocus,
												onClick: {}
											),
											Button(
												label: HomeStrings:MENU_RULES,
												shortcutKey: 'r',
												width: w,
												focusTarget: rulesFocus,
												onClick: { onOpenRules(); }
											),
											Button(
												label: HomeStrings:MENU_OPTIONS,
												shortcutKey: 'o',
												width: w,
												focusTarget: optionsFocus,
												onClick: { onOpenOptions(); }
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
									shortcutKey: 'q',
									focusTarget: quitFocus,
									onClick: { onQuit(); }
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
