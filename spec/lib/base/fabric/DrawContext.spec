#! Package base:fabric
#! 2D software drawing context targeting a `SuitCanvas` (ARGB8888).

Class is DrawContext{
	replace [String] is namespace: ['base', 'fabric'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'suit', SuitCanvas]
	];

	SuitCanvas is canvas: SuitCanvas(width: 1, height: 1);

	replace Function is init(SuitCanvas is canvas){
		:canvas: canvas;
	}

	## Clears the target canvas to fully transparent (`0x00000000`).
	Function is clearTransparent(){
		canvas:clear(color: 0);
	}

	## Fills an axis-aligned rectangle.
	Function is fillRect(Int is x, Int is y, Int is w, Int is h, Int is color){
		canvas:fillRect(x: x, y: y, w: w, h: h, color: color);
	}

	## Draws a 1px outline around ([x], [y], [w], [h]).
	Function is strokeRect(Int is x, Int is y, Int is w, Int is h, Int is color){
		if({ w <= 0 || h <= 0 }, { return; });
		canvas:fillRect(x: x, y: y, w: w, h: 1, color: color);
		canvas:fillRect(x: x, y: y + h - 1, w: w, h: 1, color: color);
		canvas:fillRect(x: x, y: y, w: 1, h: h, color: color);
		canvas:fillRect(x: x + w - 1, y: y, w: 1, h: h, color: color);
	}

	## Measures the pixel width of [text] at integer [scale].
	Function of Int is measureTextWidth(String is text, Int is scale: 2){
		local Int is len: text:length();
		if({ len <= 0 }, { return 0; });
		return len * 6 * scale - scale;
	}

	## Measures the pixel height of a single line at integer [scale].
	Function of Int is measureTextHeight(Int is scale: 2){
		return 7 * scale;
	}

	## Returns a 5-bit row mask for a 5x7 glyph at [code] and [row] (0..6).
	local Function of Int is glyphRow(Int is code, Int is row){
		## Uppercase normalization for ASCII 'a'..'z'
		local Int is c: if({ code >= 97 && code <= 122 }, { code - 32 }, { code });
		if({ c == 48 }, { ## '0'
			if({ row == 0 || row == 6 }, { return 14; });
			if({ row == 1 || row == 5 }, { return 17; });
			if({ row == 2 }, { return 19; });
			if({ row == 3 }, { return 21; });
			return 25;
		});
		if({ c == 49 }, { ## '1'
			if({ row == 0 }, { return 4; });
			if({ row == 1 }, { return 12; });
			if({ row == 6 }, { return 14; });
			return 4;
		});
		if({ c == 50 }, { ## '2'
			if({ row == 0 }, { return 14; });
			if({ row == 1 }, { return 17; });
			if({ row == 2 }, { return 1; });
			if({ row == 3 }, { return 6; });
			if({ row == 4 }, { return 8; });
			if({ row == 5 }, { return 16; });
			return 31;
		});
		if({ c == 51 }, { ## '3'
			if({ row == 0 || row == 6 }, { return 30; });
			if({ row == 3 }, { return 14; });
			return 1;
		});
		if({ c == 52 }, { ## '4'
			if({ row == 0 }, { return 2; });
			if({ row == 1 }, { return 6; });
			if({ row == 2 }, { return 10; });
			if({ row == 3 }, { return 18; });
			if({ row == 4 }, { return 31; });
			return 2;
		});
		if({ c == 53 }, { ## '5'
			if({ row == 0 }, { return 31; });
			if({ row == 1 }, { return 16; });
			if({ row == 2 }, { return 30; });
			if({ row == 3 || row == 4 || row == 5 }, { return 1; });
			return 30;
		});
		if({ c == 54 }, { ## '6'
			if({ row == 0 }, { return 14; });
			if({ row == 1 || row == 2 }, { return 16; });
			if({ row == 3 }, { return 30; });
			if({ row == 4 || row == 5 }, { return 17; });
			return 14;
		});
		if({ c == 55 }, { ## '7'
			if({ row == 0 }, { return 31; });
			if({ row == 1 }, { return 1; });
			if({ row == 2 }, { return 2; });
			if({ row == 3 }, { return 4; });
			return 8;
		});
		if({ c == 56 }, { ## '8'
			if({ row == 0 || row == 3 || row == 6 }, { return 14; });
			return 17;
		});
		if({ c == 57 }, { ## '9'
			if({ row == 0 }, { return 14; });
			if({ row == 1 || row == 2 }, { return 17; });
			if({ row == 3 }, { return 15; });
			if({ row == 4 || row == 5 }, { return 1; });
			return 14;
		});
		if({ c == 65 }, { ## 'A'
			if({ row == 0 }, { return 14; });
			if({ row == 3 }, { return 31; });
			return 17;
		});
		if({ c == 66 }, { ## 'B'
			if({ row == 0 || row == 3 || row == 6 }, { return 30; });
			return 17;
		});
		if({ c == 67 }, { ## 'C'
			if({ row == 0 || row == 6 }, { return 14; });
			if({ row == 1 || row == 5 }, { return 17; });
			return 16;
		});
		if({ c == 68 }, { ## 'D'
			if({ row == 0 || row == 6 }, { return 30; });
			return 17;
		});
		if({ c == 69 }, { ## 'E'
			if({ row == 0 || row == 6 }, { return 31; });
			if({ row == 3 }, { return 28; });
			return 16;
		});
		if({ c == 70 }, { ## 'F'
			if({ row == 0 }, { return 31; });
			if({ row == 3 }, { return 28; });
			return 16;
		});
		if({ c == 71 }, { ## 'G'
			if({ row == 0 || row == 6 }, { return 14; });
			if({ row == 1 }, { return 17; });
			if({ row == 2 }, { return 16; });
			if({ row == 3 }, { return 23; });
			return 17;
		});
		if({ c == 72 }, { ## 'H'
			if({ row == 3 }, { return 31; });
			return 17;
		});
		if({ c == 73 }, { ## 'I'
			if({ row == 0 || row == 6 }, { return 14; });
			return 4;
		});
		if({ c == 74 }, { ## 'J'
			if({ row == 0 }, { return 7; });
			if({ row == 5 }, { return 17; });
			if({ row == 6 }, { return 14; });
			return 2;
		});
		if({ c == 75 }, { ## 'K'
			if({ row == 0 || row == 6 }, { return 17; });
			if({ row == 1 || row == 5 }, { return 18; });
			if({ row == 2 || row == 4 }, { return 20; });
			return 24;
		});
		if({ c == 76 }, { ## 'L'
			if({ row == 6 }, { return 31; });
			return 16;
		});
		if({ c == 77 }, { ## 'M'
			if({ row == 1 }, { return 27; });
			if({ row == 2 }, { return 21; });
			return 17;
		});
		if({ c == 78 }, { ## 'N'
			if({ row == 1 }, { return 25; });
			if({ row == 2 }, { return 21; });
			if({ row == 3 }, { return 19; });
			return 17;
		});
		if({ c == 79 }, { ## 'O'
			if({ row == 0 || row == 6 }, { return 14; });
			return 17;
		});
		if({ c == 80 }, { ## 'P'
			if({ row == 0 || row == 3 }, { return 30; });
			if({ row == 1 || row == 2 }, { return 17; });
			return 16;
		});
		if({ c == 81 }, { ## 'Q'
			if({ row == 0 }, { return 14; });
			if({ row == 4 }, { return 21; });
			if({ row == 5 }, { return 18; });
			if({ row == 6 }, { return 13; });
			return 17;
		});
		if({ c == 82 }, { ## 'R'
			if({ row == 0 || row == 3 }, { return 30; });
			if({ row == 4 }, { return 20; });
			if({ row == 5 }, { return 18; });
			return 17;
		});
		if({ c == 83 }, { ## 'S'
			if({ row == 0 || row == 6 }, { return 14; });
			if({ row == 1 || row == 2 }, { return 16; });
			if({ row == 3 }, { return 14; });
			if({ row == 4 || row == 5 }, { return 1; });
			return 14;
		});
		if({ c == 84 }, { ## 'T'
			if({ row == 0 }, { return 31; });
			return 4;
		});
		if({ c == 85 }, { ## 'U'
			if({ row == 6 }, { return 14; });
			return 17;
		});
		if({ c == 86 }, { ## 'V'
			if({ row == 4 }, { return 10; });
			if({ row == 5 || row == 6 }, { return 4; });
			return 17;
		});
		if({ c == 87 }, { ## 'W'
			if({ row == 4 }, { return 21; });
			if({ row == 5 }, { return 27; });
			return 17;
		});
		if({ c == 88 }, { ## 'X'
			if({ row == 2 || row == 4 }, { return 10; });
			if({ row == 3 }, { return 4; });
			return 17;
		});
		if({ c == 89 }, { ## 'Y'
			if({ row == 0 || row == 1 }, { return 17; });
			if({ row == 2 }, { return 10; });
			return 4;
		});
		if({ c == 90 }, { ## 'Z'
			if({ row == 0 || row == 6 }, { return 31; });
			if({ row == 1 }, { return 1; });
			if({ row == 2 }, { return 2; });
			if({ row == 3 }, { return 4; });
			if({ row == 4 }, { return 8; });
			return 16;
		});
		if({ c == 58 }, { ## ':'
			if({ row == 2 || row == 5 }, { return 4; });
			return 0;
		});
		if({ c == 46 }, { ## '.'
			if({ row == 6 }, { return 4; });
			return 0;
		});
		if({ c == 44 }, { ## ','
			if({ row == 5 }, { return 4; });
			if({ row == 6 }, { return 8; });
			return 0;
		});
		if({ c == 45 }, { ## '-'
			if({ row == 3 }, { return 14; });
			return 0;
		});
		if({ c == 32 }, { ## ' '
			return 0;
		});
		## Generic fallback box for any other printable char
		if({ row == 0 || row == 6 }, { return 31; });
		return 17;
	}

	## Draws crisp 5x7 bitmap text at ([x], [y]) with [color] and integer [scale].
	Function is drawText(Int is x, Int is y, String is text, Int is color, Int is scale: 2){
		local Int is len: text:length();
		times(count: len, worker: local Function(Int is i){
			local Int is code: text:byteAt(index: i);
			local Int is gx: x + i * 6 * scale;
			times(count: 7, worker: local Function(Int is row){
				local Int is mask: :glyphRow(code: code, row: row);
				times(count: 5, worker: local Function(Int is col){
					local Int is bit: (mask >> (4 - col)) & 1;
					if({ bit != 0 }, {
						canvas:fillRect(
							x: gx + col * scale,
							y: y + row * scale,
							w: scale,
							h: scale,
							color: color
						);
					});
				});
			});
		});
	}
}
