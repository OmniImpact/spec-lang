#! Package base:theo
#! Multi-line preformatted Unicode/ASCII graphic display widget.

Class of Widget is TextGraphic{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', Widget],
		['base', 'theo', TheoColor],
		['base', 'theo', TheoBuffer],
		['base', 'theo', TheoRenderer],
		['base', 'sys', [as Conditional(), as Loops()]]
	];

	Array of String is rows: Array();
	TheoColor is color: TheoColor:none();

	replace Function is init(String is graphic: '', TheoColor is color: TheoColor:none()){
		:rows: graphic:lines();
		:color: color;
	}

	replace Function of Int is measureWidth(Int is maxW){
		local Int is best: 0;
		local Int is i: 0;
		while({ i < rows:length() }, {
			local Int is w: rows:get(index: i):runeCount();
			if({ w > best }, { best: w; });
			i: i + 1;
		});
		if({ best > maxW }, { return maxW; });
		return best;
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){ rows:length(); }

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		local TheoColor is effColor: if({ color:isSet() }, { color }, { activeTheme:foreground });
		local Int is i: 0;
		while({ i < rows:length() && i < boxH }, {
			buf:drawText(x: boxX, y: boxY + i, text: rows:get(index: i), fg: effColor);
			i: i + 1;
		});
	}
}
