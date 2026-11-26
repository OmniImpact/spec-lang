#! Package base:scrap
#! Reactive multi-line text view (`SewNode`) with optional wrapping, line numbers, cursor, highlight selection, and copy/cut/paste.

Class of SewNode is TextView{
	replace [String] is namespace: ['base', 'scrap', 'text'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', Font],
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'signal', BoolEmitter],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Constraints],
		['base', 'sew', Rect],
		['base', 'fabric', Color],
		['base', 'fabric', DrawContext]
	];

	TextEmitter is text: TextEmitter(initial: '');
	BoolEmitter is wrap: BoolEmitter(initial: false);
	BoolEmitter is lineNumbers: BoolEmitter(initial: false);
	BoolEmitter is monospace: BoolEmitter(initial: false);
	TextEmitter is cursorStatus: TextEmitter(initial: 'Ln 1, Col 1');
	Function is onTextChange: local Function(String is _next){};
	Function is onRightClickMenu: local Function(Int is _x, Int is _y){};
	Function is onClipboardWrite: local Function(String is _text){};
	Function of String is onClipboardRead: local Function of String(){ '' };
	Float is padPt: 12.0;
	Float is lineGapPt: 4.0;
	Float is docTextDeltaPt: 0.0;

	Array of String is rawLines: Array(['']);
	Array of String is dispLines: Array(['']);
	Array of Int is dispRawLine: Array([0]);
	Array of Int is dispRawStart: Array([0]);
	Int is cursorLine: 0;
	Int is cursorCol: 0;
	Int is selAnchorLine: 0;
	Int is selAnchorCol: 0;
	Boolean is hasSelection: false;
	Boolean is wrapCached: false;
	Boolean is lineNumsCached: false;
	Boolean is monoCached: false;
	Int is lastWrapW: -1;
	Int is maxDispW: 0;
	String is clipboardText: '';
	Boolean is ignoreSelfEmit: false;
	Int is cursorAlphaByte: 255;
	Int is lastBlinkMs: 0;

	replace Function is init(
		TextEmitter is text,
		BoolEmitter is wrap: BoolEmitter(initial: false),
		BoolEmitter is lineNumbers: BoolEmitter(initial: false),
		BoolEmitter is monospace: BoolEmitter(initial: false),
		TextEmitter is cursorStatus: TextEmitter(initial: 'Ln 1, Col 1'),
		Function is onTextChange: local Function(String is _next){},
		Function is onRightClickMenu: local Function(Int is _x, Int is _y){},
		Function is onClipboardWrite: local Function(String is _text){},
		Function of String is onClipboardRead: local Function of String(){ '' },
		Float is padPt: 12.0,
		Float is lineGapPt: 4.0
	){
		:initTextView(
			text: text,
			wrap: wrap,
			lineNumbers: lineNumbers,
			monospace: monospace,
			cursorStatus: cursorStatus,
			onTextChange: onTextChange,
			onRightClickMenu: onRightClickMenu,
			onClipboardWrite: onClipboardWrite,
			onClipboardRead: onClipboardRead,
			padPt: padPt,
			lineGapPt: lineGapPt
		);
	}

	Function is initTextView(
		TextEmitter is text,
		BoolEmitter is wrap: BoolEmitter(initial: false),
		BoolEmitter is lineNumbers: BoolEmitter(initial: false),
		BoolEmitter is monospace: BoolEmitter(initial: false),
		TextEmitter is cursorStatus: TextEmitter(initial: 'Ln 1, Col 1'),
		Function is onTextChange: local Function(String is _next){},
		Function is onRightClickMenu: local Function(Int is _x, Int is _y){},
		Function is onClipboardWrite: local Function(String is _text){},
		Function of String is onClipboardRead: local Function of String(){ '' },
		Float is padPt: 12.0,
		Float is lineGapPt: 4.0
	){
		:text: text;
		:wrap: wrap;
		:lineNumbers: lineNumbers;
		:monospace: monospace;
		:cursorStatus: cursorStatus;
		:onTextChange: onTextChange;
		:onRightClickMenu: onRightClickMenu;
		:onClipboardWrite: onClipboardWrite;
		:onClipboardRead: onClipboardRead;
		:padPt: padPt;
		:lineGapPt: lineGapPt;
		:wrapCached: wrap:current();
		:lineNumsCached: lineNumbers:current();
		:monoCached: monospace:current();
		:rebuildRawLines(raw: text:current());
		:emitCursorStatus();

		signalBag:track(
			slot: 'text',
			emitter: text,
			collector: text:collect(onEmit: local Function(String is next){
				if({ ignoreSelfEmit }, {
					ignoreSelfEmit: false;
					return;
				});
				:rebuildRawLines(raw: next);
				:cursorLine: 0;
				:cursorCol: 0;
				:hasSelection: false;
				:emitCursorStatus();
				invalidate();
			})
		);
		signalBag:track(
			slot: 'wrap',
			emitter: wrap,
			collector: wrap:collect(onEmit: local Function(){
				:wrapCached: wrap:current();
				:lastWrapW: -1;
				invalidate();
			})
		);
		signalBag:track(
			slot: 'lineNumbers',
			emitter: lineNumbers,
			collector: lineNumbers:collect(onEmit: local Function(){
				:lineNumsCached: lineNumbers:current();
				:lastWrapW: -1;
				invalidate();
			})
		);
		signalBag:track(
			slot: 'monospace',
			emitter: monospace,
			collector: monospace:collect(onEmit: local Function(){
				:monoCached: monospace:current();
				:lastWrapW: -1;
				invalidate();
			})
		);
	}

	Function is setDocTextDeltaPt(Float is deltaPt){
		:docTextDeltaPt: deltaPt;
		:lastWrapW: -1;
		invalidate();
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		:lastWrapW: -1;
	}

	local Function of Int is fontPx(){
		local Float is docPt: activeTheme:scaledTextPt(defaultPt: 18.0) + docTextDeltaPt;
		local Float is clampedPt: if({ docPt < 8.0 }, { 8.0 }, { docPt });
		local Int is px: activeScale:px(pt: clampedPt);
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Int is measureStr(String is s, Int is fpx){
		if({ s == '' }, { return 0; });
		return DrawContext:shared:measureTextWidth(text: s, pixelHeight: fpx, mono: monoCached);
	}

	local Function of Int is gutterWidthPx(Int is fpx){
		if({ !lineNumsCached }, { return 0; });
		local Int is n: rawLines:length();
		local String is sample: '' . n;
		if({ sample:length() < 3 }, { sample: '999'; });
		return :measureStr(s: sample, fpx: fpx) + activeScale:px(pt: 18.0);
	}

	local Function is emitCursorStatus(){
		cursorStatus:emit(value: 'Ln ' . (cursorLine + 1) . ', Col ' . (cursorCol + 1));
	}

	local Function is rebuildRawLines(String is raw){
		rawLines: Array();
		local Int is len: raw:length();
		if({ len == 0 }, {
			rawLines:add(item: '');
			lastWrapW: -1;
			return;
		});
		local Int is start: 0;
		local Int is i: 0;
		while({ i < len }, {
			local Int is ch: raw:byteAt(index: i);
			if({ ch == 10 }, {
				local Int is endIdx: i;
				if({ endIdx > start && raw:byteAt(index: endIdx - 1) == 13 }, {
					endIdx: endIdx - 1;
				});
				rawLines:add(item: raw:substring(start: start, end: endIdx));
				start: i + 1;
			});
			i: i + 1;
		});
		if({ start <= len }, {
			local Int is endIdx: len;
			if({ endIdx > start && raw:byteAt(index: endIdx - 1) == 13 }, {
				endIdx: endIdx - 1;
			});
			rawLines:add(item: raw:substring(start: start, end: endIdx));
		});
		if({ rawLines:length() == 0 }, { rawLines:add(item: ''); });
		lastWrapW: -1;
	}

	local Function is rebuildDisplayLines(Int is availTextW, Int is fpx){
		dispLines: Array();
		dispRawLine: Array();
		dispRawStart: Array();
		maxDispW: 0;
		local Int is rcount: rawLines:length();
		local Int is r: 0;
		while({ r < rcount }, {
			local String is line: rawLines:get(index: r);
			if({ !wrapCached || availTextW <= fpx || line == '' }, {
				dispLines:add(item: line);
				dispRawLine:add(item: r);
				dispRawStart:add(item: 0);
				local Int is lw: :measureStr(s: line, fpx: fpx);
				if({ lw > maxDispW }, { maxDispW: lw; });
			}, {
				local Int is len: line:length();
				local Int is pos: 0;
				while({ pos < len }, {
					local Int is endPos: pos + 1;
					local Int is lastSpace: -1;
					local Boolean is fit: true;
					while({ endPos <= len && fit }, {
						local String is sub: line:substring(start: pos, end: endPos);
						if({ :measureStr(s: sub, fpx: fpx) > availTextW && endPos > pos + 1 }, {
							fit: false;
						}, {
							if({ line:byteAt(index: endPos - 1) == 32 }, { lastSpace: endPos; });
							endPos: endPos + 1;
						});
					});
					local Int is segEnd: endPos - 1;
					if({ segEnd < len && lastSpace > pos }, {
						segEnd: lastSpace;
					});
					if({ segEnd <= pos }, { segEnd: pos + 1; });
					local String is seg: line:substring(start: pos, end: segEnd);
					dispLines:add(item: seg);
					dispRawLine:add(item: r);
					dispRawStart:add(item: pos);
					local Int is sw: :measureStr(s: seg, fpx: fpx);
					if({ sw > maxDispW }, { maxDispW: sw; });
					pos: segEnd;
				});
			});
			r: r + 1;
		});
		lastWrapW: availTextW;
	}

	local Function of String is joinRawLines(){
		local String is out: '';
		local Int is i: 0;
		local Int is n: rawLines:length();
		while({ i < n }, {
			if({ i > 0 }, { out: out . '\n'; });
			out: out . rawLines:get(index: i);
			i: i + 1;
		});
		return out;
	}

	local Function is notifyEdited(){
		local String is joined: :joinRawLines();
		lastWrapW: -1;
		ignoreSelfEmit: true;
		text:emit(value: joined);
		local Function is cb: onTextChange;
		cb(joined);
		:emitCursorStatus();
		cursorAlphaByte: 255;
		lastBlinkMs: 0;
		invalidate();
	}

	local Function of Boolean is hasNonEmptySelection(){
		return hasSelection && (selAnchorLine != cursorLine || selAnchorCol != cursorCol);
	}

	local Function of Array of Int is orderedSelection(){
		local Int is sl: selAnchorLine;
		local Int is sc: selAnchorCol;
		local Int is el: cursorLine;
		local Int is ec: cursorCol;
		if({ sl > el || (sl == el && sc > ec) }, {
			return Array([el, ec, sl, sc]);
		});
		return Array([sl, sc, el, ec]);
	}

	## Returns the currently highlighted text, or `''` if nothing is selected.
	Function of String is selectedText(){
		if({ !:hasNonEmptySelection() }, { return ''; });
		local Array of Int is r: :orderedSelection();
		local Int is sl: r:get(index: 0);
		local Int is sc: r:get(index: 1);
		local Int is el: r:get(index: 2);
		local Int is ec: r:get(index: 3);
		if({ sl == el }, {
			return rawLines:get(index: sl):substring(start: sc, end: ec);
		});
		local String is out: rawLines:get(index: sl):substring(start: sc, end: rawLines:get(index: sl):length());
		local Int is i: sl + 1;
		while({ i < el }, {
			out: out . '\n' . rawLines:get(index: i);
			i: i + 1;
		});
		out: out . '\n' . rawLines:get(index: el):substring(start: 0, end: ec);
		return out;
	}

	local Function is replaceSelection(String is replacement){
		local Int is sl: cursorLine;
		local Int is sc: cursorCol;
		local Int is el: cursorLine;
		local Int is ec: cursorCol;
		if({ :hasNonEmptySelection() }, {
			local Array of Int is r: :orderedSelection();
			sl: r:get(index: 0);
			sc: r:get(index: 1);
			el: r:get(index: 2);
			ec: r:get(index: 3);
		});
		local String is prefix: rawLines:get(index: sl):substring(start: 0, end: sc);
		local String is suffix: rawLines:get(index: el):substring(start: ec, end: rawLines:get(index: el):length());
		local String is combined: prefix . replacement . suffix;

		## Split replacement to find final cursor line/col
		local Int is repLines: 0;
		local Int is lastNl: -1;
		local Int is k: 0;
		while({ k < replacement:length() }, {
			if({ replacement:byteAt(index: k) == 10 }, {
				repLines: repLines + 1;
				lastNl: k;
			});
			k: k + 1;
		});

		## Rebuild rawLines with [sl..el] replaced by split(combined)
		local Array of String is nextRaw: Array();
		local Int is i: 0;
		while({ i < sl }, {
			nextRaw:add(item: rawLines:get(index: i));
			i: i + 1;
		});
		local Int is start: 0;
		local Int is j: 0;
		while({ j < combined:length() }, {
			if({ combined:byteAt(index: j) == 10 }, {
				local Int is endIdx: j;
				if({ endIdx > start && combined:byteAt(index: endIdx - 1) == 13 }, { endIdx: endIdx - 1; });
				nextRaw:add(item: combined:substring(start: start, end: endIdx));
				start: j + 1;
			});
			j: j + 1;
		});
		nextRaw:add(item: combined:substring(start: start, end: combined:length()));
		i: el + 1;
		while({ i < rawLines:length() }, {
			nextRaw:add(item: rawLines:get(index: i));
			i: i + 1;
		});
		rawLines: nextRaw;

		cursorLine: sl + repLines;
		if({ repLines == 0 }, {
			cursorCol: sc + replacement:length();
		}, {
			cursorCol: replacement:length() - (lastNl + 1);
		});
		hasSelection: false;
		:notifyEdited();
	}

	## Returns `true` when there is a non-empty text selection.
	Function of Boolean is hasSelectedText(){
		return :hasNonEmptySelection();
	}

	## Returns `true` when the internal or system clipboard buffer is non-empty.
	Function of Boolean is hasClipboardText(){
		if({ clipboardText != '' }, { return true; });
		local Function of String is readFn: onClipboardRead;
		return readFn() != '';
	}

	## Copies the active selection into the clipboard buffer and returns it.
	Function of String is copySelection(){
		local String is sel: :selectedText();
		if({ sel != '' }, {
			clipboardText: sel;
			local Function is writeFn: onClipboardWrite;
			writeFn(sel);
		});
		return clipboardText;
	}

	## Cuts the active selection into the clipboard buffer and removes it.
	Function of String is cutSelection(){
		local String is sel: :selectedText();
		if({ sel == '' }, { return ''; });
		clipboardText: sel;
		local Function is writeFn: onClipboardWrite;
		writeFn(sel);
		:replaceSelection(replacement: '');
		return clipboardText;
	}

	## Pastes [clip] (or the system/internal clipboard when empty) at the cursor/selection.
	Function is pasteText(String is clip: ''){
		local String is src: clip;
		if({ src == '' }, {
			local Function of String is readFn: onClipboardRead;
			src: readFn();
		});
		if({ src == '' }, { src: clipboardText; });
		if({ src == '' }, { return; });
		:replaceSelection(replacement: src);
	}

	## Selects the entire document.
	Function is selectAll(){
		if({ rawLines:length() == 0 }, { return; });
		selAnchorLine: 0;
		selAnchorCol: 0;
		cursorLine: rawLines:length() - 1;
		cursorCol: rawLines:get(index: cursorLine):length();
		hasSelection: true;
		:emitCursorStatus();
		cursorAlphaByte: 255;
		lastBlinkMs: 0;
		invalidate();
	}

	local Function is moveCursor(Int is line, Int is col, Boolean is extendSel){
		if({ !extendSel }, {
			hasSelection: false;
		}, {
			if({ !hasSelection }, {
				selAnchorLine: cursorLine;
				selAnchorCol: cursorCol;
				hasSelection: true;
			});
		});
		local Int is maxLine: rawLines:length() - 1;
		if({ maxLine < 0 }, { maxLine: 0; });
		local Int is nl: line;
		if({ nl < 0 }, { nl: 0; });
		if({ nl > maxLine }, { nl: maxLine; });
		local Int is maxCol: rawLines:get(index: nl):length();
		local Int is nc: col;
		if({ nc < 0 }, { nc: 0; });
		if({ nc > maxCol }, { nc: maxCol; });
		cursorLine: nl;
		cursorCol: nc;
		if({ extendSel && selAnchorLine == cursorLine && selAnchorCol == cursorCol }, {
			hasSelection: false;
		});
		:emitCursorStatus();
		cursorAlphaByte: 255;
		lastBlinkMs: 0;
		invalidate();
	}

	replace Function of Boolean is tick(Int is nowMs){
		if({ lastBlinkMs == 0 }, {
			lastBlinkMs: nowMs;
			cursorAlphaByte: 255;
			return false;
		});
		local Int is phase: (nowMs - lastBlinkMs) % 1000;
		local Int is nextAlpha: 255;
		if({ phase < 400 }, {
			nextAlpha: 255;
		}, {
		if({ phase < 520 }, {
			nextAlpha: ((520 - phase) * 255) / 120;
		}, {
		if({ phase < 880 }, {
			nextAlpha: 0;
		}, {
			nextAlpha: ((phase - 880) * 255) / 120;
		}); }); });
		if({ nextAlpha < 0 }, { nextAlpha: 0; });
		if({ nextAlpha > 255 }, { nextAlpha: 255; });
		if({ nextAlpha != cursorAlphaByte }, {
			cursorAlphaByte: nextAlpha;
			return true;
		});
		return false;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is fpx: :fontPx();
		local Int is gapPx: activeScale:px(pt: lineGapPt);
		local Int is padPx: activeScale:px(pt: padPt);
		local Int is gw: :gutterWidthPx(fpx: fpx);
		local Int is availTextW: c:maxW - gw - padPx * 2;
		if({ availTextW < fpx }, { availTextW: fpx; });
		if({ lastWrapW == -1 || (wrapCached && lastWrapW != availTextW) }, {
			:rebuildDisplayLines(availTextW: availTextW, fpx: fpx);
		});

		local Int is rowH: fpx + gapPx;
		local Int is totalH: padPx * 2 + dispLines:length() * rowH;
		local Int is neededW: gw + padPx * 2 + maxDispW;
		local Int is outW: if({ !wrapCached && neededW > c:maxW }, { neededW }, { c:maxW });
		desiredSize: Size(width: outW, height: totalH);
		return desiredSize;
	}

	Boolean is selectingDrag: false;

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ !selectingDrag }, {
			local Rect is b: bounds();
			if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return false; });
		});
		return :onPointerClickMod(x: x, y: y, mods: 1);
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		selectingDrag: false;
		return false;
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Rect is b: bounds();
		if({ !selectingDrag && (x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height) }, {
			return false;
		});
		local Int is fpx: :fontPx();
		local Int is gapPx: activeScale:px(pt: lineGapPt);
		local Int is padPx: activeScale:px(pt: padPt);
		local Int is rowH: fpx + gapPx;
		local Int is gw: :gutterWidthPx(fpx: fpx);
		if({ lineNumsCached && gw > 0 && x < b:x + gw }, {
			return false;
		});
		local Int is count: dispLines:length();
		if({ count == 0 || rowH <= 0 }, { return false; });

		local Int is dispIdx: (y - (b:y + padPx)) / rowH;
		if({ dispIdx < 0 }, { dispIdx: 0; });
		if({ dispIdx >= count }, { dispIdx: count - 1; });

		local Int is relX: x - (b:x + gw + padPx);
		local String is seg: dispLines:get(index: dispIdx);
		local Int is bestCol: 0;
		if({ relX > 0 }, {
			local Int is bestDist: relX;
			local Int is c: 1;
			while({ c <= seg:length() }, {
				local Int is w: :measureStr(s: seg:substring(start: 0, end: c), fpx: fpx);
				local Int is d: if({ w >= relX }, { w - relX }, { relX - w });
				if({ d <= bestDist }, {
					bestDist: d;
					bestCol: c;
				});
				c: c + 1;
			});
		});

		local Int is rLine: dispRawLine:get(index: dispIdx);
		local Int is rCol: dispRawStart:get(index: dispIdx) + bestCol;
		selectingDrag: true;
		:moveCursor(line: rLine, col: rCol, extendSel: (mods & 1) != 0);
		return true;
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		local Boolean is shift: (mods & 1) != 0;
		local Boolean is ctrl: (mods & 2) != 0;

		if({ ctrl }, {
			if({ key == 97 || key == 65 || key == 1 }, {
				:selectAll();
				return true;
			});
			if({ key == 99 || key == 67 || key == 3 }, {
				:copySelection();
				return true;
			});
			if({ key == 120 || key == 88 || key == 24 }, {
				:cutSelection();
				return true;
			});
			if({ key == 118 || key == 86 || key == 22 }, {
				:pasteText();
				return true;
			});
			return false;
		});

		if({ key == 1003 }, {
			if({ cursorCol > 0 }, {
				:moveCursor(line: cursorLine, col: cursorCol - 1, extendSel: shift);
			}, {
				if({ cursorLine > 0 }, {
					local Int is prevLen: rawLines:get(index: cursorLine - 1):length();
					:moveCursor(line: cursorLine - 1, col: prevLen, extendSel: shift);
				});
			});
			return true;
		});
		if({ key == 1004 }, {
			local Int is curLen: rawLines:get(index: cursorLine):length();
			if({ cursorCol < curLen }, {
				:moveCursor(line: cursorLine, col: cursorCol + 1, extendSel: shift);
			}, {
				if({ cursorLine + 1 < rawLines:length() }, {
					:moveCursor(line: cursorLine + 1, col: 0, extendSel: shift);
				});
			});
			return true;
		});
		if({ key == 1001 }, {
			:moveCursor(line: cursorLine - 1, col: cursorCol, extendSel: shift);
			return true;
		});
		if({ key == 1002 }, {
			:moveCursor(line: cursorLine + 1, col: cursorCol, extendSel: shift);
			return true;
		});
		if({ key == 1005 }, {
			:moveCursor(line: cursorLine, col: 0, extendSel: shift);
			return true;
		});
		if({ key == 1006 }, {
			:moveCursor(line: cursorLine, col: rawLines:get(index: cursorLine):length(), extendSel: shift);
			return true;
		});
		if({ key == 13 }, {
			:replaceSelection(replacement: '\n');
			return true;
		});
		if({ key == 9 }, {
			:replaceSelection(replacement: '    ');
			return true;
		});
		if({ key == 8 }, {
			if({ :hasNonEmptySelection() }, {
				:replaceSelection(replacement: '');
				return true;
			});
			if({ cursorCol > 0 }, {
				selAnchorLine: cursorLine;
				selAnchorCol: cursorCol - 1;
				hasSelection: true;
				:replaceSelection(replacement: '');
				return true;
			});
			if({ cursorLine > 0 }, {
				selAnchorLine: cursorLine - 1;
				selAnchorCol: rawLines:get(index: cursorLine - 1):length();
				hasSelection: true;
				:replaceSelection(replacement: '');
				return true;
			});
			return true;
		});
		if({ key == 127 }, {
			if({ :hasNonEmptySelection() }, {
				:replaceSelection(replacement: '');
				return true;
			});
			local Int is curLen: rawLines:get(index: cursorLine):length();
			if({ cursorCol < curLen }, {
				selAnchorLine: cursorLine;
				selAnchorCol: cursorCol + 1;
				hasSelection: true;
				:replaceSelection(replacement: '');
				return true;
			});
			if({ cursorLine + 1 < rawLines:length() }, {
				selAnchorLine: cursorLine + 1;
				selAnchorCol: 0;
				hasSelection: true;
				:replaceSelection(replacement: '');
				return true;
			});
			return true;
		});
		return false;
	}

	replace Function of Boolean is onText(String is ch, Int is mods){
		if({ (mods & 2) != 0 || (mods & 4) != 0 || (mods & 8) != 0 }, { return false; });
		if({ ch == '' }, { return false; });
		:replaceSelection(replacement: ch);
		return true;
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		local Function is cb: onRightClickMenu;
		cb(x, y);
		return true;
	}

	## Renders one display line of text; subclasses (e.g. `CodeEditorView`) can override for syntax highlighting.
	Function is paintLineText(DrawContext is ctx, Int is x, Int is y, String is lineStr, Int is rLine, Int is rStart, Int is fpx){
		ctx:drawText(x: x, y: y, text: lineStr, color: activeTheme:textPrimary, pixelHeight: fpx, mono: monoCached);
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		local Int is fpx: :fontPx();
		local Int is gapPx: activeScale:px(pt: lineGapPt);
		local Int is padPx: activeScale:px(pt: padPt);
		local Int is rowH: fpx + gapPx;
		local Int is gw: :gutterWidthPx(fpx: fpx);
		local Int is textStartX: b:x + gw + padPx;

		local Int is minY: if({ ctx:hasClip }, { ctx:clipY }, { 0 });
		local Int is maxY: if({ ctx:hasClip }, { ctx:clipY + ctx:clipH }, { b:y + b:height });
		local Int is minX: if({ ctx:hasClip }, { ctx:clipX }, { b:x });

		local Int is count: dispLines:length();
		if({ count > 0 && rowH > 0 }, {
			local Int is firstIdx: (minY - (b:y + padPx)) / rowH;
			if({ firstIdx < 0 }, { firstIdx: 0; });
			local Int is lastIdx: ((maxY - (b:y + padPx)) / rowH) + 1;
			if({ lastIdx >= count }, { lastIdx: count - 1; });

			local Boolean is hasSel: :hasNonEmptySelection();
			local Int is sl: 0;
			local Int is sc: 0;
			local Int is el: 0;
			local Int is ec: 0;
			if({ hasSel }, {
				local Array of Int is r: :orderedSelection();
				sl: r:get(index: 0);
				sc: r:get(index: 1);
				el: r:get(index: 2);
				ec: r:get(index: 3);
			});

			local Int is i: firstIdx;
			while({ i <= lastIdx }, {
				local Int is ly: b:y + padPx + i * rowH;
				if({ ly + fpx >= minY && ly <= maxY }, {
					local String is lineStr: dispLines:get(index: i);
					local Int is rLine: dispRawLine:get(index: i);
					local Int is rStart: dispRawStart:get(index: i);
					local Int is rEnd: rStart + lineStr:length();

					## Highlight selection if this segment overlaps [sl:sc .. el:ec]
					if({ hasSel && rLine >= sl && rLine <= el }, {
						local Int is segS: 0;
						local Int is segE: lineStr:length();
						if({ rLine == sl && sc > rStart }, { segS: sc - rStart; });
						if({ rLine == el && ec < rEnd }, { segE: ec - rStart; });
						if({ segS < 0 }, { segS: 0; });
						if({ segE > lineStr:length() }, { segE: lineStr:length(); });
						if({ segE > segS || (rLine < el && segE == lineStr:length() && segS <= lineStr:length()) }, {
							local Int is hx1: textStartX + ctx:measureTextWidth(text: lineStr:substring(start: 0, end: segS), pixelHeight: fpx, mono: monoCached);
							local Int is hx2: textStartX + ctx:measureTextWidth(text: lineStr:substring(start: 0, end: segE), pixelHeight: fpx, mono: monoCached);
							if({ rLine < el && segE == lineStr:length() }, {
								hx2: hx2 + fpx / 2;
							});
							if({ hx2 > hx1 }, {
								ctx:fillRect(x: hx1, y: ly - 1, w: hx2 - hx1, h: rowH, color: activeTheme:activeBg);
							});
						});
					});

					if({ lineStr != '' }, {
						:paintLineText(
							ctx: ctx,
							x: textStartX,
							y: ly,
							lineStr: lineStr,
							rLine: rLine,
							rStart: rStart,
							fpx: fpx
						);
					});

					## Cursor caret if on this segment (with fast-fade alpha)
					if({ cursorAlphaByte > 0 && rLine == cursorLine && cursorCol >= rStart && cursorCol <= rEnd }, {
						local Boolean is isLastSegForLine: (i + 1 >= count) || (dispRawLine:get(index: i + 1) != rLine);
						if({ cursorCol < rEnd || isLastSegForLine }, {
							local Int is localCol: cursorCol - rStart;
							local Int is cx: textStartX + ctx:measureTextWidth(text: lineStr:substring(start: 0, end: localCol), pixelHeight: fpx, mono: monoCached);
							if({ cx >= minX + gw }, {
								local Int is caretCol: Color:fromArgb(argb: activeTheme:textPrimary):withAlphaByte(a: cursorAlphaByte):toArgb();
								local Int is caretW: activeScale:px(pt: 2.0);
								if({ caretW < 1 }, { caretW: 1; });
								ctx:fillRect(x: cx, y: ly, w: caretW, h: fpx, color: caretCol);
							});
						});
					});
				});
				i: i + 1;
			});

			## Paint line-number gutter AFTER text so horizontally scrolled text passes underneath it
			if({ lineNumsCached && gw > 0 }, {
				local Int is linePx: activeTheme:linePx(scaleFactor: activeScale:factor);
				ctx:fillRect(x: minX, y: minY, w: gw, h: maxY - minY, color: activeTheme:toolbarBg);
				ctx:fillRect(x: minX + gw - linePx, y: minY, w: linePx, h: maxY - minY, color: activeTheme:toolbarBorder);
				local Int is gi: firstIdx;
				while({ gi <= lastIdx }, {
					local Int is gly: b:y + padPx + gi * rowH;
					if({ gly + fpx >= minY && gly <= maxY && dispRawStart:get(index: gi) == 0 }, {
						local String is numStr: '' . (dispRawLine:get(index: gi) + 1);
						local Int is nw: ctx:measureTextWidth(text: numStr, pixelHeight: fpx);
						local Int is nx: minX + gw - activeScale:px(pt: 8.0) - nw;
						ctx:drawText(x: nx, y: gly, text: numStr, color: activeTheme:textMuted, pixelHeight: fpx);
					});
					gi: gi + 1;
				});
			});
		}, {
			if({ lineNumsCached && gw > 0 }, {
				local Int is linePx: activeTheme:linePx(scaleFactor: activeScale:factor);
				ctx:fillRect(x: minX, y: minY, w: gw, h: maxY - minY, color: activeTheme:toolbarBg);
				ctx:fillRect(x: minX + gw - linePx, y: minY, w: linePx, h: maxY - minY, color: activeTheme:toolbarBorder);
			});
		});
	}
}
