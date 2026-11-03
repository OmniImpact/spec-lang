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

	# =========================================================================
	# Game State Fields
	# Context is explicitly passed to internal classes via :init(...)
	# =========================================================================
	local Array of Int is deck: [];
	local Array of Int is playerHand: [];
	local Array of Int is dealerHand: [];
	local Boolean is roundActive: true;

	# =========================================================================
	# Internal ClassInfo: Deck Builder Loop
	# Demonstrates the refined Iterator Loop lifecycle:
	#   - evaluate(): called automatically before/after each step to check continuation
	#   - iteration(control): does the work and returns true (success) or false (error)
	# =========================================================================
	Class is BuildDeckLoop extends Loop{
		local Array of Int is targetDeck;
		local Int is currentVal: 1;

		replace local Function is init(Array of Int is targetDeck){
			self:targetDeck: targetDeck;
		}

		# Automatically checked by the iterator engine after each iteration
		replace local Function of Boolean is evaluate(){
			return currentVal <= 10;
		}

		# Performs the step. Returns true if successful, false if an error occurred
		replace local Function of Boolean is iteration(LoopControl is control){
			targetDeck:add(item: currentVal);
			targetDeck:add(item: currentVal);
			targetDeck:add(item: currentVal);
			targetDeck:add(item: currentVal);

			currentVal: currentVal + 1;
			return true;
		}
	}

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

		replace local Function is init(Blackjack is game){
			self:game: game;
		}

		# Automatically re-evaluated after each draw
		replace local Function of Boolean is evaluate(){
			local Int is currentScore: game:handValue(hand: game:dealerHand);
			return currentScore < 17;
		}

		# Step logic: draw one card
		replace local Function of Boolean is iteration(LoopControl is control){
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

		replace local Function is init(Blackjack is game){
			self:game: game;
		}

		replace local Function is onComplete(LoopControl is control){
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

		replace local Function is init(Blackjack is game){
			self:game: game;
		}

		replace local Function is onInput(String is action){
			if (action == "") {
				output:line("\nInput closed. Thanks for playing!");
				game:roundActive: false;
				return;
			}
			if (action == "h" || action == "hit") {
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
			} else if (action == "s" || action == "stand") {
				output:line("You stand with total: " . game:handValue(hand: game:playerHand));
				game:startDealerTurn();
			} else {
				output:line("Invalid command. Please enter 'h' (hit) or 's' (stand).");
				game:promptPlayerAction();
			}
		}
	}

	# =========================================================================
	# Helper Functions
	# =========================================================================
	Function of Int is drawCard(){
		local Float is roll: math:random(min: 1.0, max: 11.0);
		return math:toInt(value: math:floor(value: roll));
	}

	Function of Int is handValue(Array of Int is hand){
		Class is ScoreAccumulator{
			local Int is total: 0;
			local Int is aceCount: 0;
		}
		local ScoreAccumulator is acc: ScoreAccumulator:init();

		# Loop 1: Tally hand cards
		Class is ScoreLoop extends Loop{
			local Array of Int is hand;
			local ScoreAccumulator is acc;
			local Int is idx: 0;

			replace local Function is init(Array of Int is hand, ScoreAccumulator is acc){
				self:hand: hand;
				self:acc: acc;
			}

			replace local Function of Boolean is evaluate(){
				return idx < hand:length();
			}

			replace local Function of Boolean is iteration(LoopControl is control){
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

		local ScoreLoop is scoreLoop: ScoreLoop:init(hand: hand, acc: acc);
		local LoopControl is scoreControl: LoopControl:init();
		While:run(loop: scoreLoop, control: scoreControl);

		# Loop 2: Downgrade Aces from 11 to 1 if score > 21
		Class is AceAdjustLoop extends Loop{
			local ScoreAccumulator is acc;

			replace local Function is init(ScoreAccumulator is acc){
				self:acc: acc;
			}

			replace local Function of Boolean is evaluate(){
				return acc:total > 21 && acc:aceCount > 0;
			}

			replace local Function of Boolean is iteration(LoopControl is control){
				acc:total: acc:total - 10;
				acc:aceCount: acc:aceCount - 1;
				return true;
			}
		}

		local AceAdjustLoop is aceLoop: AceAdjustLoop:init(acc: acc);
		local LoopControl is aceControl: LoopControl:init();
		While:run(loop: aceLoop, control: aceControl);

		return acc:total;
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
	replace local Function is init(Map of String to String is args){
		output:line("======================================");
		output:line("         Welcome to SpecJack          ");
		output:line("======================================\n");

		# 1. Build and populate card deck
		local BuildDeckLoop is deckLoop: BuildDeckLoop:init(targetDeck: deck);
		local LoopControl is deckControl: LoopControl:init();
		While:run(loop: deckLoop, control: deckControl);

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
