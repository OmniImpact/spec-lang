#! Package base:scrap
#! Syntax highlighter for JSON files (`.json`), inheriting `ScrapHighlighter`.

Class of ScrapHighlighter is JsonHighlighter{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', ScrapHighlighter]
	];

	replace Function of String is languageId(){
		return 'json';
	}

	replace Function of Boolean is matchesExtension(String is lowPath){
		return endsWith(s: lowPath, suffix: '.json');
	}

	replace Function is paintLine(DrawContext is ctx, Theme is theme, Int is x, Int is y, String is lineStr, Int is fpx){
		local Int is len: lineStr:length();
		local Int is i: 0;
		local Int is curX: x;
		while({ i < len }, {
			local Int is b: lineStr:byteAt(index: i) & 255;
			if({ b == 34 }, {
				local Int is j: i + 1;
				local Boolean is closedStr: false;
				while({ j < len && !closedStr }, {
					local Int is ch: lineStr:byteAt(index: j) & 255;
					if({ ch == 92 && j + 1 < len }, {
						j: j + 2;
					}, {
						if({ ch == 34 }, {
							j: j + 1;
							closedStr: true;
						}, {
							j: j + 1;
						});
					});
				});
				local Int is k: j;
				while({ k < len && ((lineStr:byteAt(index: k) & 255) == 32 || (lineStr:byteAt(index: k) & 255) == 9) }, {
					k: k + 1;
				});
				local Boolean is isKey: k < len && (lineStr:byteAt(index: k) & 255) == 58;
				if({ isKey }, {
					curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synType, fpx: fpx, bold: true, italic: false);
				}, {
					curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synString, fpx: fpx, bold: false, italic: true);
				});
				i: j;
			}, {
			if({ isDigit(b: b) || (b == 45 && i + 1 < len && isDigit(b: lineStr:byteAt(index: i + 1) & 255)) }, {
				local Int is j: i + 1;
				local Boolean is stopNum: false;
				while({ j < len && !stopNum }, {
					local Int is nb: lineStr:byteAt(index: j) & 255;
					if({ isDigit(b: nb) || nb == 46 || nb == 101 || nb == 69 || nb == 43 || nb == 45 }, {
						j: j + 1;
					}, {
						stopNum: true;
					});
				});
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synNumber, fpx: fpx, bold: false, italic: false);
				i: j;
			}, {
			if({ isAlpha(b: b) }, {
				local Int is j: i + 1;
				while({ j < len && isIdentChar(b: lineStr:byteAt(index: j) & 255) }, {
					j: j + 1;
				});
				local String is word: lineStr:substring(start: i, end: j);
				if({ word == 'true' || word == 'false' || word == 'null' }, {
					curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: word, color: theme:synKeyword, fpx: fpx, bold: true, italic: false);
				}, {
					curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: word, color: theme:textPrimary, fpx: fpx, bold: false, italic: false);
				});
				i: j;
			}, {
			if({ b == 123 || b == 125 || b == 91 || b == 93 || b == 58 || b == 44 }, {
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: i + 1), color: theme:synPunct, fpx: fpx, bold: false, italic: false);
				i: i + 1;
			}, {
				local Int is j: i + 1;
				local Boolean is stopPlain: false;
				while({ j < len && !stopPlain }, {
					local Int is nb: lineStr:byteAt(index: j) & 255;
					if({ nb == 34 || isDigit(b: nb) || nb == 45 || isAlpha(b: nb) || nb == 123 || nb == 125 || nb == 91 || nb == 93 || nb == 58 || nb == 44 }, {
						stopPlain: true;
					}, {
						j: j + 1;
					});
				});
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:textPrimary, fpx: fpx, bold: false, italic: false);
				i: j;
			}); }); }); });
		});
	}
}
