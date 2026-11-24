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

	Function of Card is fromNotation(String is code){
		local String is up: code:trim():toUpper();
		if({ up:length() < 2 }, { return Card(); });
		local String is sCh: up:substring(start: up:length() - 1, end: up:length());
		local String is rStr: up:substring(start: 0, end: up:length() - 1);
		local Suit is s: Suit:SPADES;
		if({ sCh == 'H' || sCh == '♥' }, { s: Suit:HEARTS; });
		if({ sCh == 'D' || sCh == '♦' }, { s: Suit:DIAMONDS; });
		if({ sCh == 'C' || sCh == '♣' }, { s: Suit:CLUBS; });
		local Rank is r: Rank:ACE;
		if({ rStr == '2' }, { r: Rank:TWO; });
		if({ rStr == '3' }, { r: Rank:THREE; });
		if({ rStr == '4' }, { r: Rank:FOUR; });
		if({ rStr == '5' }, { r: Rank:FIVE; });
		if({ rStr == '6' }, { r: Rank:SIX; });
		if({ rStr == '7' }, { r: Rank:SEVEN; });
		if({ rStr == '8' }, { r: Rank:EIGHT; });
		if({ rStr == '9' }, { r: Rank:NINE; });
		if({ rStr == '10' || rStr == 'T' }, { r: Rank:TEN; });
		if({ rStr == 'J' }, { r: Rank:JACK; });
		if({ rStr == 'Q' }, { r: Rank:QUEEN; });
		if({ rStr == 'K' }, { r: Rank:KING; });
		return Card(rank: r, suit: s);
	}
}
