#! Package theojack:model
#! Standard 52-card shuffled deck with automatic reshuffle.

Class is Deck{
	replace [String] is namespace: ['theojack', 'model'];

	merge [[String]] is using: [
		['base', 'math', as Math()],
		['theojack', 'model', [Card, Rank, Suit]]
	];

	[Card] is cards: [];
	Int is pos: 0;

	replace Function is init(){
		shuffle();
	}

	Function is shuffle(){
		local [Rank] is ranks: [
			Rank:ACE, Rank:TWO, Rank:THREE, Rank:FOUR, Rank:FIVE, Rank:SIX,
			Rank:SEVEN, Rank:EIGHT, Rank:NINE, Rank:TEN, Rank:JACK, Rank:QUEEN, Rank:KING
		];
		local [Suit] is suits: [Suit:SPADES, Suit:HEARTS, Suit:DIAMONDS, Suit:CLUBS];
		local [Card] is fresh: [];
		local Int is si: 0;
		while({ si < suits:length() }, {
			local Int is ri: 0;
			while({ ri < ranks:length() }, {
				fresh:push(item: Card(rank: ranks:get(index: ri), suit: suits:get(index: si)));
				ri: ri + 1;
			});
			si: si + 1;
		});

		local Int is i: fresh:length() - 1;
		while({ i > 0 }, {
			local Int is j: toInt(value: random(min: 0.0, max: (i + 1) as Float));
			if({ j < 0 }, { j: 0; });
			if({ j > i }, { j: i; });
			local Card is tmp: fresh:get(index: i);
			fresh:set(index: i, item: fresh:get(index: j));
			fresh:set(index: j, item: tmp);
			i: i - 1;
		});
		:cards: fresh;
		:pos: 0;
	}

	Function of Int is remaining(){ cards:length() - pos }

	## True once fewer than [cutCards] cards remain; callers reshuffle between
	## rounds so the deck never runs dry (and duplicates cards) mid-round.
	Function of Boolean is needsShuffle(Int is cutCards){ remaining() < cutCards }

	Function of Card is draw(){
		if({ pos >= cards:length() }, {
			shuffle();
		});
		local Card is c: cards:get(index: pos);
		:pos: pos + 1;
		return c;
	}
}
