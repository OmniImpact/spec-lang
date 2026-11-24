#! Interactive console Blackjack game ("SpecJack").

## Interactive Blackjack game coordinating player input, dealer loop, and outcome scoring.
Class is Blackjack{

	replace [[String]] is using: [
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

	local Deck is deckUtil: Deck();
	local Array of Int is deck: Array();
	local Array of Int is playerHand: Array();
	local Array of Int is dealerHand: Array();
	local Boolean is roundActive: true;

	## Loop driving the dealer's hit-until-17 turn.
	Class of Loop is DealerTurnLoop{

		replace [[String]] is using: [
			['base', 'sys', as Output()]
		];
		local Blackjack is game;

		replace Function is init(Blackjack is game){
			:game: game;
		}

		replace Function of Boolean is evaluate(){
			local Int is currentScore: game:handValue(hand: game:dealerHand);
			return currentScore < 17;
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local Int is card: game:drawCard();
			game:dealerHand:add(item: card);
			local Int is newScore: game:handValue(hand: game:dealerHand);
			line("Dealer draws: {{card}} (Total: {{newScore}})");
			return true;
		}

	}

	## Callback invoked when the dealer loop finishes to score the round.
	Class of LoopCallback is DealerTurnCompleteCallback{

		replace [[String]] is using: [
			['base', 'sys', as Output()]
		];
		local Blackjack is game;

		replace Function is init(Blackjack is game){
			:game: game;
		}

		replace Function is onComplete(LoopControl is control){
			line("\nDealer stands or busts.");
			game:evaluateRoundOutcome();
		}

	}

	## Console input handler for player `(h)it` / `(s)tand` commands.
	Class of InputHandler is PlayerTurnHandler{

		replace [[String]] is using: [
			['base', 'sys', as Output()],
			['base', 'sys', as Conditional()]
		];
		local Blackjack is game;

		replace Function is init(Blackjack is game){
			:game: game;
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
					line("You drew: {{card}}");

					local Int is score: game:handValue(hand: game:playerHand);
					line("Your total is now: {{score}}");

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
					line("You stand with total: {{game:handValue(hand: game:playerHand)}}");
					game:startDealerTurn();
				},
				else: {
					line('Invalid command. Please enter \'h\' (hit) or \'s\' (stand).');
					game:promptPlayerAction();
				}
			]);
		}

	}

	## Draws a random card value (1..10).
	Function of Int is drawCard(){
		return deckUtil:drawCard();
	}

	## Computes the optimal Blackjack score for [hand], treating Aces (`1`) as 11 or 1.
	Function of Int is handValue(Array of Int is hand){
		return deckUtil:handValue(hand: hand);
	}

	## Prompts the player for hit/stand input via [consIn].
	Function is promptPlayerAction(){
		line('Would you like to (h)it or (s)tand?');
		local Blackjack:PlayerTurnHandler is handler: Blackjack:PlayerTurnHandler(game: :);
		consIn(handler: handler);
	}

	## Runs the dealer's automated draw loop until total >= 17.
	Function is startDealerTurn(){
		line("\n--- Starting Dealer's Turn ---");
		local Blackjack:DealerTurnLoop is dealerLoop: Blackjack:DealerTurnLoop(game: :);
		local Blackjack:DealerTurnCompleteCallback is onComplete: Blackjack:DealerTurnCompleteCallback(game: :);
		local LoopControl is control: LoopControl();
		control:onComplete: local Function(){
			onComplete:onComplete(control: control);
		};
		run(loop: dealerLoop, control: control);
	}

	## Compares player and dealer scores and prints the final round outcome.
	Function is evaluateRoundOutcome(){
		local Int is playerScore: handValue(hand: playerHand);
		local Int is dealerScore: handValue(hand: dealerHand);

		line("\n=== Final Results ===");
		line("Player: {{playerScore}} | Dealer: {{dealerScore}}");

		match(when: [
			{ dealerScore > 21 }:          { line('Dealer busts! You win!'); },
			{ playerScore > dealerScore }: { line('You beat the dealer! You win!'); },
			{ dealerScore > playerScore }: { line('Dealer wins!'); },
			else:                          { line('Push (Tie)!'); }
		]);
	}

	## Entry point; deals initial hands and begins the player turn.
	replace Function is init(Map of String to String is args){
		line('======================================');
		line('         Welcome to SpecJack          ');
		line("======================================\n");

		deck: deckUtil:createDeck();

		playerHand:add(item: drawCard());
		playerHand:add(item: drawCard());
		dealerHand:add(item: drawCard());
		dealerHand:add(item: drawCard());

		line("Your hand: {{playerHand[0]}}, {{playerHand[1]}} (Total: {{handValue(hand: playerHand)}})");
		line("Dealer's up card: {{dealerHand[0]}} [Hidden Card]\n");

		if({ handValue(hand: playerHand) == 21 }, {
			line('Natural Blackjack! You win!');
			return;
		});

		promptPlayerAction();
	}

}
