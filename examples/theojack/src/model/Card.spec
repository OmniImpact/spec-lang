#! Package theojack:model
#! Playing card value combining [Rank] and [Suit], plus deck/random helpers.

Class is Card{
	replace [String] is namespace: ['theojack', 'model'];

	merge [[String]] is using: [
		['base', 'math', as Math()],
		['theojack', 'model', [Rank, Suit]]
	];

	Rank is rank: Rank:ACE;
	Suit is suit: Suit:SPADES;

	replace Function is init(Rank is rank: Rank:ACE, Suit is suit: Suit:SPADES){
		:rank: rank;
		:suit: suit;
	}

	Function of String is label(){
		return rank:value() . suit:value();
	}

	Function of Boolean is isRed(){
		return suit == Suit:HEARTS || suit == Suit:DIAMONDS;
	}

	Function of Card is randomCard(){
		local Int is rIdx: toInt(value: random(min: 0.0, max: 13.0));
		if({ rIdx < 0 }, { rIdx: 0; });
		if({ rIdx > 12 }, { rIdx: 12; });
		local Int is sIdx: toInt(value: random(min: 0.0, max: 4.0));
		if({ sIdx < 0 }, { sIdx: 0; });
		if({ sIdx > 3 }, { sIdx: 3; });
		local [Rank] is ranks: [
			Rank:ACE, Rank:TWO, Rank:THREE, Rank:FOUR, Rank:FIVE, Rank:SIX,
			Rank:SEVEN, Rank:EIGHT, Rank:NINE, Rank:TEN, Rank:JACK, Rank:QUEEN, Rank:KING
		];
		local [Suit] is suits: [Suit:SPADES, Suit:HEARTS, Suit:DIAMONDS, Suit:CLUBS];
		return Card(rank: ranks:get(index: rIdx), suit: suits:get(index: sIdx));
	}
}
