#! Package theojack:model
#! Blackjack game state machine (betting, dealing, hit/stand/double, payouts, and multi-round match).

Class is BlackjackGame{
	replace [String] is namespace: ['theojack', 'model'];

	merge [[String]] is using: [
		['theojack', 'model', [Card, Deck, GamePhase, Hand]]
	];

	Deck is deck: Deck();
	Hand is dealerHand: Hand();
	Hand is playerHand: Hand();
	Int is startingAmount: 500;
	Int is bankroll: 500;
	Int is maxRounds: 10;
	Int is currentRound: 1;
	Int is currentBet: 10;
	GamePhase is phase: GamePhase:BETTING;
	String is outcomeTitle: '';
	String is outcomeMessage: '';

	replace Function is init(Int is startingAmount: 500, Int is maxRounds: 10){
		:startingAmount: startingAmount;
		:maxRounds: maxRounds;
		resetMatch();
	}

	Function is resetMatch(){
		deck:shuffle();
		dealerHand:clear();
		playerHand:clear();
		:bankroll: startingAmount;
		:currentRound: 1;
		:currentBet: if({ bankroll >= 10 }, { 10 }, { bankroll });
		:phase: GamePhase:BETTING;
		:outcomeTitle: '';
		:outcomeMessage: '';
	}

	Function is adjustBet(Int is delta){
		if({ phase != GamePhase:BETTING }, { return; });
		local Int is next: currentBet + delta;
		if({ next < 10 && bankroll >= 10 }, { next: 10; });
		if({ next < 1 }, { next: 1; });
		if({ next > bankroll }, { next: bankroll; });
		:currentBet: next;
	}

	Function of Boolean is canDouble(){ phase == GamePhase:PLAYER_TURN && playerHand:count() == 2 && bankroll >= currentBet; }

	Function is deal(){
		if({ phase != GamePhase:BETTING || bankroll <= 0 }, { return; });
		if({ currentBet > bankroll }, { :currentBet: bankroll; });
		if({ currentBet <= 0 }, { return; });
		:bankroll: bankroll - currentBet;
		dealerHand:clear();
		playerHand:clear();
		playerHand:add(card: deck:draw());
		dealerHand:add(card: deck:draw());
		playerHand:add(card: deck:draw());
		dealerHand:add(card: deck:draw());

		if({ playerHand:isBlackjack() || dealerHand:isBlackjack() }, {
			resolveImmediateBlackjack();
			return;
		});
		:phase: GamePhase:PLAYER_TURN;
	}

	local Function is resolveImmediateBlackjack(){
		:phase: GamePhase:ROUND_OVER;
		local Boolean is pBj: playerHand:isBlackjack();
		local Boolean is dBj: dealerHand:isBlackjack();
		if({ pBj && dBj }, {
			:bankroll: bankroll + currentBet;
			:outcomeTitle: ' Push ';
			:outcomeMessage: "Both have Blackjack! Bet returned. Bankroll: $" . (bankroll as String);
			return;
		});
		if({ pBj }, {
			local Int is winAmt: currentBet + (currentBet * 3) / 2;
			:bankroll: bankroll + winAmt;
			:outcomeTitle: ' Blackjack! ';
			:outcomeMessage: "Natural 21! You win 3:2 ($" . (((currentBet * 3) / 2) as String) . "). Bankroll: $" . (bankroll as String);
			return;
		});
		:outcomeTitle: ' Dealer Blackjack ';
		:outcomeMessage: "Dealer has Blackjack. You lose $" . (currentBet as String) . ". Bankroll: $" . (bankroll as String);
	}

	Function is hit(){
		if({ phase != GamePhase:PLAYER_TURN }, { return; });
		playerHand:add(card: deck:draw());
		if({ playerHand:isBust() }, {
			:phase: GamePhase:ROUND_OVER;
			:outcomeTitle: ' Bust! ';
			:outcomeMessage: "You busted with " . (playerHand:score() as String) . ". Lost $" . (currentBet as String) . ". Bankroll: $" . (bankroll as String);
		});
	}

	Function is stand(){
		if({ phase != GamePhase:PLAYER_TURN }, { return; });
		while({ dealerHand:score() < 17 }, {
			dealerHand:add(card: deck:draw());
		});
		:phase: GamePhase:ROUND_OVER;
		local Int is pScore: playerHand:score();
		local Int is dScore: dealerHand:score();
		if({ dealerHand:isBust() }, {
			:bankroll: bankroll + (currentBet * 2);
			:outcomeTitle: ' You Win! ';
			:outcomeMessage: "Dealer busted (" . (dScore as String) . ")! You win $" . (currentBet as String) . ". Bankroll: $" . (bankroll as String);
			return;
		});
		if({ pScore > dScore }, {
			:bankroll: bankroll + (currentBet * 2);
			:outcomeTitle: ' You Win! ';
			:outcomeMessage: (pScore as String) . " beats dealer's " . (dScore as String) . "! Won $" . (currentBet as String) . ". Bankroll: $" . (bankroll as String);
			return;
		});
		if({ pScore == dScore }, {
			:bankroll: bankroll + currentBet;
			:outcomeTitle: ' Push ';
			:outcomeMessage: "Tied at " . (pScore as String) . ". Bet returned. Bankroll: $" . (bankroll as String);
			return;
		});
		:outcomeTitle: ' You Lose ';
		:outcomeMessage: "Dealer's " . (dScore as String) . " beats your " . (pScore as String) . ". Lost $" . (currentBet as String) . ". Bankroll: $" . (bankroll as String);
	}

	Function is doubleDown(){
		if({ !canDouble() }, { return; });
		:bankroll: bankroll - currentBet;
		:currentBet: currentBet * 2;
		playerHand:add(card: deck:draw());
		if({ playerHand:isBust() }, {
			:phase: GamePhase:ROUND_OVER;
			:outcomeTitle: ' Bust! ';
			:outcomeMessage: "Doubled and busted with " . (playerHand:score() as String) . ". Lost $" . (currentBet as String) . ". Bankroll: $" . (bankroll as String);
			return;
		});
		stand();
	}

	Function of Boolean is isMatchFinished(){ currentRound >= maxRounds || bankroll <= 0; }

	Function is nextRound(){
		if({ isMatchFinished() }, {
			:phase: GamePhase:MATCH_OVER;
			return;
		});
		:currentRound: currentRound + 1;
		dealerHand:clear();
		playerHand:clear();
		if({ currentBet > bankroll }, { :currentBet: bankroll; });
		if({ currentBet <= 0 && bankroll > 0 }, { :currentBet: if({ bankroll >= 10 }, { 10 }, { bankroll }); });
		:phase: GamePhase:BETTING;
		:outcomeTitle: '';
		:outcomeMessage: '';
	}
}
