Class is Blackjack{

	replace Array of String is using: [
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

	# =========================================================================
	# Game State Fields
	# Context is explicitly passed to internal classes via :init(...)
	# =========================================================================
	local Array of Int is deck: [];
	local Array of Int is playerHand: [];
	local Array of Int is dealerHand: [];
	local Boolean is roundActive: true;

	# =========================================================================
	# Internal ClassInfo: Dealer's Turn Loop
	# Lifecycle:
	#   - evaluate() checks if dealer score < 17
	#   - iteration() draws card and returns true
	#   - When evaluate() becomes false (dealer >= 17), iterator stops automatically
	#     and fires the onComplete callback attached to LoopControl
	# =========================================================================
	Class is DealerTurnLoop extends Loop{
		local Blackjack is game;

		replace Function is init(Blackjack is game){
			self:game: game;
		}

		# Automatically re-evaluated after each draw
		replace Function of Boolean is evaluate(){
			local Int is currentScore: game:handValue(hand: game:dealerHand);
			return currentScore < 17;
		}

		# Step logic: draw one card
		replace Function of Boolean is iteration(LoopControl is control){
			local Int is card: game:drawCard();
			game:dealerHand:add(item: card);

			local Int is newScore: game:handValue(hand: game:dealerHand);
			output:line("Dealer draws: " . card . " (Total: " . newScore . ")");

			return true; # Step completed normally; engine will call evaluate() next
		}
	}

	# =========================================================================
	# Internal ClassInfo: Dealer Turn Completion Callback
	# Triggered automatically when evaluate() returns false or control is stopped
	# =========================================================================
	Class is DealerTurnCompleteCallback extends LoopCallback{
		local Blackjack is game;

		replace Function is init(Blackjack is game){
			self:game: game;
		}

		replace Function is onComplete(LoopControl is control){
			output:line("\nDealer stands or busts.");
			game:evaluateRoundOutcome();
		}
	}

	# =========================================================================
	# Internal ClassInfo: Interactive Input Handler
	# Dispatched asynchronously on user input
	# =========================================================================
	Class is PlayerTurnHandler extends InputHandler{
		local Blackjack is game;

		replace Function is init(Blackjack is game){
			self:game: game;
		}

		replace Function is onInput(String is action){
			if (action == "") {
				output:line("\nInput closed. Thanks for playing!");
				game:roundActive: false;
				return;
			}
			when (action) {
				is "h", "hit": {
				local Int is card: game:drawCard();
				game:playerHand:add(item: card);
				output:line("You drew: " . card);

				local Int is score: game:handValue(hand: game:playerHand);
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
				output:line("You stand with total: " . game:handValue(hand: game:playerHand));
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
	# Helper Functions
	# =========================================================================
	Function of Int is drawCard(){
		local Float is roll: math:random(min: 1.0, max: 11.0);
		return math:floor(value: roll) as Int;
	}

	## Computes the best blackjack value of a hand: aces count 11, downgraded
	## to 1 as needed to stay at or under 21.
	##
	## @param hand: Card values (1 = ace, 2..10 = face value).
	## @return: Best hand total.
	Function of Int is handValue(Array of Int is hand){
		local Int is total: hand:fold(
			initial: 0,
			accumulate: local Function of Int(Int is acc, Int is card){
				return acc + if (card == 1) 11 else card;
			}
		);
		local Int is aceCount: hand:count(
			predicate: local Function of Boolean(Int is card){
				return card == 1;
			}
		);

		# Each ace can absorb 10 points of excess; compute how many must downgrade.
		local Int is excess: total - 21;
		local Int is downgrades: 0;
		if (excess > 0) {
			downgrades: (excess + 9) / 10;
			if (downgrades > aceCount) {
				downgrades: aceCount;
			}
		}
		return total - (downgrades * 10);
	}

	Function is promptPlayerAction(){
		output:line("Would you like to (h)it or (s)tand?");
		local PlayerTurnHandler is handler: PlayerTurnHandler:init(game: self);
		Input:prompt(handler: handler);
	}

	Function is startDealerTurn(){
		output:line("\n--- Starting Dealer's Turn ---");

		local DealerTurnLoop is dealerLoop: DealerTurnLoop:init(game: self);
		local DealerTurnCompleteCallback is onComplete: DealerTurnCompleteCallback:init(game: self);
		local LoopControl is control: LoopControl:init(onComplete: onComplete);

		While:run(loop: dealerLoop, control: control);
	}

	Function is evaluateRoundOutcome(){
		local Int is playerScore: handValue(hand: playerHand);
		local Int is dealerScore: handValue(hand: dealerHand);

		output:line("\n=== Final Results ===");
		output:line("Player: " . playerScore . " | Dealer: " . dealerScore);

		if (dealerScore > 21) {
			output:line("Dealer busts! You win!");
		} else if (playerScore > dealerScore) {
			output:line("You beat the dealer! You win!");
		} else if (dealerScore > playerScore) {
			output:line("Dealer wins!");
		} else {
			output:line("Push (Tie)!");
		}
	}

	# =========================================================================
	# Application Entry Point
	# =========================================================================
	replace Function is init(Map of String to String is args){
		output:line("======================================");
		output:line("         Welcome to SpecJack          ");
		output:line("======================================\n");

		# 1. Build the deck: four suits of each value 1..10.
		local Int is value: 1;
		While:condition(
			evaluate: local Function of Boolean(){ return value <= 10; },
			iteration: local Function(){
				local Int is suit: 0;
				While:condition(
					evaluate: local Function of Boolean(){ return suit < 4; },
					iteration: local Function(){
						deck:add(item: value);
						suit: suit + 1;
					}
				);
				value: value + 1;
			}
		);

		# 2. Initial deal
		playerHand:add(item: drawCard());
		playerHand:add(item: drawCard());
		dealerHand:add(item: drawCard());
		dealerHand:add(item: drawCard());

		output:line("Your hand: " . playerHand[0] . ", " . playerHand[1] . " (Total: " . handValue(hand: playerHand) . ")");
		output:line("Dealer's up card: " . dealerHand[0] . " [Hidden Card]\n");

		# 3. Check natural 21
		if (handValue(hand: playerHand) == 21) {
			output:line("Natural Blackjack! You win!");
			return;
		}

		# 4. Start player turn
		promptPlayerAction();
	}

}
