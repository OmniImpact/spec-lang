Enum is RoundOutcome {
	PLAYER_WINS,
	DEALER_WINS,
	DEALER_BUSTS,
	PUSH
}

Class is Blackjack{

	replace local Array of String is using: [
		base:struct:Array,
		base:struct:Map,
		base:iterator:Loop,
		base:iterator:LoopControl,
		base:iterator:LoopCallback,
		base:iterator:While,
		base:io:Output,
		base:io:Input,
		base:io:InputHandler,
		base:math:*
	];

	# Game State Fields
	local Array of Int is deck: [];
	local Array of Int is playerHand: [];
	local Array of Int is dealerHand: [];
	local Boolean is roundActive: true;

	# =========================================================================
	# Deck Builder Loop (Shorthand Syntax: Batch Add Array & Positional Init)
	# =========================================================================
	Class is BuildDeckLoop extends Loop{
		local Array of Int is targetDeck;
		local Int is currentVal: 1;

		replace init(Array of Int is targetDeck){
			self:targetDeck: targetDeck;
		}

		replace evaluate(){
			return currentVal <= 10;
		}

		replace iteration(control){
			# Batch add 4 cards at once using array parameter shorthand
			targetDeck:add([currentVal, currentVal, currentVal, currentVal]);
			currentVal: currentVal + 1;
			return true;
		}
	}

	# =========================================================================
	# Dealer's Turn Loop (Shorthand: Positional Args & Automated Lifecycle)
	# =========================================================================
	Class is DealerTurnLoop extends Loop{
		local Blackjack is game;

		replace init(Blackjack is game){
			self:game: game;
		}

		replace evaluate(){
			return game:handValue(game:dealerHand) < 17;
		}

		replace iteration(control){
			local Int is card: game:drawCard();
			game:dealerHand:add(card);

			local Int is newScore: game:handValue(game:dealerHand);
			output:line("Dealer draws: " . card . " (Total: " . newScore . ")");
			return true;
		}
	}

	# =========================================================================
	# Dealer Turn Completion Callback
	# =========================================================================
	Class is DealerTurnCompleteCallback extends LoopCallback{
		local Blackjack is game;

		replace init(Blackjack is game){
			self:game: game;
		}

		replace onComplete(control){
			output:line("\nDealer stands or busts.");
			game:evaluateRoundOutcome();
		}
	}

	# =========================================================================
	# Interactive Input Handler
	# =========================================================================
	Class is PlayerTurnHandler extends InputHandler{
		local Blackjack is game;

		replace init(Blackjack is game){
			self:game: game;
		}

		replace onInput(action){
			if (action == "") {
				output:line("\nInput closed. Thanks for playing!");
				game:roundActive: false;
				return;
			}
			when (action) {
				is "h", "hit": {
					local Int is card: game:drawCard();
					game:playerHand:add(card);
					output:line("You drew: " . card);

					local Int is score: game:handValue(game:playerHand);
					output:line("Your total is now: " . score);

					if (score > 21) {
						output:line("Bust! You lose.");
						game:roundActive: false;
					} else if (score == 21) {
						output:line("21! Standing automatically.");
						game:startDealerTurn();
					} else {
						game:promptPlayerAction();
					}
				}
				is "s", "stand": {
					output:line("You stand with total: " . game:handValue(game:playerHand));
					game:startDealerTurn();
				}
				else: {
					output:line("Invalid command. Please enter 'h' (hit) or 's' (stand).");
					game:promptPlayerAction();
				}
			}
		}
	}

	# =========================================================================
	# Helpers (Using Positional Calls and Batch Add)
	# =========================================================================
	Function of Int is drawCard(){
		# Positional argument shorthand for math functions
		local Float is roll: math:random(1.0, 11.0);
		return math:toInt(math:floor(roll));
	}

	Function of Int is handValue(Array of Int is hand){
		Class is ScoreAccumulator{
			local Int is total: 0;
			local Int is aceCount: 0;
		}
		local ScoreAccumulator is acc: ScoreAccumulator:init();

		# Tally hand cards
		Class is ScoreLoop extends Loop{
			local Array of Int is hand;
			local ScoreAccumulator is acc;
			local Int is idx: 0;

			replace init(Array of Int is hand, ScoreAccumulator is acc){
				self:hand: hand;
				self:acc: acc;
			}

			replace evaluate(){
				return idx < hand:length();
			}

			replace iteration(control){
				local Int is card: hand[idx];
				if (card == 1) {
					acc:aceCount: acc:aceCount + 1;
					acc:total: acc:total + 11;
				} else {
					acc:total: acc:total + card;
				}
				idx: idx + 1;
				return true;
			}
		}
		While:run(ScoreLoop:init(hand, acc), LoopControl:init());

		# Adjust Aces if total exceeds 21
		Class is AceAdjustLoop extends Loop{
			local ScoreAccumulator is acc;

			replace init(ScoreAccumulator is acc){
				self:acc: acc;
			}

			replace evaluate(){
				return acc:total > 21 && acc:aceCount > 0;
			}

			replace iteration(control){
				acc:total: acc:total - 10;
				acc:aceCount: acc:aceCount - 1;
				return true;
			}
		}
		While:run(AceAdjustLoop:init(acc), LoopControl:init());

		return acc:total;
	}

	Function is promptPlayerAction(){
		output:line("Would you like to (h)it or (s)tand?");
		Input:prompt(PlayerTurnHandler:init(self));
	}

	Function is startDealerTurn(){
		output:line("\n--- Starting Dealer's Turn ---");
		local LoopControl is control: LoopControl:init(DealerTurnCompleteCallback:init(self));
		While:run(DealerTurnLoop:init(self), control);
	}

	Function is evaluateRoundOutcome(){
		local Int is playerScore: handValue(playerHand);
		local Int is dealerScore: handValue(dealerHand);

		output:line("\n=== Final Results ===");
		output:line("Player: " . playerScore . " | Dealer: " . dealerScore);

		local RoundOutcome is outcome: if (dealerScore > 21)
			RoundOutcome:DEALER_BUSTS
		else if (playerScore > dealerScore)
			RoundOutcome:PLAYER_WINS
		else if (dealerScore > playerScore)
			RoundOutcome:DEALER_WINS
		else
			RoundOutcome:PUSH;

		when (outcome) {
			is DEALER_BUSTS: { output:line("Dealer busts! You win!"); }
			is PLAYER_WINS: { output:line("You beat the dealer! You win!"); }
			is DEALER_WINS: { output:line("Dealer wins!"); }
			is PUSH: { output:line("Push (Tie)!"); }
		}
	}

	# =========================================================================
	# Application Entry Point
	# =========================================================================
	replace init(Map of String to String is args){
		output:line("======================================");
		output:line("      Welcome to SpecJack (Clean)     ");
		output:line("======================================\n");

		# 1. Populate card deck via loop runner
		While:run(BuildDeckLoop:init(deck), LoopControl:init());

		# 2. Initial deal using batch array append shorthand
		playerHand:add([drawCard(), drawCard()]);
		dealerHand:add([drawCard(), drawCard()]);

		output:line("Your hand: " . playerHand[0] . ", " . playerHand[1] . " (Total: " . handValue(playerHand) . ")");
		output:line("Dealer's up card: " . dealerHand[0] . " [Hidden Card]\n");

		if (handValue(playerHand) == 21) {
			output:line("Natural Blackjack! You win!");
			return;
		}

		promptPlayerAction();
	}

}
