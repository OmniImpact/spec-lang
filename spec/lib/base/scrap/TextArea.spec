#! Package base:scrap
#! Lightweight multi-line editable text input widget derived from [Theme].

Class of SewNode is TextArea{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', Time],
		['base', 'struct', Array],
		['base', 'fabric', Theme],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'scrap', TextEditBridge]
	];

	String is text: '';
	String is placeholder: '';
	Int is minLines: 4;
	Float is minWidthPt: 200.0;
	Float is heightPt: 0.0;
	Function is onChange: local Function(String is _next){};

	Boolean is hovered: false;
	Boolean is focused: false;
	Int is cursorPos: 0;
	Int is selAnchor: 0;
	Int is scrollY: 0;
	Int is maxScrollY: 0;
	Boolean is caretVisible: true;
	Int is caretBlinkMs: 0;
	Int is lastClickMs: 0;
	Int is clickStreak: 0;
	Int is lastClickPos: -1;
	Boolean is selectingDrag: false;
	Time is clock: Time();

	replace Function is init(
		String is text: '',
		String is placeholder: '',
		Int is minLines: 4,
		Float is minWidthPt: 200.0,
		Float is heightPt: 0.0,
		String is tooltip: '',
		Function is onChange: local Function(String is _next){}
	){
		:text: text;
		:placeholder: placeholder;
		:minLines: minLines;
		:minWidthPt: minWidthPt;
		:heightPt: heightPt;
		:tooltip: tooltip;
		:onChange: onChange;
		:cursorPos: text:length();
		:selAnchor: cursorPos;
	}

	local Function of Boolean is hasSelection(){
		return selAnchor != cursorPos;
	}

	local Function of Int is selStart(){
		return if({ selAnchor < cursorPos }, { selAnchor }, { cursorPos });
	}

	local Function of Int is selEnd(){
		return if({ selAnchor > cursorPos }, { selAnchor }, { cursorPos });
	}

	local Function is clearSelection(){
		:selAnchor: cursorPos;
	}

	local Function of Boolean is isWordCode(Int is cp){
		return (cp >= 48 && cp <= 57) || (cp >= 65 && cp <= 90) || (cp >= 97 && cp <= 122) || cp == 95;
	}

	local Function is selectWordAt(Int is pos){
		local Int is n: text:length();
		if({ n == 0 }, {
			:cursorPos: 0;
			:selAnchor: 0;
			return;
		});
		local Int is p: pos;
		if({ p >= n }, { p: n - 1; });
		if({ p < 0 }, { p: 0; });
		local Int is cp: text:codePointAtRune(runeIndex: p);
		if({ !:isWordCode(cp: cp) && p > 0 && :isWordCode(cp: text:codePointAtRune(runeIndex: p - 1)) }, {
			p: p - 1;
			cp: text:codePointAtRune(runeIndex: p);
		});
		local Int is start: p;
		local Int is end: p + 1;
		if({ :isWordCode(cp: cp) }, {
			while({ start > 0 && :isWordCode(cp: text:codePointAtRune(runeIndex: start - 1)) }, {
				start: start - 1;
			});
			while({ end < n && :isWordCode(cp: text:codePointAtRune(runeIndex: end)) }, {
				end: end + 1;
			});
		});
		:selAnchor: start;
		:cursorPos: end;
	}

	local Function is selectAll(){
		:selAnchor: 0;
		:cursorPos: text:length();
		:caretVisible: true;
		:caretBlinkMs: 0;
		:invalidate();
	}

	local Function is copySelection(){
		if({ !:hasSelection() }, { return; });
		local String is sel: text:substring(start: :selStart(), end: :selEnd());
		if({ sel != '' }, {
			TextEditBridge:shared:writeClipboard(text: sel);
		});
	}

	local Function is cutSelection(){
		if({ !:hasSelection() }, { return; });
		:copySelection();
		:deleteSelection();
		:caretVisible: true;
		:caretBlinkMs: 0;
		:ensureCursorVisible();
		local Function is cb: :onChange;
		cb(text);
		:invalidate();
	}

	local Function is pasteText(){
		local String is clip: TextEditBridge:shared:readClipboard();
		if({ clip == '' }, { return; });
		if({ :hasSelection() }, { :deleteSelection(); });
		local Int is n: text:length();
		if({ cursorPos < 0 }, { :cursorPos: 0; });
		if({ cursorPos > n }, { :cursorPos: n; });
		:text: text:substring(start: 0, end: cursorPos) . clip . text:substring(start: cursorPos, end: n);
		:cursorPos: cursorPos + clip:length();
		:selAnchor: cursorPos;
		:caretVisible: true;
		:caretBlinkMs: 0;
		:ensureCursorVisible();
		local Function is cb: :onChange;
		cb(text);
		:invalidate();
	}

	local Function of Int is posAtPoint(Int is x, Int is y){
		local Rect is b: bounds();
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Int is lh: :lineHeightPx();
		local Int is relY: y - (b:y + pad) + scrollY;
		local Array of String is lines: :splitLines();
		local Array of Int is starts: :lineStartOffsets();
		local Int is li: if({ lh > 0 }, { relY / lh }, { 0 });
		if({ li < 0 }, { li: 0; });
		if({ li >= lines:length() }, { li: lines:length() - 1; });
		local String is ln: lines:get(index: li);
		local Int is relX: x - (b:x + pad);
		local Int is approxCol: if({ relX <= 0 }, { 0 }, { (relX * 10) / (:fontPx() * 6) });
		if({ approxCol > ln:length() }, { approxCol: ln:length(); });
		return starts:get(index: li) + approxCol;
	}

	local Function is deleteSelection(){
		local Int is s0: :selStart();
		local Int is s1: :selEnd();
		if({ s1 <= s0 }, { return; });
		:text: text:substring(start: 0, end: s0) . text:substring(start: s1, end: text:length());
		:cursorPos: s0;
		:selAnchor: s0;
	}

	Function is setText(String is next){
		:text: next;
		if({ cursorPos > text:length() }, { :cursorPos: text:length(); });
		if({ cursorPos < 0 }, { :cursorPos: 0; });
		:selAnchor: cursorPos;
		:invalidate();
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:baseTextPt);
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Int is lineHeightPx(){
		local Int is fpx: :fontPx();
		return (fpx * 13) / 10 + 2;
	}

	local Function of Array of String is splitLines(){
		local Array of String is out: Array();
		local Int is n: text:length();
		local Int is start: 0;
		local Int is i: 0;
		while({ i < n }, {
			if({ text:substring(start: i, end: i + 1) == '\n' }, {
				out:add(item: text:substring(start: start, end: i));
				start: i + 1;
			});
			i: i + 1;
		});
		out:add(item: text:substring(start: start, end: n));
		return out;
	}

	local Function of Array of Int is lineStartOffsets(){
		local Array of Int is out: Array();
		out:add(item: 0);
		local Int is n: text:length();
		local Int is i: 0;
		while({ i < n }, {
			if({ text:substring(start: i, end: i + 1) == '\n' }, {
				out:add(item: i + 1);
			});
			i: i + 1;
		});
		return out;
	}

	local Function of Int is cursorLineIndex(Array of Int is starts){
		local Int is i: starts:length() - 1;
		while({ i > 0 }, {
			if({ cursorPos >= starts:get(index: i) }, { return i; });
			i: i - 1;
		});
		return 0;
	}

	local Function is ensureCursorVisible(){
		local Rect is b: bounds();
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Int is lh: :lineHeightPx();
		local Int is viewH: b:height - pad * 2;
		if({ viewH <= 0 }, { return; });
		local Array of Int is starts: :lineStartOffsets();
		local Int is li: :cursorLineIndex(starts: starts);
		local Int is topY: li * lh;
		local Int is botY: topY + lh;
		if({ topY < scrollY }, { :scrollY: topY; });
		if({ botY > scrollY + viewH }, { :scrollY: botY - viewH; });
		if({ scrollY < 0 }, { :scrollY: 0; });
	}

	replace Function of Size is measure(Constraints is c){
		local Int is w: activeScale:px(pt: minWidthPt);
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Int is lh: :lineHeightPx();
		local Int is linesH: minLines * lh + pad * 2;
		local Int is h: if({ heightPt > 0.0 }, { activeScale:px(pt: heightPt) }, { linesH });
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Int is lh: :lineHeightPx();
		local Array of String is lines: :splitLines();
		local Int is contentH: lines:length() * lh;
		local Int is viewH: bounds:height - pad * 2;
		local Int is ms: contentH - viewH;
		:maxScrollY: if({ ms > 0 }, { ms }, { 0 });
		if({ scrollY > maxScrollY }, { :scrollY: maxScrollY; });
		if({ scrollY < 0 }, { :scrollY: 0; });
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is bw: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
		local Int is rad: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
		local FillStyle is fill: activeTheme:resolveButtonFill(
			enabled: true, selected: false, hovered: hovered, focused: focused
		);
		local Int is borderCol: if({ focused }, { activeTheme:textAccent }, { activeTheme:buttonBorderColorArgb() });
		ctx:drawStyledBoxFill(
			x: b:x, y: b:y, w: b:width, h: b:height,
			fill: fill, borderColor: borderCol, thickness: bw, radius: rad,
			style: activeTheme:buttonBorderStyle
		);

		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Int is clipX: b:x + pad;
		local Int is clipY: b:y + pad;
		local Int is clipW: b:width - pad * 2;
		local Int is clipH: b:height - pad * 2;
		if({ clipW <= 0 || clipH <= 0 }, { return; });

		ctx:setClip(x: clipX, y: clipY, w: clipW, h: clipH);
		local Int is fpx: :fontPx();
		local Int is lh: :lineHeightPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is yOff: (lh - th) / 2;

		if({ text == '' && !focused && placeholder != '' }, {
			ctx:drawText(x: clipX, y: clipY + yOff, text: placeholder, color: activeTheme:textMuted, pixelHeight: fpx);
		}, {
			local Array of String is lines: :splitLines();
			local Array of Int is starts: :lineStartOffsets();
			local Int is curLine: :cursorLineIndex(starts: starts);
			local Int is curCol: cursorPos - starts:get(index: curLine);
			local Int is i: 0;
			while({ i < lines:length() }, {
				local Int is ly: clipY + i * lh - scrollY;
				if({ ly + lh > clipY && ly < clipY + clipH }, {
					local String is ln: lines:get(index: i);
					if({ focused && :hasSelection() }, {
						local Int is lineStart: starts:get(index: i);
						local Int is lineEnd: lineStart + ln:length();
						local Int is s0: :selStart();
						local Int is s1: :selEnd();
						local Int is ov0: if({ s0 > lineStart }, { s0 }, { lineStart });
						local Int is ov1: if({ s1 < lineEnd }, { s1 }, { lineEnd });
						if({ ov1 > ov0 }, {
							local Int is c0: ov0 - lineStart;
							local Int is c1: ov1 - lineStart;
							local Int is x0: if({ c0 > 0 }, { ctx:measureTextWidth(text: ln:substring(start: 0, end: c0), pixelHeight: fpx) }, { 0 });
							local Int is x1: ctx:measureTextWidth(text: ln:substring(start: 0, end: c1), pixelHeight: fpx);
							if({ x1 > x0 }, {
								ctx:fillRect(x: clipX + x0, y: ly + 1, w: x1 - x0, h: lh - 2, color: activeTheme:highlight:toArgb());
							});
						});
					});
					if({ ln != '' }, {
						ctx:drawText(x: clipX, y: ly + yOff, text: ln, color: activeTheme:textPrimary, pixelHeight: fpx);
					});
					if({ focused && caretVisible && i == curLine }, {
						local Int is cc: if({ curCol > ln:length() }, { ln:length() }, { curCol });
						local String is before: ln:substring(start: 0, end: cc);
						local Int is cw: if({ before != '' }, { ctx:measureTextWidth(text: before, pixelHeight: fpx) }, { 0 });
						local Int is cx: clipX + cw;
						if({ cx >= clipX && cx < clipX + clipW }, {
							ctx:fillRect(x: cx, y: ly + 1, w: 1, h: lh - 2, color: activeTheme:textAccent);
						});
					});
				});
				i: i + 1;
			});
		});

		if({ maxScrollY > 0 }, {
			local Int is barW: activeScale:px(pt: 4.0);
			if({ barW < 3 }, { barW: 3; });
			local Int is contentH: :splitLines():length() * lh;
			local Int is thumbH: (clipH * clipH) / contentH;
			if({ thumbH < 14 }, { thumbH: 14; });
			if({ thumbH > clipH }, { thumbH: clipH; });
			local Int is trackH: clipH - thumbH;
			local Int is thumbY: clipY + if({ maxScrollY > 0 }, { (scrollY * trackH) / maxScrollY }, { 0 });
			ctx:fillRect(x: clipX + clipW - barW, y: thumbY, w: barW, h: thumbH, color: activeTheme:textMuted);
		});
		ctx:clearClip();
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is inside: :containsPoint(x: x, y: y);
		if({ inside != hovered }, {
			:hovered: inside;
			:invalidate();
		});
		return inside;
	}

	replace Function is clearHover(){
		if({ hovered }, {
			:hovered: false;
			:invalidate();
		});
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ !:containsPoint(x: x, y: y) }, { return false; });
		local Rect is b: bounds();
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Int is lh: :lineHeightPx();
		local Int is relY: y - (b:y + pad) + scrollY;
		local Array of String is lines: :splitLines();
		local Array of Int is starts: :lineStartOffsets();
		local Int is li: if({ lh > 0 }, { relY / lh }, { 0 });
		if({ li < 0 }, { li: 0; });
		if({ li >= lines:length() }, { li: lines:length() - 1; });
		local String is ln: lines:get(index: li);
		local Int is relX: x - (b:x + pad);
		local Int is approxCol: if({ relX <= 0 }, { 0 }, { (relX * 10) / (:fontPx() * 6) });
		if({ approxCol > ln:length() }, { approxCol: ln:length(); });
		local Int is clickPos: starts:get(index: li) + approxCol;
		local Int is nowMs: clock:monotonicMs();
		local Int is dist: if({ clickPos >= lastClickPos }, { clickPos - lastClickPos }, { lastClickPos - clickPos });
		if({ lastClickMs > 0 && (nowMs - lastClickMs) <= 450 && dist <= 2 }, {
			:clickStreak: clickStreak + 1;
			if({ clickStreak > 3 }, { :clickStreak: 1; });
		}, {
			:clickStreak: 1;
		});
		:lastClickMs: nowMs;
		:lastClickPos: clickPos;
		if({ clickStreak == 2 }, {
			:selectWordAt(pos: clickPos);
		}, {
		if({ clickStreak == 3 }, {
			:selAnchor: starts:get(index: li);
			:cursorPos: starts:get(index: li) + ln:length();
		}, {
			:cursorPos: clickPos;
			:selAnchor: clickPos;
			:selectingDrag: true;
		}); });
		:caretVisible: true;
		:caretBlinkMs: 0;
		:invalidate();
		return true;
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ !selectingDrag }, { return false; });
		local Int is pos: :posAtPoint(x: x, y: y);
		if({ pos != cursorPos }, {
			:cursorPos: pos;
			:caretVisible: true;
			:caretBlinkMs: 0;
			:ensureCursorVisible();
			:invalidate();
		});
		return true;
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		if({ selectingDrag }, {
			:selectingDrag: false;
			return true;
		});
		return false;
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		if({ !:containsPoint(x: x, y: y) }, { return false; });
		local Boolean is hasSel: :hasSelection();
		TextEditBridge:shared:openEditMenu(
			x: x,
			y: y,
			onCut: local Function(){ :cutSelection(); },
			onCopy: local Function(){ :copySelection(); },
			onPaste: local Function(){ :pasteText(); },
			onSelectAll: local Function(){ :selectAll(); },
			canCut: hasSel,
			canCopy: hasSel,
			canPaste: TextEditBridge:shared:readClipboard() != ''
		);
		return true;
	}

	replace Function of Boolean is tick(Int is nowMs){
		if({ !focused }, {
			:caretBlinkMs: 0;
			:caretVisible: true;
			return false;
		});
		if({ caretBlinkMs == 0 }, {
			:caretBlinkMs: nowMs;
			return false;
		});
		if({ nowMs - caretBlinkMs >= 530 }, {
			:caretBlinkMs: nowMs;
			:caretVisible: !caretVisible;
			:invalidate();
			return true;
		});
		return false;
	}

	replace Function of Boolean is onScroll(Int is deltaY){
		if({ !hovered || maxScrollY <= 0 }, { return false; });
		local Int is step: activeScale:px(pt: 24.0);
		local Int is next: scrollY - deltaY * step;
		if({ next < 0 }, { next: 0; });
		if({ next > maxScrollY }, { next: maxScrollY; });
		if({ next != scrollY }, {
			:scrollY: next;
			:invalidate();
		});
		return true;
	}

	replace Function of Boolean is onText(String is ch, Int is mods){
		if({ !focused || ch == '' }, { return false; });
		if({ :hasSelection() }, { :deleteSelection(); });
		local Int is n: text:length();
		if({ cursorPos < 0 }, { :cursorPos: 0; });
		if({ cursorPos > n }, { :cursorPos: n; });
		local String is before: text:substring(start: 0, end: cursorPos);
		local String is after: text:substring(start: cursorPos, end: n);
		:text: before . ch . after;
		:cursorPos: cursorPos + ch:length();
		:selAnchor: cursorPos;
		:caretVisible: true;
		:caretBlinkMs: 0;
		:ensureCursorVisible();
		local Function is cb: :onChange;
		cb(text);
		:invalidate();
		return true;
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		if({ !focused }, { return false; });
		if({ (mods & 2) != 0 }, {
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
		local Int is n: text:length();
		if({ cursorPos < 0 }, { :cursorPos: 0; });
		if({ cursorPos > n }, { :cursorPos: n; });

		# Enter -> insert newline
		if({ key == 10 || key == 13 || key == 36 }, {
			if({ :hasSelection() }, { :deleteSelection(); n: text:length(); });
			local String is before: text:substring(start: 0, end: cursorPos);
			local String is after: text:substring(start: cursorPos, end: n);
			:text: before . '\n' . after;
			:cursorPos: cursorPos + 1;
			:selAnchor: cursorPos;
			:caretVisible: true;
			:caretBlinkMs: 0;
			:ensureCursorVisible();
			local Function is cb: :onChange;
			cb(text);
			:invalidate();
			return true;
		});
		# Backspace
		if({ key == 8 || key == 22 }, {
			if({ :hasSelection() }, {
				:deleteSelection();
				:caretVisible: true;
				:caretBlinkMs: 0;
				:ensureCursorVisible();
				local Function is cb: :onChange;
				cb(text);
				:invalidate();
			}, {
			if({ cursorPos > 0 }, {
				local String is before: text:substring(start: 0, end: cursorPos - 1);
				local String is after: text:substring(start: cursorPos, end: n);
				:text: before . after;
				:cursorPos: cursorPos - 1;
				:clearSelection();
				:caretVisible: true;
				:caretBlinkMs: 0;
				:ensureCursorVisible();
				local Function is cb: :onChange;
				cb(text);
				:invalidate();
			}); });
			return true;
		});
		# Delete
		if({ key == 127 || key == 119 }, {
			if({ :hasSelection() }, {
				:deleteSelection();
				:caretVisible: true;
				:caretBlinkMs: 0;
				:ensureCursorVisible();
				local Function is cb: :onChange;
				cb(text);
				:invalidate();
			}, {
			if({ cursorPos < n }, {
				local String is before: text:substring(start: 0, end: cursorPos);
				local String is after: text:substring(start: cursorPos + 1, end: n);
				:text: before . after;
				:clearSelection();
				:caretVisible: true;
				:caretBlinkMs: 0;
				local Function is cb: :onChange;
				cb(text);
				:invalidate();
			}); });
			return true;
		});
		# Left / Right
		if({ key == 1003 || key == 113 }, {
			if({ :hasSelection() }, {
				:cursorPos: :selStart();
				:clearSelection();
				:caretVisible: true;
				:caretBlinkMs: 0;
				:ensureCursorVisible();
				:invalidate();
			}, {
			if({ cursorPos > 0 }, { :cursorPos: cursorPos - 1; :clearSelection(); :caretVisible: true; :caretBlinkMs: 0; :ensureCursorVisible(); :invalidate(); }); });
			return true;
		});
		if({ key == 1004 || key == 114 }, {
			if({ :hasSelection() }, {
				:cursorPos: :selEnd();
				:clearSelection();
				:caretVisible: true;
				:caretBlinkMs: 0;
				:ensureCursorVisible();
				:invalidate();
			}, {
			if({ cursorPos < n }, { :cursorPos: cursorPos + 1; :clearSelection(); :caretVisible: true; :caretBlinkMs: 0; :ensureCursorVisible(); :invalidate(); }); });
			return true;
		});
		# Up / Down / Home / End
		local Array of String is lines: :splitLines();
		local Array of Int is starts: :lineStartOffsets();
		local Int is li: :cursorLineIndex(starts: starts);
		local Int is col: cursorPos - starts:get(index: li);
		if({ key == 1001 || key == 111 }, {
			if({ li > 0 }, {
				local Int is prevLen: lines:get(index: li - 1):length();
				local Int is nc: if({ col < prevLen }, { col }, { prevLen });
				:cursorPos: starts:get(index: li - 1) + nc;
				:caretVisible: true;
				:caretBlinkMs: 0;
				:ensureCursorVisible();
				:invalidate();
			});
			return true;
		});
		if({ key == 1002 || key == 116 }, {
			if({ li + 1 < lines:length() }, {
				local Int is nextLen: lines:get(index: li + 1):length();
				local Int is nc: if({ col < nextLen }, { col }, { nextLen });
				:cursorPos: starts:get(index: li + 1) + nc;
				:caretVisible: true;
				:caretBlinkMs: 0;
				:ensureCursorVisible();
				:invalidate();
			});
			return true;
		});
		if({ key == 1005 || key == 110 }, {
			:cursorPos: starts:get(index: li);
			:caretVisible: true;
			:caretBlinkMs: 0;
			:ensureCursorVisible();
			:invalidate();
			return true;
		});
		if({ key == 1006 || key == 115 }, {
			:cursorPos: starts:get(index: li) + lines:get(index: li):length();
			:caretVisible: true;
			:caretBlinkMs: 0;
			:ensureCursorVisible();
			:invalidate();
			return true;
		});
		return false;
	}

	replace Function of Boolean is canFocus(){
		return true;
	}

	replace Function of Boolean is isFocused(){
		return focused;
	}

	replace Function is setFocused(Boolean is next){
		:focused: next;
		:caretVisible: true;
		:caretBlinkMs: 0;
		:invalidate();
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ :containsPoint(x: x, y: y) }, { return CursorShape:TEXT; });
		return CursorShape:DEFAULT;
	}
}
