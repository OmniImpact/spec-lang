#! Package base:scrap
#! Syntax highlighter for CSS stylesheets (`.css`), inheriting `Highlighter`.

Class of Highlighter is HighlighterCss{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', 'highlighter', Highlighter]
	];

	String is valueKeywords: ' auto block both center collapse contain cover fixed flex grid hidden inherit initial inline inline-block inline-flex italic left none normal nowrap pointer relative repeat right round scroll solid space-between space-around static sticky transparent underline uppercase lowercase ';

	replace Function of String is languageId(){
		return 'css';
	}

	replace Function of String is displayName(){
		return 'CSS';
	}

	replace Function of Highlighter is clone(){
		return HighlighterCss() as Highlighter;
	}

	replace Function of Boolean is matchesExtension(String is lowPath){
		return endsWith(s: lowPath, suffix: '.css');
	}

	local Function of Boolean is isHexDigit(Int is b){
		return isDigit(b: b) || (b >= 65 && b <= 70) || (b >= 97 && b <= 102);
	}

	local Function of Boolean is isCssIdentStart(Int is b){
		return isAlpha(b: b) || b == 45;
	}

	local Function of Boolean is isCssIdentChar(Int is b){
		return isIdentChar(b: b) || b == 45;
	}

	local Function of Boolean is isCssPunct(Int is b){
		return b == 123 || b == 125 || b == 91 || b == 93 || b == 40 || b == 41 || b == 58 || b == 59 || b == 44 || b == 46;
	}

	replace Function is paintLine(DrawContext is ctx, Theme is theme, Int is x, Int is y, String is lineStr, Int is fpx){
		local Int is len: lineStr:length();
		local Int is i: 0;
		local Int is curX: x;
		while({ i < len }, {
			local Int is b: lineStr:byteAt(index: i) & 255;
			if({ b == 47 && i + 1 < len && (lineStr:byteAt(index: i + 1) & 255) == 42 }, {
				local Int is j: i + 2;
				local Boolean is closedCmt: false;
				while({ j < len && !closedCmt }, {
					if({ j + 1 < len && (lineStr:byteAt(index: j) & 255) == 42 && (lineStr:byteAt(index: j + 1) & 255) == 47 }, {
						j: j + 2;
						closedCmt: true;
					}, {
						j: j + 1;
					});
				});
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synComment, fpx: fpx, bold: false, italic: true);
				i: j;
			}, {
			if({ b == 34 || b == 39 }, {
				local Int is q: b;
				local Int is j: i + 1;
				local Boolean is closedStr: false;
				while({ j < len && !closedStr }, {
					local Int is ch: lineStr:byteAt(index: j) & 255;
					if({ ch == 92 && j + 1 < len }, {
						j: j + 2;
					}, {
						if({ ch == q }, {
							j: j + 1;
							closedStr: true;
						}, {
							j: j + 1;
						});
					});
				});
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synString, fpx: fpx, bold: false, italic: true);
				i: j;
			}, {
			if({ b == 64 || b == 33 }, {
				local Int is j: i + 1;
				while({ j < len && :isCssIdentChar(b: lineStr:byteAt(index: j) & 255) }, {
					j: j + 1;
				});
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synKeyword, fpx: fpx, bold: true, italic: false);
				i: j;
			}, {
			if({ b == 35 && i + 1 < len && :isHexDigit(b: lineStr:byteAt(index: i + 1) & 255) }, {
				local Int is j: i + 1;
				while({ j < len && :isHexDigit(b: lineStr:byteAt(index: j) & 255) }, {
					j: j + 1;
				});
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synNumber, fpx: fpx, bold: false, italic: false);
				i: j;
			}, {
			if({ isDigit(b: b) }, {
				local Int is j: i + 1;
				while({ j < len && (isDigit(b: lineStr:byteAt(index: j) & 255) || (lineStr:byteAt(index: j) & 255) == 46) }, {
					j: j + 1;
				});
				while({ j < len && (isAlpha(b: lineStr:byteAt(index: j) & 255) || (lineStr:byteAt(index: j) & 255) == 37) }, {
					j: j + 1;
				});
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synNumber, fpx: fpx, bold: false, italic: false);
				i: j;
			}, {
			if({ :isCssIdentStart(b: b) }, {
				local Int is j: i + 1;
				while({ j < len && :isCssIdentChar(b: lineStr:byteAt(index: j) & 255) }, {
					j: j + 1;
				});
				local String is word: lineStr:substring(start: i, end: j);
				local Int is k: j;
				while({ k < len && (lineStr:byteAt(index: k) & 255) == 32 }, {
					k: k + 1;
				});
				if({ k < len && (lineStr:byteAt(index: k) & 255) == 58 }, {
					curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: word, color: theme:synType, fpx: fpx, bold: true, italic: false);
				}, {
					if({ valueKeywords:contains(needle: ' ' . word . ' ') }, {
						curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: word, color: theme:synKeyword, fpx: fpx, bold: true, italic: false);
					}, {
						curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: word, color: theme:textPrimary, fpx: fpx, bold: false, italic: false);
					});
				});
				i: j;
			}, {
			if({ :isCssPunct(b: b) }, {
				local Int is j: i + 1;
				local Boolean is keepPunct: true;
				while({ j < len && keepPunct }, {
					if({ :isCssPunct(b: lineStr:byteAt(index: j) & 255) }, {
						j: j + 1;
					}, {
						keepPunct: false;
					});
				});
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synPunct, fpx: fpx, bold: false, italic: false);
				i: j;
			}, {
				local Int is j: i + 1;
				local Boolean is stopPlain: false;
				while({ j < len && !stopPlain }, {
					local Int is nb: lineStr:byteAt(index: j) & 255;
					if({ nb == 47 || nb == 34 || nb == 39 || nb == 64 || nb == 33 || nb == 35 || isDigit(b: nb) || :isCssIdentStart(b: nb) || :isCssPunct(b: nb) }, {
						stopPlain: true;
					}, {
						j: j + 1;
					});
				});
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:textPrimary, fpx: fpx, bold: false, italic: false);
				i: j;
			}); }); }); }); }); }); });
		});
	}
}
