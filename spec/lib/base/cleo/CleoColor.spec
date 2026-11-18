#! Package base:cleo
#! Unified terminal color value supporting default, 256-color, and 24-bit RGB.

Class is CleoColor{
	namespace: ['base', 'cleo'];

	replace Array of Array of String is using: [
		['base', 'sys', as Ansi()],
		['base', 'sys', as Conditional()]
	];

	Int is kind: 0;
	Int is code: 0;
	Int is r: 0;
	Int is g: 0;
	Int is b: 0;

	replace Function is init(){
	}

	Function of CleoColor is default(){
		local CleoColor is c: CleoColor:init();
		c:kind: 0;
		return c;
	}

	Function of CleoColor is ansi(Int is code){
		local CleoColor is c: CleoColor:init();
		c:kind: 1;
		c:code: code;
		return c;
	}

	Function of CleoColor is rgb(Int is r, Int is g, Int is b){
		local CleoColor is c: CleoColor:init();
		c:kind: 2;
		c:r: r;
		c:g: g;
		c:b: b;
		return c;
	}

	Function of Boolean is isSet(){
		return self:kind != 0;
	}

	Function of String is fgSeq(){
		if({ self:kind == 1 }, {
			return Ansi:fg256(code: self:code);
		});
		if({ self:kind == 2 }, {
			return Ansi:fgRgb(r: self:r, g: self:g, b: self:b);
		});
		return '';
	}

	Function of String is bgSeq(){
		if({ self:kind == 1 }, {
			return Ansi:bg256(code: self:code);
		});
		if({ self:kind == 2 }, {
			return Ansi:bgRgb(r: self:r, g: self:g, b: self:b);
		});
		return '';
	}
}
