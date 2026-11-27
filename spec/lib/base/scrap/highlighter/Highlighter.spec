#! Package base:scrap
#! Common interface and shared drawing/scanning helpers for pluggable syntax highlighters in `CodeEditorView`.

Class is Highlighter{
	replace [String] is namespace: ['base', 'scrap', 'highlighter'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Mem()],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext]
	];

	Boolean is monoMode: false;
	Boolean is measureOnly: false;
	Boolean is advOnly: false;
	Int is advOutPtr: 0;
	Int is advScratchPtr: 0;
	Int is advTmpPtr: 0;
	Int is advTmpCap: 0;
	Int is measureTargetCol: 0;
	Int is measureColPos: 0;
	Int is measureResultX: 0;

	Function is dispose(){
		if({ advTmpPtr != 0 }, {
			Mem:free(ptr: advTmpPtr);
			:advTmpPtr: 0;
			:advTmpCap: 0;
		});
	}

	Function is destroy(){
		:dispose();
	}

	Function of String is languageId(){
		return 'plain';
	}

	Function of String is displayName(){
		return 'Plain Text';
	}

	## Returns a fresh instance of this highlighter for worker-thread wrapping/measurement.
	Function of Highlighter is clone(){
		return Highlighter();
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
		if({ advOnly }, {
			local Int is slen: seg:length();
			local Int is needBytes: (slen + 1) * 4;
			if({ needBytes > advTmpCap }, {
				local Int is nextCap: if({ advTmpCap > 0 }, { advTmpCap * 2 }, { 256 });
				while({ nextCap < needBytes }, { nextCap: nextCap * 2; });
				if({ advTmpPtr != 0 }, {
					:advTmpPtr: Mem:realloc(ptr: advTmpPtr, bytes: nextCap);
				}, {
					:advTmpPtr: Mem:alloc(bytes: nextCap);
				});
				:advTmpCap: nextCap;
			});
			ctx:measurePrefixAdvances(text: seg, pixelHeight: fpx, bold: bold, italic: italic, mono: monoMode, outAdvI32Ptr: advTmpPtr, scratchPtr: advScratchPtr);
			local Int is si: 1;
			while({ si <= slen }, {
				local Int is v: curX + Mem:loadI32(ptr: advTmpPtr, byteOffset: si * 4);
				Mem:storeI32(ptr: advOutPtr, byteOffset: (measureColPos + si) * 4, val: v);
				si: si + 1;
			});
			local Int is endX: curX + Mem:loadI32(ptr: advTmpPtr, byteOffset: slen * 4);
			:measureColPos: measureColPos + slen;
			return endX;
		});
		if({ measureOnly }, {
			if({ measureColPos >= measureTargetCol }, { return curX; });
			local Int is segLen: seg:length();
			local Int is remaining: measureTargetCol - measureColPos;
			if({ remaining < segLen }, {
				local String is part: seg:substring(start: 0, end: remaining);
				local Int is partW: ctx:measureTextWidth(text: part, pixelHeight: fpx, bold: bold, italic: italic, mono: monoMode);
				:measureColPos: measureTargetCol;
				:measureResultX: curX + partW;
				return curX + partW;
			});
			local Int is fullW: ctx:measureTextWidth(text: seg, pixelHeight: fpx, bold: bold, italic: italic, mono: monoMode);
			:measureColPos: measureColPos + segLen;
			:measureResultX: curX + fullW;
			return curX + fullW;
		});
		return curX + ctx:drawTextAdvance(x: curX, y: y, text: seg, color: color, pixelHeight: fpx, bold: bold, italic: italic, mono: monoMode);
	}

	Function is paintLine(DrawContext is ctx, Theme is theme, Int is x, Int is y, String is lineStr, Int is fpx){
		:drawSpan(ctx: ctx, curX: x, y: y, seg: lineStr, color: theme:textPrimary, fpx: fpx, bold: false, italic: false);
	}

	## Measures pixel X offset at [col] on [lineStr] using the exact styling of `paintLine`.
	Function of Int is measureLinePrefix(DrawContext is ctx, Theme is theme, String is lineStr, Int is fpx, Int is col){
		if({ col <= 0 || lineStr == '' }, { return 0; });
		local Int is target: if({ col > lineStr:length() }, { lineStr:length() }, { col });
		:measureOnly: true;
		:measureTargetCol: target;
		:measureColPos: 0;
		:measureResultX: 0;
		:paintLine(ctx: ctx, theme: theme, x: 0, y: 0, lineStr: lineStr, fpx: fpx);
		:measureOnly: false;
		return measureResultX;
	}

	## Measures cumulative styled pixel X advances for [lineStr] into [outAdvI32Ptr] in a single pass.
	Function is measureLineAdvances(DrawContext is ctx, Theme is theme, String is lineStr, Int is fpx, Int is outAdvI32Ptr, Int is scratchPtr: 0){
		if({ outAdvI32Ptr == 0 }, { return; });
		Mem:storeI32(ptr: outAdvI32Ptr, byteOffset: 0, val: 0);
		if({ lineStr == '' }, { return; });
		:advOnly: true;
		:advOutPtr: outAdvI32Ptr;
		:advScratchPtr: scratchPtr;
		:measureColPos: 0;
		:paintLine(ctx: ctx, theme: theme, x: 0, y: 0, lineStr: lineStr, fpx: fpx);
		:advOnly: false;
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
				curX: :drawSpan(ctx: ctx, curX: curX, y: y, seg: lineStr:substring(start: i, end: j), color: theme:synPunct, fpx: fpx, bold: false, italic: false);
				i: j;
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
