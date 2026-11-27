#! Package base:scrap
#! Reactive multi-line text view (`SewNode`) with optional wrapping, line numbers, cursor, highlight selection, and copy/cut/paste.

Class of SewNode is TextView{
	replace [String] is namespace: ['base', 'scrap', 'text'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Mem()],
		['base', 'sys', Process],
		['base', 'sys', Font],
		['base', 'sys', Parallel],
		['base', 'sys', Time],
		['base', 'struct', Array],
		['base', 'signal', TextEmitter],
		['base', 'signal', BoolEmitter],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Constraints],
		['base', 'sew', Rect],
		['base', 'fabric', Color],
		['base', 'fabric', DrawContext],
		['base', 'scrap', 'highlighter', Highlighter]
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
	Float is padPt: 0.0;
	Float is lineGapPt: 0.0;
	Float is docTextDeltaPt: 0.0;

	Array of String is rawLines: Array(['']);
	Array of String is dispLines: Array(['']);
	Array of Int is dispRawLine: Array([0]);
	Array of Int is dispRawStart: Array([0]);
	Array of Array of String is cachedLineSegs: Array();
	Array of Array of Int is cachedLineStarts: Array();
	Int is lastWrapFpx: 0;
	Int is cursorLine: 0;
	Int is cursorCol: 0;
	Int is selAnchorLine: 0;
	Int is selAnchorCol: 0;
	Boolean is hasSelection: false;
	Int is lastClickMs: 0;
	Int is clickStreak: 0;
	Int is lastClickLine: -1;
	Int is lastClickCol: -1;
	Time is clock: Time();
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
		Float is padPt: 0.0,
		Float is lineGapPt: 0.0
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
		Float is padPt: 0.0,
		Float is lineGapPt: 0.0
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

	Function of Highlighter is createWrapContext(){
		return Highlighter();
	}

	Function is measureLineAdvancesInCtx(Highlighter is hl, String is lineStr, Int is fpx, Boolean is mono, Int is outAdvI32Ptr, Int is scratchPtr){
		DrawContext:shared:measurePrefixAdvances(text: lineStr, pixelHeight: fpx, mono: mono, outAdvI32Ptr: outAdvI32Ptr, scratchPtr: scratchPtr);
	}

	local Function of Boolean is lineHasNonAscii(String is line){
		local Int is len: line:length();
		local Int is i: 0;
		while({ i < len }, {
			if({ (line:byteAt(index: i) & 255) >= 128 }, { return true; });
			i: i + 1;
		});
		return false;
	}

	local Function of Boolean is lineCannotWrap(String is line, Int is availTextW, Int is maxAsciiW, Int is tabW){
		local Int is len: line:length();
		if({ len == 0 }, { return true; });
		if({ len * maxAsciiW <= availTextW }, {
			local Int is i: 0;
			local Int is boundW: 0;
			while({ i < len }, {
				local Int is b: line:byteAt(index: i) & 255;
				if({ b >= 128 }, { return false; });
				if({ b == 9 }, {
					boundW: boundW + tabW;
				}, {
					boundW: boundW + maxAsciiW;
				});
				if({ boundW > availTextW }, { return false; });
				i: i + 1;
			});
			return true;
		});
		return false;
	}

	local Function is wrapLineSingle(
		Highlighter is wrapCtx,
		String is line,
		Int is availTextW,
		Int is fpx,
		Boolean is mono,
		Int is scratchPtr,
		Array of String is outSegs,
		Array of Int is outStarts,
		Int is maxAsciiW: 0,
		Int is tabW: 0
	){
		if({ line == '' }, {
			outSegs:add(item: '');
			outStarts:add(item: 0);
			return;
		});
		if({ maxAsciiW > 0 && :lineCannotWrap(line: line, availTextW: availTextW, maxAsciiW: maxAsciiW, tabW: tabW) }, {
			outSegs:add(item: line);
			outStarts:add(item: 0);
			return;
		});
		local Int is len: line:length();
		local Int is advBuf: Mem:alloc(bytes: (len + 1) * 4);
		:measureLineAdvancesInCtx(hl: wrapCtx, lineStr: line, fpx: fpx, mono: mono, outAdvI32Ptr: advBuf, scratchPtr: scratchPtr);
		local Int is fullW: Mem:loadI32(ptr: advBuf, byteOffset: len * 4);
		if({ fullW <= availTextW }, {
			Mem:free(ptr: advBuf);
			outSegs:add(item: line);
			outStarts:add(item: 0);
			return;
		});
		local Int is pos: 0;
		while({ pos < len }, {
			local Int is baseAdv: Mem:loadI32(ptr: advBuf, byteOffset: pos * 4);
			local Int is totalAdv: Mem:loadI32(ptr: advBuf, byteOffset: len * 4);
			local Int is segEnd: len;
			if({ totalAdv - baseAdv > availTextW }, {
				local Int is lo: pos + 1;
				local Int is hi: len - 1;
				local Int is maxFit: pos + 1;
				while({ lo <= hi }, {
					local Int is mid: lo + (hi - lo) / 2;
					if({ Mem:loadI32(ptr: advBuf, byteOffset: mid * 4) - baseAdv <= availTextW }, {
						maxFit: mid;
						lo: mid + 1;
					}, {
						hi: mid - 1;
					});
				});
				segEnd: maxFit;
				if({ segEnd < len }, {
					local Int is si: segEnd - 1;
					local Boolean is foundSpace: false;
					while({ si >= pos && !foundSpace }, {
						if({ line:byteAt(index: si) == 32 }, {
							if({ si + 1 > pos }, {
								segEnd: si + 1;
								foundSpace: true;
							});
						});
						si: si - 1;
					});
				});
				if({ segEnd <= pos }, { segEnd: pos + 1; });
			});
			outSegs:add(item: line:substring(start: pos, end: segEnd));
			outStarts:add(item: pos);
			pos: segEnd;
		});
		Mem:free(ptr: advBuf);
	}

	local Function is wrapLineRanges(
		Highlighter is wrapCtx,
		String is line,
		Int is availTextW,
		Int is fpx,
		Boolean is mono,
		Int is scratchPtr,
		Int is slotPtrs,
		Int is slotCounts,
		Int is rIdx,
		Int is maxAsciiW: 0,
		Int is tabW: 0
	){
		if({ line == '' || (maxAsciiW > 0 && :lineCannotWrap(line: line, availTextW: availTextW, maxAsciiW: maxAsciiW, tabW: tabW)) }, {
			Mem:storeI32(ptr: slotCounts, byteOffset: rIdx * 4, val: 1);
			Mem:storeI64(ptr: slotPtrs, byteOffset: rIdx * 8, val: 0);
			return;
		});
		local Int is len: line:length();
		local Int is advBuf: Mem:alloc(bytes: (len + 1) * 4);
		:measureLineAdvancesInCtx(hl: wrapCtx, lineStr: line, fpx: fpx, mono: mono, outAdvI32Ptr: advBuf, scratchPtr: scratchPtr);
		local Int is fullW: Mem:loadI32(ptr: advBuf, byteOffset: len * 4);
		if({ fullW <= availTextW }, {
			Mem:free(ptr: advBuf);
			Mem:storeI32(ptr: slotCounts, byteOffset: rIdx * 4, val: 1);
			Mem:storeI64(ptr: slotPtrs, byteOffset: rIdx * 8, val: 0);
			return;
		});
		local Int is cap: 16;
		local Int is buf: Mem:alloc(bytes: cap * 8);
		local Int is cnt: 0;
		local Int is pos: 0;
		while({ pos < len }, {
			local Int is baseAdv: Mem:loadI32(ptr: advBuf, byteOffset: pos * 4);
			local Int is totalAdv: Mem:loadI32(ptr: advBuf, byteOffset: len * 4);
			local Int is segEnd: len;
			if({ totalAdv - baseAdv > availTextW }, {
				local Int is lo: pos + 1;
				local Int is hi: len - 1;
				local Int is maxFit: pos + 1;
				while({ lo <= hi }, {
					local Int is mid: lo + (hi - lo) / 2;
					if({ Mem:loadI32(ptr: advBuf, byteOffset: mid * 4) - baseAdv <= availTextW }, {
						maxFit: mid;
						lo: mid + 1;
					}, {
						hi: mid - 1;
					});
				});
				segEnd: maxFit;
				if({ segEnd < len }, {
					local Int is si: segEnd - 1;
					local Boolean is foundSpace: false;
					while({ si >= pos && !foundSpace }, {
						if({ line:byteAt(index: si) == 32 }, {
							if({ si + 1 > pos }, {
								segEnd: si + 1;
								foundSpace: true;
							});
						});
						si: si - 1;
					});
				});
				if({ segEnd <= pos }, { segEnd: pos + 1; });
			});
			if({ cnt >= cap }, {
				local Int is newCap: cap * 2;
				local Int is newBuf: Mem:alloc(bytes: newCap * 8);
				local Int is ci: 0;
				while({ ci < cnt }, {
					Mem:storeI32(ptr: newBuf, byteOffset: ci * 8, val: Mem:loadI32(ptr: buf, byteOffset: ci * 8));
					Mem:storeI32(ptr: newBuf, byteOffset: ci * 8 + 4, val: Mem:loadI32(ptr: buf, byteOffset: ci * 8 + 4));
					ci: ci + 1;
				});
				Mem:free(ptr: buf);
				buf: newBuf;
				cap: newCap;
			});
			Mem:storeI32(ptr: buf, byteOffset: cnt * 8, val: pos);
			Mem:storeI32(ptr: buf, byteOffset: cnt * 8 + 4, val: segEnd);
			cnt: cnt + 1;
			pos: segEnd;
		});
		Mem:free(ptr: advBuf);
		Mem:storeI32(ptr: slotCounts, byteOffset: rIdx * 4, val: cnt);
		Mem:storeI64(ptr: slotPtrs, byteOffset: rIdx * 8, val: buf);
	}

	local Function is rebuildDisplayLines(Int is availTextW, Int is fpx){
		dispLines: Array();
		dispRawLine: Array();
		dispRawStart: Array();
		maxDispW: 0;
		local Int is rcount: rawLines:length();
		local Int is maxAsciiW: DrawContext:shared:measureTextWidth(text: 'W', pixelHeight: fpx, bold: true, mono: monoCached) + 2;
		if({ maxAsciiW < fpx / 2 }, { maxAsciiW: fpx / 2; });
		if({ maxAsciiW < 4 }, { maxAsciiW: 4; });
		local Int is tabW: DrawContext:shared:measureTextWidth(text: '\t', pixelHeight: fpx, bold: true, mono: monoCached) + 2;
		if({ tabW < maxAsciiW * 2 }, { tabW: maxAsciiW * 2; });
		if({ wrapCached && availTextW > fpx && rcount >= 64 }, {
			DrawContext:shared:measureTextWidth(text: ' ', pixelHeight: fpx, mono: monoCached);
			DrawContext:shared:measureTextWidth(text: ' ', pixelHeight: fpx, bold: true, mono: monoCached);
			DrawContext:shared:measureTextWidth(text: ' ', pixelHeight: fpx, italic: true, mono: monoCached);
			DrawContext:shared:measureTextWidth(text: ' ', pixelHeight: fpx, bold: true, italic: true, mono: monoCached);
			DrawContext:shared:measureTextWidth(text: '\u2026', pixelHeight: fpx, mono: monoCached);
			local Int is pw: 0;
			while({ pw < rcount }, {
				local String is pl: rawLines:get(index: pw);
				if({ :lineHasNonAscii(line: pl) }, {
					DrawContext:shared:prewarmText(text: pl, mono: monoCached);
				});
				pw: pw + 1;
			});
			local Int is slotPtrs: Mem:alloc(bytes: rcount * 8);
			local Int is slotCounts: Mem:alloc(bytes: rcount * 4);
			local Int is nThreads: Process():threadCount();
			if({ nThreads < 2 }, { nThreads: 2; });
			if({ nThreads > 8 }, { nThreads: 8; });
			if({ nThreads > rcount }, { nThreads: rcount; });
			local Int is baseCount: rcount / nThreads;
			local Int is remCount: rcount % nThreads;
			local Boolean is monoVal: monoCached;
			Parallel():runScoped(
				threads: nThreads,
				iterations: rcount,
				worker: local Function of Int(Int is tid, Int is cnt){
					local Int is startR: tid * baseCount + if({ tid < remCount }, { tid }, { remCount });
					local Int is endR: startR + cnt;
					local Int is scratch: Mem:alloc(bytes: 8);
					local Highlighter is wrapCtx: :createWrapContext();
					local Int is r: startR;
					while({ r < endR }, {
						:wrapLineRanges(
							wrapCtx: wrapCtx,
							line: rawLines:get(index: r),
							availTextW: availTextW,
							fpx: fpx,
							mono: monoVal,
							scratchPtr: scratch,
							slotPtrs: slotPtrs,
							slotCounts: slotCounts,
							rIdx: r,
							maxAsciiW: maxAsciiW,
							tabW: tabW
						);
						r: r + 1;
					});
					Mem:free(ptr: scratch);
					return 0;
				}
			);
			cachedLineSegs: Array();
			cachedLineStarts: Array();
			local Int is mr: 0;
			while({ mr < rcount }, {
				local String is line: rawLines:get(index: mr);
				local Int is cnt: Mem:loadI32(ptr: slotCounts, byteOffset: mr * 4);
				local Int is bufPtr: Mem:loadI64(ptr: slotPtrs, byteOffset: mr * 8);
				local Array of String is lineSegs: Array();
				local Array of Int is lineStarts: Array();
				if({ bufPtr == 0 }, {
					lineSegs:add(item: line);
					lineStarts:add(item: 0);
					dispLines:add(item: line);
					dispRawLine:add(item: mr);
					dispRawStart:add(item: 0);
				}, {
					local Int is j: 0;
					while({ j < cnt }, {
						local Int is sp: Mem:loadI32(ptr: bufPtr, byteOffset: j * 8);
						local Int is ep: Mem:loadI32(ptr: bufPtr, byteOffset: j * 8 + 4);
						local String is segStr: line:substring(start: sp, end: ep);
						lineSegs:add(item: segStr);
						lineStarts:add(item: sp);
						dispLines:add(item: segStr);
						dispRawLine:add(item: mr);
						dispRawStart:add(item: sp);
						j: j + 1;
					});
					Mem:free(ptr: bufPtr);
				});
				cachedLineSegs:add(item: lineSegs);
				cachedLineStarts:add(item: lineStarts);
				mr: mr + 1;
			});
			Mem:free(ptr: slotPtrs);
			Mem:free(ptr: slotCounts);
			lastWrapW: availTextW;
			lastWrapFpx: fpx;
			return;
		});

		cachedLineSegs: Array();
		cachedLineStarts: Array();
		local Highlighter is seqWrapCtx: :createWrapContext();
		local Int is r: 0;
		while({ r < rcount }, {
			local String is line: rawLines:get(index: r);
			local Array of String is lineSegs: Array();
			local Array of Int is lineStarts: Array();
			if({ !wrapCached || availTextW <= fpx || line == '' }, {
				lineSegs:add(item: line);
				lineStarts:add(item: 0);
				dispLines:add(item: line);
				dispRawLine:add(item: r);
				dispRawStart:add(item: 0);
				if({ !wrapCached && !:lineCannotWrap(line: line, availTextW: maxDispW, maxAsciiW: maxAsciiW, tabW: tabW) }, {
					local Int is lw: :measureStr(s: line, fpx: fpx);
					if({ lw > maxDispW }, { maxDispW: lw; });
				});
			}, {
				:wrapLineSingle(
					wrapCtx: seqWrapCtx,
					line: line,
					availTextW: availTextW,
					fpx: fpx,
					mono: monoCached,
					scratchPtr: 0,
					outSegs: lineSegs,
					outStarts: lineStarts,
					maxAsciiW: maxAsciiW,
					tabW: tabW
				);
				local Int is j: 0;
				while({ j < lineSegs:length() }, {
					dispLines:add(item: lineSegs:get(index: j));
					dispRawLine:add(item: r);
					dispRawStart:add(item: lineStarts:get(index: j));
					j: j + 1;
				});
			});
			cachedLineSegs:add(item: lineSegs);
			cachedLineStarts:add(item: lineStarts);
			r: r + 1;
		});
		lastWrapW: availTextW;
		lastWrapFpx: fpx;
	}

	local Function of String is joinRawLines(){
		local Int is n: rawLines:length();
		if({ n == 0 }, { return ''; });
		if({ n == 1 }, { return rawLines:get(index: 0); });
		local Int is totalBytes: n - 1;
		local Int is i: 0;
		while({ i < n }, {
			totalBytes: totalBytes + rawLines:get(index: i):length();
			i: i + 1;
		});
		if({ totalBytes <= 0 }, { return ''; });
		local Int is buf: Mem:alloc(bytes: totalBytes + 1);
		if({ buf == 0 }, { return ''; });
		local Int is pos: 0;
		i: 0;
		while({ i < n }, {
			if({ i > 0 }, {
				Mem:storeByte(ptr: buf, byteOffset: pos, val: 10);
				pos: pos + 1;
			});
			local String is ln: rawLines:get(index: i);
			local Int is sAddr: Mem:objToAddr(obj: ln);
			if({ sAddr != 0 }, {
				local Int is dAddr: Mem:loadI64(ptr: sAddr, byteOffset: 0);
				local Int is slen: Mem:loadI64(ptr: sAddr, byteOffset: 8);
				if({ dAddr != 0 && slen > 0 }, {
					Mem:copy(dst: buf + pos, src: dAddr, bytes: slen);
					pos: pos + slen;
				});
			});
			i: i + 1;
		});
		local String is out: Mem:strFromBytes(srcAddr: buf, len: pos);
		Mem:free(ptr: buf);
		return out;
	}

	local Function is notifyEdited(Boolean is keepWrapCache: false){
		local String is joined: :joinRawLines();
		if({ !keepWrapCache }, {
			lastWrapW: -1;
		});
		ignoreSelfEmit: true;
		text:emit(value: joined);
		local Function is cb: onTextChange;
		cb(joined);
		:emitCursorStatus();
		cursorAlphaByte: 255;
		lastBlinkMs: 0;
		invalidate();
	}

	local Function of Int is findFirstDispForRaw(Int is rawIdx){
		local Int is n: dispRawLine:length();
		local Int is lo: 0;
		local Int is hi: n - 1;
		local Int is ans: -1;
		while({ lo <= hi }, {
			local Int is mid: lo + (hi - lo) / 2;
			local Int is v: dispRawLine:get(index: mid);
			if({ v >= rawIdx }, {
				if({ v == rawIdx }, { ans: mid; });
				hi: mid - 1;
			}, {
				lo: mid + 1;
			});
		});
		return ans;
	}

	local Function of Boolean is updateWrapCacheForEdit(Int is sl, Int is el, Int is newEndLine){
		if({ lastWrapW < 0 || lastWrapFpx <= 0 }, { return false; });
		if({ !wrapCached }, {
			local Int is rc: rawLines:length();
			if({ sl == el && newEndLine == sl && dispLines:length() == rc }, {
				local String is edited: rawLines:get(index: sl);
				dispLines:set(index: sl, item: edited);
				if({ cachedLineSegs:length() == rc }, {
					local Array of String is sArr: Array([edited]);
					local Array of Int is stArr: Array([0]);
					cachedLineSegs:set(index: sl, item: sArr);
					cachedLineStarts:set(index: sl, item: stArr);
				});
				local Int is lw: :measureStr(s: edited, fpx: lastWrapFpx);
				if({ lw > maxDispW }, { maxDispW: lw; });
				return true;
			});
			dispLines: Array();
			dispRawLine: Array();
			dispRawStart: Array();
			cachedLineSegs: Array();
			cachedLineStarts: Array();
			local Int is r: 0;
			while({ r < rc }, {
				local String is ln: rawLines:get(index: r);
				dispLines:add(item: ln);
				dispRawLine:add(item: r);
				dispRawStart:add(item: 0);
				cachedLineSegs:add(item: Array([ln]));
				cachedLineStarts:add(item: Array([0]));
				if({ r >= sl && r <= newEndLine }, {
					local Int is lw: :measureStr(s: ln, fpx: lastWrapFpx);
					if({ lw > maxDispW }, { maxDispW: lw; });
				});
				r: r + 1;
			});
			return true;
		});
		if({ lastWrapW <= lastWrapFpx || cachedLineSegs:length() == 0 }, { return false; });
		local Int is maxAsciiW: DrawContext:shared:measureTextWidth(text: 'W', pixelHeight: lastWrapFpx, bold: true, mono: monoCached) + 2;
		if({ maxAsciiW < lastWrapFpx / 2 }, { maxAsciiW: lastWrapFpx / 2; });
		if({ maxAsciiW < 4 }, { maxAsciiW: 4; });
		local Int is tabW: DrawContext:shared:measureTextWidth(text: '\t', pixelHeight: lastWrapFpx, bold: true, mono: monoCached) + 2;
		if({ tabW < maxAsciiW * 2 }, { tabW: maxAsciiW * 2; });
		local Highlighter is editWrapCtx: :createWrapContext();

		## Fast path: single-line edit with unchanged wrapped segment count updates dispLines in-place (O(log N))
		if({ sl == el && newEndLine == sl && cachedLineSegs:length() == rawLines:length() }, {
			local Array of String is segs: Array();
			local Array of Int is starts: Array();
			:wrapLineSingle(
				wrapCtx: editWrapCtx,
				line: rawLines:get(index: sl),
				availTextW: lastWrapW,
				fpx: lastWrapFpx,
				mono: monoCached,
				scratchPtr: 0,
				outSegs: segs,
				outStarts: starts,
				maxAsciiW: maxAsciiW,
				tabW: tabW
			);
			local Int is oldCnt: cachedLineSegs:get(index: sl):length();
			cachedLineSegs:set(index: sl, item: segs);
			cachedLineStarts:set(index: sl, item: starts);
			if({ segs:length() == oldCnt }, {
				local Int is baseDisp: :findFirstDispForRaw(rawIdx: sl);
				if({ baseDisp >= 0 && baseDisp + oldCnt <= dispLines:length() }, {
					local Int is k: 0;
					while({ k < oldCnt }, {
						dispLines:set(index: baseDisp + k, item: segs:get(index: k));
						dispRawStart:set(index: baseDisp + k, item: starts:get(index: k));
						k: k + 1;
					});
					return true;
				});
			});
			dispLines: Array();
			dispRawLine: Array();
			dispRawStart: Array();
			local Int is rr: 0;
			while({ rr < cachedLineSegs:length() }, {
				local Array of String is rSegs: cachedLineSegs:get(index: rr);
				local Array of Int is rStarts: cachedLineStarts:get(index: rr);
				local Int is jj: 0;
				while({ jj < rSegs:length() }, {
					dispLines:add(item: rSegs:get(index: jj));
					dispRawLine:add(item: rr);
					dispRawStart:add(item: rStarts:get(index: jj));
					jj: jj + 1;
				});
				rr: rr + 1;
			});
			return true;
		});

		local Array of Array of String is nextSegs: Array();
		local Array of Array of Int is nextStarts: Array();
		local Int is i: 0;
		while({ i < sl && i < cachedLineSegs:length() }, {
			nextSegs:add(item: cachedLineSegs:get(index: i));
			nextStarts:add(item: cachedLineStarts:get(index: i));
			i: i + 1;
		});
		local Int is ni: sl;
		while({ ni <= newEndLine && ni < rawLines:length() }, {
			local Array of String is segs: Array();
			local Array of Int is starts: Array();
			:wrapLineSingle(
				wrapCtx: editWrapCtx,
				line: rawLines:get(index: ni),
				availTextW: lastWrapW,
				fpx: lastWrapFpx,
				mono: monoCached,
				scratchPtr: 0,
				outSegs: segs,
				outStarts: starts,
				maxAsciiW: maxAsciiW,
				tabW: tabW
			);
			nextSegs:add(item: segs);
			nextStarts:add(item: starts);
			ni: ni + 1;
		});
		i: el + 1;
		while({ i < cachedLineSegs:length() }, {
			nextSegs:add(item: cachedLineSegs:get(index: i));
			nextStarts:add(item: cachedLineStarts:get(index: i));
			i: i + 1;
		});
		if({ nextSegs:length() != rawLines:length() }, { return false; });
		cachedLineSegs: nextSegs;
		cachedLineStarts: nextStarts;

		dispLines: Array();
		dispRawLine: Array();
		dispRawStart: Array();
		local Int is r: 0;
		while({ r < cachedLineSegs:length() }, {
			local Array of String is rSegs: cachedLineSegs:get(index: r);
			local Array of Int is rStarts: cachedLineStarts:get(index: r);
			local Int is j: 0;
			while({ j < rSegs:length() }, {
				dispLines:add(item: rSegs:get(index: j));
				dispRawLine:add(item: r);
				dispRawStart:add(item: rStarts:get(index: j));
				j: j + 1;
			});
			r: r + 1;
		});
		return true;
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

		## Fast path: single-line edit without newlines updates rawLines in-place (O(1))
		if({ sl == el && repLines == 0 }, {
			rawLines:set(index: sl, item: combined);
		}, {
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
		});

		cursorLine: sl + repLines;
		if({ repLines == 0 }, {
			cursorCol: sc + replacement:length();
		}, {
			cursorCol: replacement:length() - (lastNl + 1);
		});
		hasSelection: false;
		local Boolean is kept: :updateWrapCacheForEdit(sl: sl, el: el, newEndLine: sl + repLines);
		:notifyEdited(keepWrapCache: kept);
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
		local Int is gapPx: activeScale:px(pt: if({ lineGapPt > 0.0 }, { lineGapPt }, { activeTheme:lineGapPt }));
		local Int is padPx: activeScale:px(pt: if({ padPt > 0.0 }, { padPt }, { activeTheme:editorPadPt }));
		local Int is gw: :gutterWidthPx(fpx: fpx);
		local Int is availTextW: c:maxW - gw - padPx * 2;
		if({ availTextW < fpx }, { availTextW: fpx; });
		if({ lastWrapW == -1 || (wrapCached && (lastWrapW != availTextW || lastWrapFpx != fpx)) }, {
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

	local Function of Boolean is isWordCode(Int is cp){
		return (cp >= 48 && cp <= 57) || (cp >= 65 && cp <= 90) || (cp >= 97 && cp <= 122) || cp == 95;
	}

	local Function is selectWordAt(Int is rLine, Int is rCol){
		if({ rLine < 0 || rLine >= rawLines:length() }, { return; });
		local String is ln: rawLines:get(index: rLine);
		local Int is n: ln:length();
		if({ n == 0 }, {
			:moveCursor(line: rLine, col: 0, extendSel: false);
			return;
		});
		local Int is p: rCol;
		if({ p >= n }, { p: n - 1; });
		if({ p < 0 }, { p: 0; });
		local Int is cp: ln:codePointAtRune(runeIndex: p);
		if({ !:isWordCode(cp: cp) && p > 0 && :isWordCode(cp: ln:codePointAtRune(runeIndex: p - 1)) }, {
			p: p - 1;
			cp: ln:codePointAtRune(runeIndex: p);
		});
		local Int is start: p;
		local Int is end: p + 1;
		if({ :isWordCode(cp: cp) }, {
			while({ start > 0 && :isWordCode(cp: ln:codePointAtRune(runeIndex: start - 1)) }, {
				start: start - 1;
			});
			while({ end < n && :isWordCode(cp: ln:codePointAtRune(runeIndex: end)) }, {
				end: end + 1;
			});
		});
		selAnchorLine: rLine;
		selAnchorCol: start;
		cursorLine: rLine;
		cursorCol: end;
		hasSelection: true;
		:emitCursorStatus();
		cursorAlphaByte: 255;
		lastBlinkMs: 0;
		invalidate();
	}

	local Function is selectLineAt(Int is rLine){
		if({ rLine < 0 || rLine >= rawLines:length() }, { return; });
		local String is ln: rawLines:get(index: rLine);
		selAnchorLine: rLine;
		selAnchorCol: 0;
		cursorLine: rLine;
		cursorCol: ln:length();
		hasSelection: ln:length() > 0;
		:emitCursorStatus();
		cursorAlphaByte: 255;
		lastBlinkMs: 0;
		invalidate();
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Rect is b: bounds();
		if({ !selectingDrag && (x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height) }, {
			return false;
		});
		local Int is fpx: :fontPx();
		local Int is gapPx: activeScale:px(pt: if({ lineGapPt > 0.0 }, { lineGapPt }, { activeTheme:lineGapPt }));
		local Int is padPx: activeScale:px(pt: if({ padPt > 0.0 }, { padPt }, { activeTheme:editorPadPt }));
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
		if({ relX > 0 && seg:length() > 0 }, {
			local Int is lo: 1;
			local Int is hi: seg:length();
			local Int is geIdx: seg:length();
			while({ lo <= hi }, {
				local Int is mid: lo + (hi - lo) / 2;
				local Int is mw: :measureLinePrefix(ctx: DrawContext:shared, lineStr: seg, col: mid, fpx: fpx);
				if({ mw >= relX }, {
					geIdx: mid;
					hi: mid - 1;
				}, {
					lo: mid + 1;
				});
			});
			local Int is prevIdx: geIdx - 1;
			local Int is wGe: :measureLinePrefix(ctx: DrawContext:shared, lineStr: seg, col: geIdx, fpx: fpx);
			local Int is wPrev: if({ prevIdx > 0 }, { :measureLinePrefix(ctx: DrawContext:shared, lineStr: seg, col: prevIdx, fpx: fpx) }, { 0 });
			local Int is dGe: if({ wGe >= relX }, { wGe - relX }, { relX - wGe });
			local Int is dPrev: if({ wPrev >= relX }, { wPrev - relX }, { relX - wPrev });
			bestCol: if({ dGe <= dPrev }, { geIdx }, { prevIdx });
		});

		local Int is rLine: dispRawLine:get(index: dispIdx);
		local Int is rCol: dispRawStart:get(index: dispIdx) + bestCol;
		if({ (mods & 1) != 0 }, {
			:clickStreak: 1;
			:lastClickMs: 0;
			selectingDrag: true;
			:moveCursor(line: rLine, col: rCol, extendSel: true);
			return true;
		});
		local Int is nowMs: clock:monotonicMs();
		local Int is dCol: if({ rCol >= lastClickCol }, { rCol - lastClickCol }, { lastClickCol - rCol });
		if({ lastClickMs > 0 && (nowMs - lastClickMs) <= 450 && rLine == lastClickLine && dCol <= 2 }, {
			:clickStreak: clickStreak + 1;
			if({ clickStreak > 3 }, { :clickStreak: 1; });
		}, {
			:clickStreak: 1;
		});
		:lastClickMs: nowMs;
		:lastClickLine: rLine;
		:lastClickCol: rCol;
		if({ clickStreak == 2 }, {
			selectingDrag: false;
			:selectWordAt(rLine: rLine, rCol: rCol);
			return true;
		});
		if({ clickStreak == 3 }, {
			selectingDrag: false;
			:selectLineAt(rLine: rLine);
			return true;
		});
		selectingDrag: true;
		:moveCursor(line: rLine, col: rCol, extendSel: false);
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

	## Measures pixel X offset at [col] on [lineStr]; subclasses can override to match styled text width.
	Function of Int is measureLinePrefix(DrawContext is ctx, String is lineStr, Int is col, Int is fpx){
		if({ col <= 0 || lineStr == '' }, { return 0; });
		local Int is target: if({ col > lineStr:length() }, { lineStr:length() }, { col });
		return ctx:measureTextWidth(text: lineStr:substring(start: 0, end: target), pixelHeight: fpx, mono: monoCached);
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		local Int is fpx: :fontPx();
		local Int is gapPx: activeScale:px(pt: if({ lineGapPt > 0.0 }, { lineGapPt }, { activeTheme:lineGapPt }));
		local Int is padPx: activeScale:px(pt: if({ padPt > 0.0 }, { padPt }, { activeTheme:editorPadPt }));
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
							local Int is hx1: textStartX + :measureLinePrefix(ctx: ctx, lineStr: lineStr, col: segS, fpx: fpx);
							local Int is hx2: textStartX + :measureLinePrefix(ctx: ctx, lineStr: lineStr, col: segE, fpx: fpx);
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
							local Int is cx: textStartX + :measureLinePrefix(ctx: ctx, lineStr: lineStr, col: localCol, fpx: fpx);
							if({ cx >= minX + gw }, {
								local Int is caretCol: Color:fromArgb(argb: activeTheme:textPrimary):withAlphaByte(a: cursorAlphaByte):toArgb();
								local Int is caretW: activeScale:px(pt: 1.0);
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
