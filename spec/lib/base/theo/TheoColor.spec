#! Package base:theo
#! Color descriptor for Theo widgets and cell buffers (none, 256-color, or 24-bit RGB).

Class is TheoColor{
	namespace: ['base', 'theo'];

	replace Array of Array of String is using: [
		['base', 'sys', as Ansi()],
		['base', 'sys', as Conditional()]
	];

	Int is kind: 0;
	Int is c1: 0;
	Int is c2: 0;
	Int is c3: 0;

	replace Function is init(){
		:kind: 0;
	}

	held Function of TheoColor is none(){
		return TheoColor();
	}

	held Function of TheoColor is ansi(Int is code){
		local TheoColor is c: TheoColor();
		c:kind: 1;
		c:c1: code;
		return c;
	}

	held Function of TheoColor is rgb(Int is r, Int is g, Int is b){
		local TheoColor is c: TheoColor();
		c:kind: 2;
		c:c1: r;
		c:c2: g;
		c:c3: b;
		return c;
	}

	Function of Boolean is isSet(){
		return kind != 0;
	}

	Function of Boolean is equals(TheoColor is other){
		return kind == other:kind && c1 == other:c1 && c2 == other:c2 && c3 == other:c3;
	}

	Function of String is fgSeq(){
		if({ kind == 1 }, { return fg256(code: c1); });
		if({ kind == 2 }, { return fgRgb(r: c1, g: c2, b: c3); });
		return '';
	}

	Function of String is bgSeq(){
		if({ kind == 1 }, { return bg256(code: c1); });
		if({ kind == 2 }, { return bgRgb(r: c1, g: c2, b: c3); });
		return '';
	}
}
