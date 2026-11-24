#! Package base:theo
#! Flexible or fixed empty spacer inside [Row] or [Col].

Class of Widget is Spacer{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', Widget]
	];

	Float is weight: 1.0;
	Int is size: 0;

	replace Function is init(Float is weight: 1.0, Int is size: 0){
		:weight: weight;
		:size: size;
	}

	replace Function of Float is flexWeight(){ weight; }

	replace Function of Int is measureWidth(Int is maxW){ size; }

	replace Function of Int is measureHeight(Int is maxW, Int is maxH){ size; }
}
