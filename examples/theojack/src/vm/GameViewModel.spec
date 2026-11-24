#! Package theojack:vm
#! ViewModel for the TheoJack gameplay screen: wraps [BlackjackGame] state, formatting, and round/match actions.

Class is GameViewModel{
	replace [String] is namespace: ['theojack', 'vm'];

	merge [[String]] is using: [
		['theojack', 'model', [BlackjackGame, Card, CardStyle, GamePhase]],
		['theojack', 'util', HomeStrings]
	];

	BlackjackGame is game: BlackjackGame();
	CardStyle is cardStyle: CardStyle:WIREFRAME;
	Function is onStateChanged: {};
	Function is onHome: {};

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

	Function is adjustBet(Int is delta){
		game:adjustBet(delta: delta);
		onStateChanged();
	}

	Function is deal(){
		game:deal();
		onStateChanged();
	}

	Function is hit(){
		game:hit();
		onStateChanged();
	}

	Function is stand(){
		game:stand();
		onStateChanged();
	}

	Function is doubleDown(){
		game:doubleDown();
		onStateChanged();
	}

	Function is advanceFromResult(){
		if({ game:phase == GamePhase:MATCH_OVER || game:isMatchFinished() }, {
			game:resetMatch();
		}, {
			game:nextRound();
		});
		onStateChanged();
	}

	Function is goHome(){
		onHome();
	}

	Function of Boolean is isBetting(){ game:phase == GamePhase:BETTING }

	Function of Boolean is isResultShown(){ game:phase == GamePhase:ROUND_OVER || game:phase == GamePhase:MATCH_OVER }

	Function of Boolean is shouldHideDealerHole(){ game:phase == GamePhase:PLAYER_TURN }

	Function of Boolean is canDouble(){ game:canDouble() }

	Function of String is roundText(){ "Round {{game:currentRound}} / {{game:maxRounds}}" }

	Function of String is bankrollText(){ "Bankroll: \${{game:bankroll}}" }

	Function of String is betText(){ "Bet: \${{game:currentBet}}" }

	Function of String is dealerScoreText(){
		if({ game:dealerHand:count() == 0 }, { return 'Waiting for deal...'; });
		if({ shouldHideDealerHole() }, { return 'Score: ?'; });
		return "Score: {{game:dealerHand:score()}}";
	}

	Function of String is playerScoreText(){
		if({ game:playerHand:count() == 0 }, { return 'Place your bet and deal.'; });
		return "Score: {{game:playerHand:score()}}";
	}

	Function of String is resultTitle(){
		if({ game:phase == GamePhase:MATCH_OVER }, { return ' Match Over '; });
		return game:outcomeTitle;
	}

	Function of String is resultMessage(){
		if({ game:phase == GamePhase:MATCH_OVER }, {
			return "Finished {{game:currentRound}} round(s). Final bankroll: \${{game:bankroll}}";
		});
		return game:outcomeMessage;
	}

	Function of String is resultButtonLabel(){
		if({ game:phase == GamePhase:MATCH_OVER || game:isMatchFinished() }, {
			return HomeStrings:ACTION_PLAY_AGAIN;
		});
		return HomeStrings:ACTION_NEXT_ROUND;
	}
}
