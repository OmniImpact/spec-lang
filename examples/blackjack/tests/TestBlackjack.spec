#! specunit: suite

Class of SpecUnitTest is TestBlackjack{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', as Assert()],
		[Deck]
	];

	Function is testHandValueAcesAndBust(){
		local Deck is d: Deck();
		Assert:areEqualInt(21, d:handValue(hand: Array([1, 10])));
		Assert:areEqualInt(12, d:handValue(hand: Array([1, 1])));
		Assert:areEqualInt(18, d:handValue(hand: Array([1, 7, 10])));
		Assert:areEqualInt(23, d:handValue(hand: Array([10, 8, 5])));
	}

	Function is testCreateDeck(){
		local Deck is d: Deck();
		Assert:areEqualInt(40, d:createDeck():length());
	}

}
