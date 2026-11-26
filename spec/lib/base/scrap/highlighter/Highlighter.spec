#! Package base:scrap
#! Common interface and shared drawing/scanning helpers for pluggable syntax highlighters in `CodeEditorView`.

Class is Highlighter{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext]
	];

	Boolean is monoMode: false;

	Function of String is languageId(){
		return 'plain';
	}

	Function of String is displayName(){
		return 'Plain Text';
	}

	Function of Boolean is matchesExtension(String is lowPath){
		return false;
	}

	Function of Boolean is endsWith(String is s, String is suffix){
		local Int is sl: s:length();
		local Int is fl: suffix:length();
		if({ sl < fl }, { return false; });
		return s:substring(start: sl - fl, end: sl) == suffix;
	}

	Function of Boolean is isAlpha(Int is b){
		return (b >= 65 && b <= 90) || (b >= 97 && b <= 122) || b == 95;
	}

	Function of Boolean is isDigit(Int is b){
		return b >= 48 && b <= 57;
	}

	Function of Boolean is isIdentChar(Int is b){
		return :isAlpha(b: b) || :isDigit(b: b);
	}

	Function of Int is drawSpan(
		DrawContext is ctx,
		Int is curX,
		Int is y,
		String is seg,
		Int is color,
		Int is fpx,
		Boolean is bold: false,
		Boolean is italic: false
	){
		if({ seg == '' }, { return curX; });
		ctx:drawText(x: curX, y: y, text: seg, color: color, pixelHeight: fpx, bold: bold, italic: italic, mono: monoMode);
		return curX + ctx:measureTextWidth(text: seg, pixelHeight: fpx, bold: bold, italic: italic, mono: monoMode);
	}

	Function is paintLine(DrawContext is ctx, Theme is theme, Int is x, Int is y, String is lineStr, Int is fpx){
		ctx:drawText(x: x, y: y, text: lineStr, color: theme:textPrimary, pixelHeight: fpx, mono: monoMode);
	}

	## Shared single-line scanner for C-like and scripting languages parameterized by comment syntax and keyword list.
	Function is paintCodeLine(
		DrawContext is ctx,
		Theme is theme,
		Int is x,
		Int is y,
		String is lineStr,
		Int is fpx,
		String is lineComment,
		Boolean is blockComments,
		String is spaceWrappedKeywords
	){
		local Int is len: lineStr:length();
		local Int is i: 0;
		local Int is curX: x;
		while({ i < len }, {
			local Int is b: lineStr:byteAt(index: i) & 255;
			if({ lineComment == '#' && b == 35 }, {
				curX: :drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: len), color: theme:synComment, fpx: fpx, bold: false, italic: true);
				return;
			});
			if({ lineComment == '//' && b == 47 && i + 1 < len && (lineStr:byteAt(index: i + 1) & 255) == 47 }, {
				curX: :drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: len), color: theme:synComment, fpx: fpx, bold: false, italic: true);
				return;
			});
			if({ blockComments && b == 47 && i + 1 < len && (lineStr:byteAt(index: i + 1) & 255) == 42 }, {
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
				curX: :drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synComment, fpx: fpx, bold: false, italic: true);
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
				curX: :drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synString, fpx: fpx, bold: false, italic: true);
				i: j;
			}, {
			if({ :isDigit(b: b) }, {
				local Int is j: i + 1;
				while({ j < len && (:isIdentChar(b: lineStr:byteAt(index: j) & 255) || (lineStr:byteAt(index: j) & 255) == 46) }, {
					j: j + 1;
				});
				curX: :drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synNumber, fpx: fpx, bold: false, italic: false);
				i: j;
			}, {
			if({ :isAlpha(b: b) }, {
				local Int is j: i + 1;
				while({ j < len && :isIdentChar(b: lineStr:byteAt(index: j) & 255) }, {
					j: j + 1;
				});
				local String is word: lineStr:substring(start: i, end: j);
				if({ spaceWrappedKeywords:contains(needle: ' ' . word . ' ') }, {
					curX: :drawSpan(ctx: ctx, curX: curX, y: y, seg: word, color: theme:synKeyword, fpx: fpx, bold: true, italic: false);
				}, {
					if({ b >= 65 && b <= 90 }, {
						curX: :drawSpan(ctx: ctx, curX: curX, y: y, seg: word, color: theme:synType, fpx: fpx, bold: true, italic: false);
					}, {
						curX: :drawSpan(ctx: ctx, curX: curX, y: y, seg: word, color: theme:textPrimary, fpx: fpx, bold: false, italic: false);
					});
				});
				i: j;
			}, {
			if({ b == 123 || b == 125 || b == 91 || b == 93 || b == 40 || b == 41 || b == 58 || b == 59 || b == 44 || b == 46 }, {
				curX: :drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: i + 1), color: theme:synPunct, fpx: fpx, bold: false, italic: false);
				i: i + 1;
			}, {
				local Int is j: i + 1;
				local Boolean is stopPlain: false;
				while({ j < len && !stopPlain }, {
					local Int is nb: lineStr:byteAt(index: j) & 255;
					if({ nb == 35 || nb == 47 || nb == 34 || nb == 39 || :isDigit(b: nb) || :isAlpha(b: nb) || nb == 123 || nb == 125 || nb == 91 || nb == 93 || nb == 40 || nb == 41 || nb == 58 || nb == 59 || nb == 44 || nb == 46 }, {
						stopPlain: true;
					}, {
						j: j + 1;
					});
				});
				curX: :drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:textPrimary, fpx: fpx, bold: false, italic: false);
				i: j;
			}); }); }); }); });
		});
	}
}
