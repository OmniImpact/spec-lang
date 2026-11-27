#! Package base:scrap
#! Data-driven syntax highlighter base for tag-based markup languages (HTML, XML), inheriting `Highlighter`.

Class of Highlighter is MarkupHighlighter{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', 'highlighter', Highlighter]
	];

	String is langId: 'xml';
	String is langDisplay: 'XML';
	Array of String is extensions: Array();

	replace Function is init(
		String is langId: 'xml',
		String is langDisplay: 'XML',
		Array of String is extensions: Array()
	){
		:langId: langId;
		:langDisplay: langDisplay;
		:extensions: extensions;
	}

	replace Function of String is languageId(){
		return langId;
	}

	replace Function of String is displayName(){
		return langDisplay;
	}

	replace Function of Boolean is matchesExtension(String is lowPath){
		local Int is i: 0;
		while({ i < extensions:length() }, {
			if({ endsWith(s: lowPath, suffix: extensions:get(index: i)) }, { return true; });
			i: i + 1;
		});
		return false;
	}

	replace Function of Highlighter is clone(){
		return MarkupHighlighter(
			langId: langId,
			langDisplay: langDisplay,
			extensions: extensions
		) as Highlighter;
	}

	local Function of Boolean is isTagNameChar(Int is b){
		return isIdentChar(b: b) || b == 45 || b == 58 || b == 46;
	}

	replace Function is paintLine(DrawContext is ctx, Theme is theme, Int is x, Int is y, String is lineStr, Int is fpx){
		local Int is len: lineStr:length();
		local Int is i: 0;
		local Int is curX: x;
		while({ i < len }, {
			local Int is b: lineStr:byteAt(index: i) & 255;
			if({ b == 60 }, {
				## <!-- comment -->
				if({ i + 3 < len && (lineStr:byteAt(index: i + 1) & 255) == 33 && (lineStr:byteAt(index: i + 2) & 255) == 45 && (lineStr:byteAt(index: i + 3) & 255) == 45 }, {
					local Int is j: i + 4;
					local Boolean is closedCmt: false;
					while({ j < len && !closedCmt }, {
						if({ j + 2 < len && (lineStr:byteAt(index: j) & 255) == 45 && (lineStr:byteAt(index: j + 1) & 255) == 45 && (lineStr:byteAt(index: j + 2) & 255) == 62 }, {
							j: j + 3;
							closedCmt: true;
						}, {
							j: j + 1;
						});
					});
					curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synComment, fpx: fpx, bold: false, italic: true);
					i: j;
				}, {
					## Opening bracket: <, </, <?, <!
					local Int is openEnd: i + 1;
					if({ openEnd < len }, {
						local Int is nb: lineStr:byteAt(index: openEnd) & 255;
						if({ nb == 47 || nb == 63 || nb == 33 }, {
							openEnd: openEnd + 1;
						});
					});
					curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: openEnd), color: theme:synPunct, fpx: fpx, bold: false, italic: false);
					i: openEnd;

					## Tag name
					if({ i < len && :isTagNameChar(b: lineStr:byteAt(index: i) & 255) }, {
						local Int is tj: i + 1;
						while({ tj < len && :isTagNameChar(b: lineStr:byteAt(index: tj) & 255) }, {
							tj: tj + 1;
						});
						curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: tj), color: theme:synKeyword, fpx: fpx, bold: true, italic: false);
						i: tj;
					});

					## Attributes until > or end of line
					local Boolean is inTag: true;
					while({ i < len && inTag }, {
						local Int is tb: lineStr:byteAt(index: i) & 255;
						if({ tb == 62 }, {
							curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: '>', color: theme:synPunct, fpx: fpx, bold: false, italic: false);
							i: i + 1;
							inTag: false;
						}, {
						if({ (tb == 47 || tb == 63) && i + 1 < len && (lineStr:byteAt(index: i + 1) & 255) == 62 }, {
							curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: i + 2), color: theme:synPunct, fpx: fpx, bold: false, italic: false);
							i: i + 2;
							inTag: false;
						}, {
						if({ tb == 34 || tb == 39 }, {
							local Int is q: tb;
							local Int is sj: i + 1;
							local Boolean is closedStr: false;
							while({ sj < len && !closedStr }, {
								local Int is ch: lineStr:byteAt(index: sj) & 255;
								if({ ch == q }, {
									sj: sj + 1;
									closedStr: true;
								}, {
									sj: sj + 1;
								});
							});
							curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: sj), color: theme:synString, fpx: fpx, bold: false, italic: true);
							i: sj;
						}, {
						if({ :isTagNameChar(b: tb) }, {
							local Int is aj: i + 1;
							while({ aj < len && :isTagNameChar(b: lineStr:byteAt(index: aj) & 255) }, {
								aj: aj + 1;
							});
							curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: aj), color: theme:synType, fpx: fpx, bold: true, italic: false);
							i: aj;
						}, {
						if({ tb == 61 }, {
							curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: '=', color: theme:synPunct, fpx: fpx, bold: false, italic: false);
							i: i + 1;
						}, {
							local Int is wj: i + 1;
							local Boolean is stopWs: false;
							while({ wj < len && !stopWs }, {
								local Int is wb: lineStr:byteAt(index: wj) & 255;
								if({ wb == 62 || wb == 47 || wb == 63 || wb == 34 || wb == 39 || wb == 61 || :isTagNameChar(b: wb) }, {
									stopWs: true;
								}, {
									wj: wj + 1;
								});
							});
							curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: wj), color: theme:textPrimary, fpx: fpx, bold: false, italic: false);
							i: wj;
						}); }); }); }); });
					});
				});
			}, {
			if({ b == 38 }, {
				local Int is ej: i + 1;
				while({ ej < len && ej < i + 16 && (isIdentChar(b: lineStr:byteAt(index: ej) & 255) || (lineStr:byteAt(index: ej) & 255) == 35) }, {
					ej: ej + 1;
				});
				if({ ej < len && (lineStr:byteAt(index: ej) & 255) == 59 }, {
					ej: ej + 1;
					curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: ej), color: theme:synNumber, fpx: fpx, bold: false, italic: false);
					i: ej;
				}, {
					curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: '&', color: theme:textPrimary, fpx: fpx, bold: false, italic: false);
					i: i + 1;
				});
			}, {
				local Int is pj: i + 1;
				local Boolean is stopPlain: false;
				while({ pj < len && !stopPlain }, {
					local Int is pb: lineStr:byteAt(index: pj) & 255;
					if({ pb == 60 || pb == 38 }, {
						stopPlain: true;
					}, {
						pj: pj + 1;
					});
				});
				curX: drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: pj), color: theme:textPrimary, fpx: fpx, bold: false, italic: false);
				i: pj;
			}); });
		});
	}
}
