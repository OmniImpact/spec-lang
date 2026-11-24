#! Package theojack:view
#! Playing card widget rendering any [Card] in any [CardStyle] at 11x7 cells.

Class of Widget is CardView{
	replace [String] is namespace: ['theojack', 'view'];

	merge [[String]] is using: [
		['base', 'theo', [Widget, TheoColor, TheoBuffer, TheoRenderer]],
		['theojack', 'model', [Card, CardStyle]]
	];

	Card is card: Card();
	CardStyle is style: CardStyle:WIREFRAME;

	replace Function is init(Card is card: Card(), CardStyle is style: CardStyle:WIREFRAME){
		:card: card;
		:style: style;
	}

	Function is setCard(Card is next){
		:card: next;
		invalidate();
	}

	Function is setStyle(CardStyle is next){
		:style: next;
		invalidate();
	}

	replace Function of Int is measureWidth(Int is maxW){
		if({ 11 > maxW }, { return maxW; });
		return 11;
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){
		if({ 7 > maxH }, { return maxH; });
		return 7;
	}

	local Function of TheoColor is resolveBg(){
		if({ style == CardStyle:BLACK }, {
			return TheoColor:ansi(code: 16);
		});
		if({ style == CardStyle:WHITE }, {
			return TheoColor:ansi(code: 255);
		});
		if({ style == CardStyle:METALLIC }, {
			if({ card:isRed() }, {
				return TheoColor:ansi(code: 94);
			});
			return TheoColor:ansi(code: 240);
		});
		return TheoColor:none();
	}

	local Function of TheoColor is resolveFg(){
		local Boolean is red: card:isRed();
		if({ style == CardStyle:WHITE }, {
			if({ red }, { return TheoColor:ansi(code: 160); });
			return TheoColor:ansi(code: 16);
		});
		if({ style == CardStyle:METALLIC }, {
			if({ red }, { return TheoColor:ansi(code: 220); });
			return TheoColor:ansi(code: 252);
		});
		if({ red }, { return TheoColor:ansi(code: 196); });
		return TheoColor:ansi(code: 255);
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		if({ boxW < 11 || boxH < 7 }, { return; });
		local TheoColor is fg: resolveFg();
		local TheoColor is bg: resolveBg();
		if({ bg:isSet() }, {
			buf:fillRect(x: boxX, y: boxY, w: 11, h: 7, fg: fg, bg: bg);
		});
		buf:drawBox(x: boxX, y: boxY, w: 11, h: 7, borderColor: fg, bg: bg, rounded: true);

		local String is r: card:rank:value();
		local String is s: card:suit:value();
		buf:drawText(x: boxX + 2, y: boxY + 1, text: r, fg: fg, bg: bg, bold: true);
		buf:drawText(x: boxX + 5, y: boxY + 3, text: s, fg: fg, bg: bg, bold: true);
		local Int is brX: boxX + 9 - r:length();
		buf:drawText(x: brX, y: boxY + 5, text: r, fg: fg, bg: bg, bold: true);
	}
}
