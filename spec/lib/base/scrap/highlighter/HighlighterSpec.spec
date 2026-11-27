#! Package base:scrap
#! Syntax highlighter for Spec source files (`.spec`), inheriting `Highlighter`.

Class of Highlighter is HighlighterSpec{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', 'highlighter', Highlighter]
	];

	replace Function of String is languageId(){
		return 'spec';
	}

	replace Function of String is displayName(){
		return 'Spec';
	}

	replace Function of Highlighter is clone(){
		return HighlighterSpec() as Highlighter;
	}

	replace Function of Boolean is matchesExtension(String is lowPath){
		return endsWith(s: lowPath, suffix: '.spec');
	}

	local Function of Boolean is isKeyword(String is w){
		return w == 'Class' || w == 'Enum' || w == 'Function' || w == 'replace' || w == 'held'
			|| w == 'local' || w == 'is' || w == 'of' || w == 'to' || w == 'as'
			|| w == 'return' || w == 'if' || w == 'while' || w == 'match'
			|| w == 'true' || w == 'false' || w == 'null' || w == 'namespace' || w == 'using';
	}

	replace Function is paintLine(DrawContext is ctx, Theme is theme, Int is x, Int is y, String is lineStr, Int is fpx){
		local Int is len: lineStr:length();
		local Int is i: 0;
		local Int is curX: x;
		while({ i < len }, {
			local Int is b: lineStr:byteAt(index: i) & 255;
			if({ b == 35 }, {
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: len), color: theme:synComment, fpx: fpx, bold: false, italic: true);
				return;
			});
			if({ b == 39 }, {
				local Int is j: i + 1;
				local Boolean is closedStr: false;
				while({ j < len && !closedStr }, {
					local Int is ch: lineStr:byteAt(index: j) & 255;
					if({ ch == 92 && j + 1 < len }, {
						j: j + 2;
					}, {
						if({ ch == 39 }, {
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
			if({ isDigit(b: b) }, {
				local Int is j: i + 1;
				while({ j < len && (isDigit(b: lineStr:byteAt(index: j) & 255) || (lineStr:byteAt(index: j) & 255) == 46) }, {
					j: j + 1;
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
				if({ :isKeyword(w: word) }, {
					curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: word, color: theme:synKeyword, fpx: fpx, bold: true, italic: false);
				}, {
					if({ b >= 65 && b <= 90 }, {
						curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: word, color: theme:synType, fpx: fpx, bold: true, italic: false);
					}, {
						curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: word, color: theme:textPrimary, fpx: fpx, bold: false, italic: false);
					});
				});
				i: j;
			}, {
			if({ b == 123 || b == 125 || b == 91 || b == 93 || b == 40 || b == 41 || b == 58 || b == 59 || b == 44 || b == 46 }, {
				local Int is j: i + 1;
				local Boolean is keepPunct: true;
				while({ j < len && keepPunct }, {
					local Int is pb: lineStr:byteAt(index: j) & 255;
					if({ pb == 123 || pb == 125 || pb == 91 || pb == 93 || pb == 40 || pb == 41 || pb == 58 || pb == 59 || pb == 44 || pb == 46 }, {
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
					if({ nb == 35 || nb == 39 || isDigit(b: nb) || isAlpha(b: nb) || nb == 123 || nb == 125 || nb == 91 || nb == 93 || nb == 40 || nb == 41 || nb == 58 || nb == 59 || nb == 44 || nb == 46 }, {
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
