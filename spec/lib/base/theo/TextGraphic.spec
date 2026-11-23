#! Package base:theo
#! Multi-line preformatted Unicode/ASCII graphic display widget.

Class of Widget is TextGraphic{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'theo', Widget],
		['base', 'theo', TheoColor],
		['base', 'theo', TheoBuffer],
		['base', 'theo', TheoRenderer],
		['base', 'sys', as Loops()]
	];

	Array of String is rows: Array();
	TheoColor is color: TheoColor:none();

	replace Function is init(String is graphic: '', TheoColor is color: TheoColor:none()){
		:rows: graphic:lines();
		:color: color;
	}

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){
		return rows:length();
	}

	replace Function is paint(TheoBuffer is buf, TheoRenderer is renderer){
		local Int is i: 0;
		while({ i < rows:length() && i < boxH }, {
			buf:drawText(x: boxX, y: boxY + i, text: rows:get(index: i), fg: color);
			i: i + 1;
		});
	}
}
