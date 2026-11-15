Class is Blackjack{

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'iterator', Loop],
		['base', 'iterator', LoopControl],
		['base', 'iterator', LoopCallback],
		['base', 'sys', InputHandler],
		['base', 'sys', as Input()],
		['base', 'sys', as Output()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()],
		[Deck]
	];

	local Deck is deckUtil: Deck:init();
	local Array of Int is deck: [];
	local Array of Int is playerHand: [];
	local Array of Int is dealerHand: [];
	local Boolean is roundActive: true;

	Class of Loop is DealerTurnLoop{

		replace Array of Array of String is using: [
			['base', 'sys', as Output()]
		];
		local Blackjack is game;

		replace Function is init(Blackjack is game){
			self:game: game;
		}

		replace Function of Boolean is evaluate(){
			local Int is currentScore: game:handValue(hand: game:dealerHand);
			return currentScore < 17;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local Int is card: game:drawCard();
			game:dealerHand:add(item: card);
			local Int is newScore: game:handValue(hand: game:dealerHand);
			line('Dealer draws: ' . card . ' (Total: ' . newScore . ')');
			return true;
		}

	}

	Class of LoopCallback is DealerTurnCompleteCallback{

		replace Array of Array of String is using: [
			['base', 'sys', as Output()]
		];
		local Blackjack is game;

		replace Function is init(Blackjack is game){
			self:game: game;
		}

		replace Function is onComplete(LoopControl is control){
			line("\nDealer stands or busts.");
			game:evaluateRoundOutcome();
		}

	}

	Class of InputHandler is PlayerTurnHandler{

		replace Array of Array of String is using: [
			['base', 'sys', as Output()],
			['base', 'sys', as Conditional()]
		];
		local Blackjack is game;

		replace Function is init(Blackjack is game){
			self:game: game;
		}

		replace Function is onInput(String is action){
			if({ action == '' }, {
				line("\nInput closed. Thanks for playing!");
				game:roundActive: false;
				return;
			});
			match(on: action, when: [
				['h', 'hit']: {
					local Int is card: game:drawCard();
					game:playerHand:add(item: card);
					line('You drew: ' . card);

					local Int is score: game:handValue(hand: game:playerHand);
					line('Your total is now: ' . score);

					match(when: [
						{ score > 21 }: {
							line('Bust! You lose.');
							game:roundActive: false;
						},
						{ score == 21 }: {
							line('21! Standing automatically.');
							game:startDealerTurn();
						},
						else: {
							game:promptPlayerAction();
						}
					]);
				},
				['s', 'stand']: {
					line('You stand with total: ' . game:handValue(hand: game:playerHand));
					game:startDealerTurn();
				},
				else: {
					line('Invalid command. Please enter \'h\' (hit) or \'s\' (stand).');
					game:promptPlayerAction();
				}
			]);
		}

	}

	Function of Int is drawCard(){
		return self:deckUtil:drawCard();
	}

	Function of Int is handValue(Array of Int is hand){
		return self:deckUtil:handValue(hand: hand);
	}

	Function is promptPlayerAction(){
		line('Would you like to (h)it or (s)tand?');
		local PlayerTurnHandler is handler: PlayerTurnHandler:init(game: self);
		consIn(handler: handler);
	}

	Function is startDealerTurn(){
		line("\n--- Starting Dealer's Turn ---");
		local DealerTurnLoop is dealerLoop: DealerTurnLoop:init(game: self);
		local DealerTurnCompleteCallback is onComplete: DealerTurnCompleteCallback:init(game: self);
		local LoopControl is control: LoopControl:init(onComplete: onComplete);
		run(loop: dealerLoop, control: control);
	}

	Function is evaluateRoundOutcome(){
		local Int is playerScore: handValue(hand: playerHand);
		local Int is dealerScore: handValue(hand: dealerHand);

		line("\n=== Final Results ===");
		line('Player: ' . playerScore . ' | Dealer: ' . dealerScore);

		match(when: [
			{ dealerScore > 21 }:          { line('Dealer busts! You win!'); },
			{ playerScore > dealerScore }: { line('You beat the dealer! You win!'); },
			{ dealerScore > playerScore }: { line('Dealer wins!'); },
			else:                          { line('Push (Tie)!'); }
		]);
	}

	replace Function is init(Map of String to String is args){
		line('======================================');
		line('         Welcome to SpecJack          ');
		line("======================================\n");

		self:deck: self:deckUtil:createDeck();

		playerHand:add(item: drawCard());
		playerHand:add(item: drawCard());
		dealerHand:add(item: drawCard());
		dealerHand:add(item: drawCard());

		line('Your hand: ' . playerHand[0] . ', ' . playerHand[1] . ' (Total: ' . handValue(hand: playerHand) . ')');
		line('Dealer\'s up card: ' . dealerHand[0] . " [Hidden Card]\n");

		if({ handValue(hand: playerHand) == 21 }, {
			line('Natural Blackjack! You win!');
			return;
		});

		promptPlayerAction();
	}

}
