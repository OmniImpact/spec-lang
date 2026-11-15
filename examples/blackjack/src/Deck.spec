#! Deck and hand-scoring utility for Blackjack.

Class is Deck{

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'math', as Math()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	Function of Array of Int is createDeck(){
		local Array of Int is cards: [];
		local Int is value: 1;
		while({ value <= 10 }, {
			repeat(count: 4, worker: {
				cards:add(item: value);
			});
			value: value + 1;
		});
		return cards;
	}

	Function of Int is drawCard(){
		local Float is roll: random(min: 1.0, max: 11.0);
		return floor(value: roll) as Int;
	}

	Function of Int is handValue(Array of Int is hand){
		local Int is total: hand:fold(
			initial: 0,
			accumulate: local Function of Int(Int is acc, Int is card){
				return acc + if({ card == 1 }, { 11 }, { card });
			}
		);
		local Int is aceCount: hand:count(
			predicate: local Function of Boolean(Int is card){
				return card == 1;
			}
		);

		local Int is excess: total - 21;
		local Int is downgrades: 0;
		if({ excess > 0 }, {
			downgrades: (excess + 9) / 10;
			if({ downgrades > aceCount }, {
				downgrades: aceCount;
			});
		});
		return total - (downgrades * 10);
	}

}
