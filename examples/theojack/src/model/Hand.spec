#! Package theojack:model
#! Blackjack hand with Ace-aware scoring.

Class is Hand{
	replace [String] is namespace: ['theojack', 'model'];

	merge [[String]] is using: [
		['theojack', 'model', [Card, Rank]]
	];

	[Card] is cards: [];

	replace Function is init(){
		:cards: [];
	}

	Function is clear(){
		:cards: [];
	}

	Function is add(Card is card){
		cards:push(item: card);
	}

	Function of Int is count(){ cards:length() }

	Function of Int is score(){
		local Int is total: 0;
		local Int is aces: 0;
		local Int is i: 0;
		while({ i < cards:length() }, {
			local Rank is r: cards:get(index: i):rank;
			if({ r == Rank:ACE }, {
				total: total + 11;
				aces: aces + 1;
			}, {
				if({ r == Rank:TEN || r == Rank:JACK || r == Rank:QUEEN || r == Rank:KING }, {
					total: total + 10;
				}, {
					total: total + (r:value() as Int);
				});
			});
			i: i + 1;
		});
		while({ total > 21 && aces > 0 }, {
			total: total - 10;
			aces: aces - 1;
		});
		return total;
	}

	Function of Boolean is isBlackjack(){ cards:length() == 2 && score() == 21 }

	Function of Boolean is isBust(){ score() > 21 }
}
