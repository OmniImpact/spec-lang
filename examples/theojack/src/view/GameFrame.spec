#! Package theojack:view
#! Blackjack gameplay screen with Dealer (top), Player (bottom), padded action buttons, and win/lose Overlay dialogs.

Class of Frame is GameFrame{
	replace [String] is namespace: ['theojack', 'view'];

	merge [[String]] is using: [
		['base', 'theo', '*'],
		['theojack', 'model', [BlackjackGame, Card, CardStyle, GamePhase]],
		['theojack', 'util', HomeStrings],
		['theojack', 'view', CardView]
	];

	BlackjackGame is game: BlackjackGame();
	CardStyle is cardStyle: CardStyle:WIREFRAME;
	FocusTarget is primaryFocus: FocusTarget(initial: true);
	FocusTarget is secondaryFocus: FocusTarget();
	FocusTarget is doubleFocus: FocusTarget();
	FocusTarget is homeFocus: FocusTarget();
	FocusTarget is dialogActionFocus: FocusTarget(initial: true);
	FocusTarget is dialogHomeFocus: FocusTarget();
	Function is onHome: {};
	Array of Overlay is resultOverlays: Array();

	replace Function is init(
		Int is startingAmount: 500,
		Int is maxRounds: 10,
		CardStyle is cardStyle: CardStyle:WIREFRAME,
		Function is onHome: {}
	){
		:game: BlackjackGame(startingAmount: startingAmount, maxRounds: maxRounds);
		:cardStyle: cardStyle;
		:onHome: onHome;
	}

	local Function is syncResultOverlay(){
		if({ game:phase == GamePhase:ROUND_OVER || game:phase == GamePhase:MATCH_OVER }, {
			local String is title: if({ game:phase == GamePhase:MATCH_OVER }, { ' Match Over ' }, { game:outcomeTitle });
			local String is msg: if({ game:phase == GamePhase:MATCH_OVER }, {
				"Finished " . (game:currentRound as String) . " round(s). Final bankroll: $" . (game:bankroll as String)
			}, {
				game:outcomeMessage
			});
			local String is btnLabel: if({ game:phase == GamePhase:MATCH_OVER || game:isMatchFinished() }, {
				HomeStrings:ACTION_PLAY_AGAIN
			}, {
				HomeStrings:ACTION_NEXT_ROUND
			});

			local Overlay is ov: Overlay(
				closeOnEsc: false,
				closeOnBackdrop: false,
				content: Center(
					child: Surface(
						background: TheoColor:ansi(code: 235),
						child: Panel(
							border: true,
							padX: 2,
							padY: 1,
							topTitle: title,
							topTitleAlign: 'center',
							titleFg: TheoColor:ansi(code: 16),
							titleBg: TheoColor:ansi(code: 252),
							child: Col(
								gap: 1,
								children: Array([
									TextLine(value: msg),
									Row(
										gap: 2,
										arrowFocus: true,
										children: Array([
											Spacer(weight: 1.0),
											Button(
												label: btnLabel,
												focusTarget: dialogActionFocus,
												onClick: {
													if({ game:phase == GamePhase:MATCH_OVER || game:isMatchFinished() }, {
														game:resetMatch();
													}, {
														game:nextRound();
													});
													:resultOverlays: Array();
													:overlays: Array();
													rebuild();
												}
											),
											Button(
												label: HomeStrings:ACTION_HOME,
												focusTarget: dialogHomeFocus,
												onClick: { onHome(); }
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
			:resultOverlays: Array([ov]);
			:overlays: Array();
			showOverlay(overlay: ov);
			return;
		});
		:resultOverlays: Array();
		:overlays: Array();
	}

	Function is doDeal(){
		game:deal();
		rebuild();
		syncResultOverlay();
	}

	Function is doHit(){
		game:hit();
		rebuild();
		syncResultOverlay();
	}

	Function is doStand(){
		game:stand();
		rebuild();
		syncResultOverlay();
	}

	Function is doDouble(){
		game:doubleDown();
		rebuild();
		syncResultOverlay();
	}

	local Function of Array of Widget is buildDealerCards(){
		local Array of Widget is out: Array();
		local Boolean is hideHole: game:phase == GamePhase:PLAYER_TURN;
		local Int is i: 0;
		while({ i < game:dealerHand:count() }, {
			local Boolean is down: hideHole && i == 1;
			out:add(item: CardView(
				card: game:dealerHand:cards:get(index: i),
				style: cardStyle,
				faceDown: down
			));
			i: i + 1;
		});
		return out;
	}

	local Function of Array of Widget is buildPlayerCards(){
		local Array of Widget is out: Array();
		local Int is i: 0;
		while({ i < game:playerHand:count() }, {
			out:add(item: CardView(
				card: game:playerHand:cards:get(index: i),
				style: cardStyle
			));
			i: i + 1;
		});
		return out;
	}

	local Function of Array of Widget is buildActionButtons(){
		local Array of Widget is btns: Array();
		if({ game:phase == GamePhase:BETTING }, {
			btns:add(item: Tooltip(
				host: :,
				text: 'Decrease bet by $10',
				side: 'top',
				child: Button(
					label: HomeStrings:ACTION_BET_DOWN,
					padX: 2,
					padY: 1,
					focusTarget: secondaryFocus,
					onClick: {
						game:adjustBet(delta: -10);
						rebuild();
					}
				)
			));
			btns:add(item: Tooltip(
				host: :,
				text: 'Increase bet by $10',
				side: 'top',
				child: Button(
					label: HomeStrings:ACTION_BET_UP,
					padX: 2,
					padY: 1,
					focusTarget: doubleFocus,
					onClick: {
						game:adjustBet(delta: 10);
						rebuild();
					}
				)
			));
			btns:add(item: Tooltip(
				host: :,
				text: 'Deal a new hand',
				side: 'top',
				child: Button(
					label: HomeStrings:ACTION_DEAL,
					shortcutKey: 'd',
					padX: 2,
					padY: 1,
					focusTarget: primaryFocus,
					onClick: { doDeal(); }
				)
			));
		}, {
			btns:add(item: Button(
				label: HomeStrings:ACTION_HIT,
				shortcutKey: 'h',
				padX: 2,
				padY: 1,
				focusTarget: primaryFocus,
				onClick: { doHit(); }
			));
			btns:add(item: Button(
				label: HomeStrings:ACTION_STAND,
				shortcutKey: 's',
				padX: 2,
				padY: 1,
				focusTarget: secondaryFocus,
				onClick: { doStand(); }
			));
			if({ game:canDouble() }, {
				btns:add(item: Button(
					label: HomeStrings:ACTION_DOUBLE,
					shortcutKey: 'b',
					padX: 2,
					padY: 1,
					focusTarget: doubleFocus,
					onClick: { doDouble(); }
				));
			});
		});
		btns:add(item: Spacer(weight: 1.0));
		btns:add(item: Button(
			label: HomeStrings:ACTION_HOME,
			shortcutKey: 'q',
			padX: 2,
			padY: 1,
			focusTarget: homeFocus,
			onClick: { onHome(); }
		));
		return btns;
	}

	replace Function of Boolean is onKey(KeyEvent is event){
		if({ event:isEsc() }, {
			onHome();
			return true;
		});
		return false;
	}

	replace Function of Widget is ui(){
		local String is roundStr: "Round " . (game:currentRound as String) . " / " . (game:maxRounds as String);
		local String is bankStr: "Bankroll: $" . (game:bankroll as String);
		local String is betStr: "Bet: $" . (game:currentBet as String);

		local String is dealerScoreStr: if({ game:dealerHand:count() == 0 }, {
			'Waiting for deal...'
		}, {
			if({ game:phase == GamePhase:PLAYER_TURN }, {
				'Score: ?'
			}, {
				"Score: " . (game:dealerHand:score() as String)
			})
		});
		local String is playerScoreStr: if({ game:playerHand:count() == 0 }, {
			'Place your bet and deal.'
		}, {
			"Score: " . (game:playerHand:score() as String)
		});

		Grid(
			orientation: 'vertical',
			panes: Array([
				Grid:fixed(
					size: 3,
					child: Panel(
						border: true,
						padX: 1,
						padY: 0,
						child: Row(
							children: Array([
								TextLine(value: roundStr, bold: true),
								Spacer(weight: 1.0),
								TextLine(value: bankStr, color: TheoColor:ansi(code: 220), bold: true),
								Spacer(weight: 1.0),
								TextLine(value: betStr, bold: true)
							])
						)
					)
				),
				Grid:weight(
					weight: 1.0,
					child: Panel(
						border: true,
						padX: 2,
						padY: 1,
						rightTitle: HomeStrings:DEALER_TITLE,
						rightTitleAlign: 'center',
						titleFg: TheoColor:ansi(code: 16),
						titleBg: TheoColor:ansi(code: 252),
						child: Row(
							align: 'center',
							children: Array([
								Row(gap: 2, children: buildDealerCards()),
								Spacer(weight: 1.0),
								TextLine(value: dealerScoreStr, color: activeTheme:mutedColor)
							])
						)
					)
				),
				Grid:weight(
					weight: 1.0,
					child: Panel(
						border: true,
						padX: 2,
						padY: 1,
						leftTitle: HomeStrings:PLAYER_TITLE,
						leftTitleAlign: 'center',
						titleFg: TheoColor:ansi(code: 16),
						titleBg: TheoColor:ansi(code: 252),
						child: Row(
							align: 'center',
							children: Array([
								Row(gap: 2, children: buildPlayerCards()),
								Spacer(weight: 1.0),
								TextLine(value: playerScoreStr, color: activeTheme:mutedColor)
							])
						)
					)
				),
				Grid:fixed(
					size: 5,
					child: Panel(
						border: true,
						padX: 1,
						padY: 0,
						child: Row(
							gap: 2,
							arrowFocus: true,
							children: buildActionButtons()
						)
					)
				)
			])
		);
	}
}
