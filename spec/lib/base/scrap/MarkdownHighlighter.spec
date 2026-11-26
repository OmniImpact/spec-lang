#! Package base:scrap
#! Syntax highlighter for Markdown files (`.md`, `.markdown`), inheriting `ScrapHighlighter`.

Class of ScrapHighlighter is MarkdownHighlighter{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', ScrapHighlighter]
	];

	replace Function of String is languageId(){
		return 'markdown';
	}

	replace Function of String is displayName(){
		return 'Markdown';
	}

	replace Function of Boolean is matchesExtension(String is lowPath){
		return endsWith(s: lowPath, suffix: '.md') || endsWith(s: lowPath, suffix: '.markdown');
	}

	replace Function is paintLine(DrawContext is ctx, Theme is theme, Int is x, Int is y, String is lineStr, Int is fpx){
		local Int is len: lineStr:length();
		local Int is lead: 0;
		while({ lead < len && ((lineStr:byteAt(index: lead) & 255) == 32 || (lineStr:byteAt(index: lead) & 255) == 9) }, {
			lead: lead + 1;
		});
		if({ lead < len }, {
			local Int is fb: lineStr:byteAt(index: lead) & 255;
			if({ fb == 35 }, {
				drawSpan(ctx: ctx, curX: x, y: y, seg: lineStr, color: theme:synHeading, fpx: fpx, bold: true, italic: false);
				return;
			});
			if({ fb == 62 }, {
				drawSpan(ctx: ctx, curX: x, y: y, seg: lineStr, color: theme:synComment, fpx: fpx, bold: false, italic: true);
				return;
			});
			if({ len - lead >= 3 && lineStr:substring(start: lead, end: lead + 3) == '```' }, {
				drawSpan(ctx: ctx, curX: x, y: y, seg: lineStr, color: theme:synString, fpx: fpx, bold: false, italic: true);
				return;
			});
		});

		local Int is i: 0;
		local Int is curX: x;
		if({ lead < len && ((lineStr:byteAt(index: lead) & 255) == 45 || (lineStr:byteAt(index: lead) & 255) == 42) && lead + 1 < len && (lineStr:byteAt(index: lead + 1) & 255) == 32 }, {
			curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: 0, end: lead + 2), color: theme:synType, fpx: fpx, bold: true, italic: false);
			i: lead + 2;
		});

		while({ i < len }, {
			local Int is b: lineStr:byteAt(index: i) & 255;
			if({ b == 96 }, {
				local Int is j: i + 1;
				while({ j < len && (lineStr:byteAt(index: j) & 255) != 96 }, { j: j + 1; });
				if({ j < len }, { j: j + 1; });
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synString, fpx: fpx, bold: false, italic: false);
				i: j;
			}, {
			if({ (b == 42 || b == 95) && i + 1 < len && (lineStr:byteAt(index: i + 1) & 255) == b }, {
				local Int is j: i + 2;
				while({ j + 1 < len && !((lineStr:byteAt(index: j) & 255) == b && (lineStr:byteAt(index: j + 1) & 255) == b) }, { j: j + 1; });
				if({ j + 1 < len }, { j: j + 2; }, { j: len; });
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synKeyword, fpx: fpx, bold: true, italic: false);
				i: j;
			}, {
			if({ b == 42 || b == 95 }, {
				local Int is j: i + 1;
				while({ j < len && (lineStr:byteAt(index: j) & 255) != b }, { j: j + 1; });
				if({ j < len }, { j: j + 1; });
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synComment, fpx: fpx, bold: false, italic: true);
				i: j;
			}, {
			if({ b == 91 || b == 93 || b == 40 || b == 41 }, {
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: i + 1), color: theme:synPunct, fpx: fpx, bold: false, italic: false);
				i: i + 1;
			}, {
				local Int is j: i + 1;
				local Boolean is stopMd: false;
				while({ j < len && !stopMd }, {
					local Int is nb: lineStr:byteAt(index: j) & 255;
					if({ nb == 96 || nb == 42 || nb == 95 || nb == 91 || nb == 93 || nb == 40 || nb == 41 }, {
						stopMd: true;
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
