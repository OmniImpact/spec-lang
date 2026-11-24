#! Package base:theo
#! 2D virtual terminal cell buffer with clipping and drawing primitives.

Class is TheoBuffer{
	replace [String] is namespace: ['base', 'theo'];

	replace [[String]] is using: [
		['base', 'theo', TheoCell],
		['base', 'theo', TheoColor],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	Int is width: 80;
	Int is height: 24;
	Array of TheoCell is cells: Array();

	Int is clipX: 0;
	Int is clipY: 0;
	Int is clipW: 80;
	Int is clipH: 24;

	replace Function is init(Int is width: 80, Int is height: 24){
		resize(width: width, height: height);
	}

	Function is resize(Int is width, Int is height){
		local Int is w: if({ width < 1 }, { 1 }, { width });
		local Int is h: if({ height < 1 }, { 1 }, { height });
		:width: w;
		:height: h;
		:clipX: 0;
		:clipY: 0;
		:clipW: w;
		:clipH: h;
		:cells: Array();
		local Int is total: w * h;
		local Int is i: 0;
		while({ i < total }, {
			:cells:add(item: TheoCell());
			i: i + 1;
		});
	}

	Function is setClip(Int is x, Int is y, Int is w, Int is h){
		local Int is x0: if({ x < 0 }, { 0 }, { x });
		local Int is y0: if({ y < 0 }, { 0 }, { y });
		local Int is x1: x + w;
		local Int is y1: y + h;
		if({ x1 > width }, { x1: width; });
		if({ y1 > height }, { y1: height; });
		:clipX: x0;
		:clipY: y0;
		:clipW: if({ x1 > x0 }, { x1 - x0 }, { 0 });
		:clipH: if({ y1 > y0 }, { y1 - y0 }, { 0 });
	}

	Function is clearClip(){
		:clipX: 0;
		:clipY: 0;
		:clipW: width;
		:clipH: height;
	}

	Function is clear(){
		local Int is i: 0;
		local Int is n: cells:length();
		local TheoColor is none: TheoColor:none();
		while({ i < n }, {
			local TheoCell is c: cells:get(index: i);
			c:ch: ' ';
			c:fg: none;
			c:bg: none;
			c:bold: false;
			c:underline: false;
			c:reverse: false;
			i: i + 1;
		});
	}

	Function of TheoCell is cellAt(Int is x, Int is y){ cells:get(index: y * width + x); }

	Function is setCell(Int is x, Int is y, String is ch, TheoColor is fg: TheoColor:none(), TheoColor is bg: TheoColor:none(), Boolean is bold: false, Boolean is underline: false, Boolean is reverse: false){
		if({ x < clipX || x >= clipX + clipW || y < clipY || y >= clipY + clipH }, {
			return;
		});
		if({ x < 0 || x >= width || y < 0 || y >= height }, {
			return;
		});
		local TheoCell is c: cells:get(index: y * width + x);
		c:ch: ch;
		if({ fg:isSet() }, { c:fg: fg; });
		if({ bg:isSet() }, { c:bg: bg; });
		c:bold: bold;
		c:underline: underline;
		c:reverse: reverse;
	}

	Function is fillRect(Int is x, Int is y, Int is w, Int is h, TheoColor is fg: TheoColor:none(), TheoColor is bg: TheoColor:none()){
		local Int is ry: 0;
		while({ ry < h }, {
			local Int is rx: 0;
			while({ rx < w }, {
				setCell(x: x + rx, y: y + ry, ch: ' ', fg: fg, bg: bg);
				rx: rx + 1;
			});
			ry: ry + 1;
		});
	}

	Function is drawText(Int is x, Int is y, String is text, TheoColor is fg: TheoColor:none(), TheoColor is bg: TheoColor:none(), Boolean is bold: false, Boolean is underline: false, Boolean is reverse: false){
		local Int is n: text:length();
		local Int is i: 0;
		local Int is col: 0;
		while({ i < n }, {
			local Int is b: text:byteAt(index: i, default: 32);
			local Int is step: 1;
			if({ b >= 240 && b < 248 }, { step: 4; }, {
				if({ b >= 224 && b < 240 }, { step: 3; }, {
					if({ b >= 192 && b < 224 }, { step: 2; });
				});
			});
			local Int is endIdx: i + step;
			if({ endIdx > n }, { endIdx: n; });
			local String is ch: text:substring(start: i, end: endIdx);
			setCell(x: x + col, y: y, ch: ch, fg: fg, bg: bg, bold: bold, underline: underline, reverse: reverse);
			col: col + 1;
			i: endIdx;
		});
	}

	Function is drawBox(Int is x, Int is y, Int is w, Int is h, TheoColor is borderColor: TheoColor:none(), TheoColor is bg: TheoColor:none(), Boolean is rounded: true){
		if({ w < 2 || h < 2 }, { return; });
		local String is tl: if({ rounded }, { '╭' }, { '┌' });
		local String is tr: if({ rounded }, { '╮' }, { '┐' });
		local String is bl: if({ rounded }, { '╰' }, { '└' });
		local String is br: if({ rounded }, { '╯' }, { '┘' });
		setCell(x: x, y: y, ch: tl, fg: borderColor, bg: bg);
		setCell(x: x + w - 1, y: y, ch: tr, fg: borderColor, bg: bg);
		setCell(x: x, y: y + h - 1, ch: bl, fg: borderColor, bg: bg);
		setCell(x: x + w - 1, y: y + h - 1, ch: br, fg: borderColor, bg: bg);
		local Int is ix: 1;
		while({ ix < w - 1 }, {
			setCell(x: x + ix, y: y, ch: '─', fg: borderColor, bg: bg);
			setCell(x: x + ix, y: y + h - 1, ch: '─', fg: borderColor, bg: bg);
			ix: ix + 1;
		});
		local Int is iy: 1;
		while({ iy < h - 1 }, {
			setCell(x: x, y: y + iy, ch: '│', fg: borderColor, bg: bg);
			setCell(x: x + w - 1, y: y + iy, ch: '│', fg: borderColor, bg: bg);
			iy: iy + 1;
		});
	}

	## Renders row [y] as plain unstyled text (useful for unit-test assertions).
	Function of String is rowText(Int is y){
		if({ y < 0 || y >= height }, { return ''; });
		local String is s: '';
		local Int is x: 0;
		while({ x < width }, {
			s: "{{s}}{{cellAt(x: x, y: y):ch}}";
			x: x + 1;
		});
		return s;
	}
}
