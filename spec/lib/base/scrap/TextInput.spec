#! Package base:scrap
#! Single-line editable text input widget derived from [Theme] and participating in Sew layout.

Class of SewNode is TextInput{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', Time],
		['base', 'struct', Array],
		['base', 'suit', KeyCode],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext],
		['base', 'fabric', 'svg', SvgRenderer],
		['base', 'scrap', DropdownPopup],
		['base', 'scrap', TextEditBridge]
	];

	held String is ICON_SEARCH_SVG: "<svg viewBox=\"0 0 16 16\"><circle cx=\"7\" cy=\"7\" r=\"4.5\" fill=\"none\" stroke=\"#ffffff\" stroke-width=\"1.6\"/><path d=\"M10.5 10.5L14 14\" fill=\"none\" stroke=\"#ffffff\" stroke-width=\"1.6\" stroke-linecap=\"round\"/></svg>";
	held String is ICON_CLEAR_SVG: "<svg viewBox=\"0 0 16 16\"><path d=\"M4.5 4.5L11.5 11.5M11.5 4.5L4.5 11.5\" fill=\"none\" stroke=\"#ffffff\" stroke-width=\"1.7\" stroke-linecap=\"round\"/></svg>";

	String is text: '';
	String is placeholder: '';
	String is suffix: '';
	String is leftIconSvg: '';
	String is rightButtonIconSvg: '';
	String is rightButtonTooltip: '';
	Boolean is rightButtonOnlyWhenNonEmpty: false;
	Boolean is clearable: false;
	Function is onRightButtonClick: local Function(){};
	Boolean is hasAutocomplete: false;
	Function of Array of String is autocompleteProvider: local Function of Array of String(String is _query){ return Array(); };
	Int is autocompleteMaxVisible: 6;
	Function is onAutocompleteSelect: local Function(String is _val){};
	Boolean is focused: false;
	Boolean is hovered: false;
	Boolean is rightBtnHovered: false;
	Int is cursorPos: 0;
	Int is selAnchor: 0;
	Int is scrollX: 0;
	Boolean is caretVisible: true;
	Int is caretBlinkMs: 0;
	Int is lastClickMs: 0;
	Int is clickStreak: 0;
	Int is lastClickPos: -1;
	Time is clock: Time();
	Float is minWidthPt: 0.0;
	Float is heightPt: 0.0;
	Boolean is expand: false;
	Function is onChange: local Function(String is _next){};
	Function is onSubmit: local Function(String is _val){};
	Function is onUp: local Function(){};
	Function is onDown: local Function(){};
	Array of String is suggestions: Array();
	Boolean is acOpen: false;
	Int is acHighlight: -1;
	Int is acHover: -1;
	Rect is acPopupRect: Rect();
	Int is lastViewW: 0;
	Int is lastViewH: 0;

	replace Function is init(
		String is text: '',
		String is placeholder: '',
		String is suffix: '',
		String is leftIconSvg: '',
		String is rightButtonIconSvg: '',
		String is rightButtonTooltip: '',
		Boolean is rightButtonOnlyWhenNonEmpty: false,
		Boolean is clearable: false,
		Function is onRightButtonClick: local Function(){},
		Boolean is hasAutocomplete: false,
		Function of Array of String is autocompleteProvider: local Function of Array of String(String is _query){ return Array(); },
		Int is autocompleteMaxVisible: 6,
		Function is onAutocompleteSelect: local Function(String is _val){},
		Boolean is focused: false,
		Float is minWidthPt: 0.0,
		Float is heightPt: 0.0,
		Boolean is expand: false,
		Function is onChange: local Function(String is _next){},
		Function is onSubmit: local Function(String is _val){},
		Function is onUp: local Function(){},
		Function is onDown: local Function(){},
		String is tooltip: ''
	){
		:text: text;
		:placeholder: placeholder;
		:suffix: suffix;
		:leftIconSvg: leftIconSvg;
		:clearable: clearable;
		if({ clearable && rightButtonIconSvg == '' }, {
			:rightButtonIconSvg: TextInput:ICON_CLEAR_SVG;
		}, {
			:rightButtonIconSvg: rightButtonIconSvg;
		});
		if({ clearable && rightButtonTooltip == '' }, {
			:rightButtonTooltip: 'Clear';
		}, {
			:rightButtonTooltip: rightButtonTooltip;
		});
		:rightButtonOnlyWhenNonEmpty: rightButtonOnlyWhenNonEmpty || clearable;
		:onRightButtonClick: onRightButtonClick;
		:hasAutocomplete: hasAutocomplete;
		:autocompleteProvider: autocompleteProvider;
		:autocompleteMaxVisible: if({ autocompleteMaxVisible > 0 }, { autocompleteMaxVisible }, { 6 });
		:onAutocompleteSelect: onAutocompleteSelect;
		:focused: focused;
		:minWidthPt: minWidthPt;
		:heightPt: heightPt;
		:expand: expand;
		:onChange: onChange;
		:onSubmit: onSubmit;
		:onUp: onUp;
		:onDown: onDown;
		:hovered: false;
		:rightBtnHovered: false;
		:suggestions: Array();
		:acOpen: false;
		:acHighlight: -1;
		:acHover: -1;
		:tooltip: tooltip;
	}

	local Function of String is stripSuffix(String is s){
		if({ suffix == '' }, { return s; });
		local Int is sl: s:length();
		local Int is fl: suffix:length();
		if({ sl >= fl && s:substring(start: sl - fl, end: sl) == suffix }, {
			return s:substring(start: 0, end: sl - fl);
		});
		return s;
	}

	local Function of String is ensureSuffix(String is s){
		if({ suffix == '' || s == '' }, { return s; });
		local Int is sl: s:length();
		local Int is fl: suffix:length();
		if({ sl >= fl && s:substring(start: sl - fl, end: sl) == suffix }, {
			return s;
		});
		return s . suffix;
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
		invalidate();
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
		local Function is cb: onChange;
		cb(text);
		:refreshAutocomplete();
		invalidate();
	}

	local Function is pasteText(){
		local String is clip: TextEditBridge:shared:readClipboard();
		if({ clip == '' }, { return; });
		if({ :hasSelection() }, { :deleteSelection(); });
		local Int is cPos: cursorPos;
		if({ cPos < 0 }, { cPos: 0; });
		if({ cPos > text:length() }, { cPos: text:length(); });
		:text: text:substring(start: 0, end: cPos) . clip . text:substring(start: cPos, end: text:length());
		:cursorPos: cPos + clip:length();
		:selAnchor: cursorPos;
		:caretVisible: true;
		:caretBlinkMs: 0;
		local Function is cb: onChange;
		cb(text);
		:refreshAutocomplete();
		invalidate();
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
		local String is val: if({ focused }, { :stripSuffix(s: next) }, { next });
		if({ text != val }, {
			:text: val;
			if({ cursorPos > text:length() }, { :cursorPos: text:length(); });
			:selAnchor: cursorPos;
			invalidate();
		});
	}

	replace Function of Boolean is canFocus(){
		return true;
	}

	replace Function of Boolean is isFocused(){
		return focused;
	}

	replace Function is setFocused(Boolean is next){
		if({ focused != next }, {
			:focused: next;
			:caretVisible: true;
			:caretBlinkMs: 0;
			if({ next }, {
				:text: :stripSuffix(s: text);
				:cursorPos: text:length();
				:selAnchor: cursorPos;
				:refreshAutocomplete();
			}, {
				:acOpen: false;
				:acHighlight: -1;
				:acHover: -1;
				local Function is scb: onSubmit;
				scb(text);
				:text: :ensureSuffix(s: text);
				:cursorPos: 0;
				:scrollX: 0;
			});
			invalidate();
		});
	}

	local Function of Int is iconSizePx(){
		local Int is sz: activeScale:px(pt: 13.0);
		return if({ sz < 11 }, { 11 }, { sz });
	}

	local Function of Boolean is rightButtonVisible(){
		if({ rightButtonIconSvg == '' }, { return false; });
		if({ rightButtonOnlyWhenNonEmpty && text == '' }, { return false; });
		return true;
	}

	local Function of Rect is rightButtonRect(){
		local Rect is b: bounds();
		if({ !:rightButtonVisible() || b:width <= 0 || b:height <= 0 }, { return Rect(); });
		local Int is padX: activeScale:px(pt: activeTheme:paddingPt);
		local Int is iconSz: :iconSizePx();
		local Int is btnW: iconSz + padX;
		local Int is btnH: if({ b:height > 4 }, { b:height - 4 }, { b:height });
		return Rect(x: b:x + b:width - btnW - 2, y: b:y + (b:height - btnH) / 2, width: btnW, height: btnH);
	}

	local Function of Int is textStartX(){
		local Rect is b: bounds();
		local Int is padX: activeScale:px(pt: activeTheme:paddingPt);
		if({ leftIconSvg != '' }, {
			return b:x + padX + :iconSizePx() + activeScale:px(pt: 5.0);
		});
		return b:x + padX;
	}

	local Function of Int is textEndX(){
		local Rect is b: bounds();
		local Int is padX: activeScale:px(pt: activeTheme:paddingPt);
		if({ :rightButtonVisible() }, {
			local Rect is rbr: :rightButtonRect();
			return rbr:x - activeScale:px(pt: 4.0);
		});
		return b:x + b:width - padX;
	}

	Function is refreshAutocomplete(){
		if({ !hasAutocomplete || !focused }, {
			:acOpen: false;
			:acHighlight: -1;
			:acHover: -1;
			return;
		});
		local Function of Array of String is prov: autocompleteProvider;
		local Array of String is res: prov(text);
		:suggestions: res;
		if({ res:length() > 0 }, {
			:acOpen: true;
			:acHighlight: 0;
			:acHover: -1;
		}, {
			:acOpen: false;
			:acHighlight: -1;
			:acHover: -1;
		});
	}

	Function is acceptAutocomplete(Int is idx){
		if({ idx < 0 || idx >= suggestions:length() }, { return; });
		local String is chosen: suggestions:get(index: idx);
		:text: chosen;
		:cursorPos: text:length();
		:selAnchor: cursorPos;
		:scrollX: 0;
		:acOpen: false;
		:acHighlight: -1;
		:acHover: -1;
		:caretVisible: true;
		:caretBlinkMs: 0;
		local Function is cb: onChange;
		cb(text);
		local Function is acb: onAutocompleteSelect;
		acb(chosen);
		invalidate();
	}

	local Function of Int is acRowHeightPx(){
		local Int is h: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 14.0) + activeTheme:paddingPt * 1.5);
		return if({ h < 20 }, { 20 }, { h });
	}

	local Function is layoutAcPopup(Int is viewW, Int is viewH){
		if({ viewW > 0 }, { lastViewW: viewW; });
		if({ viewH > 0 }, { lastViewH: viewH; });
		local Rect is b: bounds();
		local Int is vis: suggestions:length();
		if({ vis > autocompleteMaxVisible }, { vis: autocompleteMaxVisible; });
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is popH: vis * :acRowHeightPx() + bw * 2;
		local Int is popW: b:width;
		:acPopupRect: DropdownPopup:shared:placeRect(
			anchor: b,
			popupW: popW,
			popupH: popH,
			viewW: lastViewW,
			viewH: lastViewH,
			gapPx: 2
		);
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 15.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Boolean is contains(Int is x, Int is y){
		local Rect is b: bounds();
		return x >= b:x && x < b:x + b:width && y >= b:y && y < b:y + b:height;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is minW: activeScale:px(pt: if({ minWidthPt > 0.0 }, { minWidthPt }, { activeTheme:inputMinWidthPt }));
		local Int is h: activeScale:px(pt: if({ heightPt > 0.0 }, { heightPt }, { activeTheme:inputHeightPt }));
		local Int is fpx: :fontPx();
		local Int is tw: DrawContext:measureWidth(text: text, pixelHeight: fpx) + activeScale:px(pt: activeTheme:paddingPt * 2.5);
		local Int is natW: if({ tw > minW }, { tw }, { minW });
		local Int is w: if({ expand && c:maxW > natW }, { c:maxW }, { natW });
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is bw: activeTheme:borderPx(scaleFactor: activeScale:factor);
		local Int is border: if({ focused }, { activeTheme:textAccent }, {
			if({ hovered }, { activeTheme:textMuted }, { activeTheme:buttonBorder })
		});
		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: activeTheme:windowBg);
		if({ bw > 0 }, {
			ctx:strokeRect(x: b:x, y: b:y, w: b:width, h: b:height, color: border, thickness: bw);
		});

		local Int is padX: activeScale:px(pt: activeTheme:paddingPt);
		local Int is iconSz: :iconSizePx();
		if({ leftIconSvg != '' }, {
			local Int is ix: b:x + padX;
			local Int is iy: b:y + (b:height - iconSz) / 2;
			local Int is iconCol: if({ focused }, { activeTheme:textPrimary }, { activeTheme:textMuted });
			SvgRenderer:shared:draw(ctx: ctx, svgSrc: leftIconSvg, x: ix, y: iy, widthPx: iconSz, heightPx: iconSz, tintColor: iconCol, useTint: true);
		});

		if({ :rightButtonVisible() }, {
			local Rect is rbr: :rightButtonRect();
			if({ rightBtnHovered }, {
				local Int is btnRad: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
				ctx:fillRoundRect(x: rbr:x, y: rbr:y, w: rbr:width, h: rbr:height, radius: btnRad, color: activeTheme:hoverBg);
			});
			local Int is rix: rbr:x + (rbr:width - iconSz) / 2;
			local Int is riy: rbr:y + (rbr:height - iconSz) / 2;
			local Int is rCol: if({ rightBtnHovered }, { activeTheme:textPrimary }, { activeTheme:textMuted });
			SvgRenderer:shared:draw(ctx: ctx, svgSrc: rightButtonIconSvg, x: rix, y: riy, widthPx: iconSz, heightPx: iconSz, tintColor: rCol, useTint: true);
		});

		local Int is fpx: :fontPx();
		local Int is th: DrawContext:measureHeight(pixelHeight: fpx);
		local Int is txStart: :textStartX();
		local Int is txEnd: :textEndX();
		local Int is clipW: txEnd - txStart;
		if({ clipW > 4 }, {
			ctx:setClip(x: txStart, y: b:y, w: clipW, h: b:height);
			local Int is textY: b:y + (b:height - th) / 2;
			if({ text == '' && !focused && placeholder != '' }, {
				ctx:drawText(x: txStart, y: textY, text: placeholder, color: activeTheme:textMuted, pixelHeight: fpx);
			}, {
				local Int is cPos: cursorPos;
				if({ cPos < 0 }, { cPos: 0; });
				if({ cPos > text:length() }, { cPos: text:length(); });
				local Int is caretOff: if({ focused && cPos > 0 }, {
					ctx:measureTextWidth(text: text:substring(start: 0, end: cPos), pixelHeight: fpx)
				}, { 0 });
				local Int is caretW: activeScale:px(pt: 1.0);
				if({ caretW < 1 }, { caretW: 1; });
				if({ focused }, {
					if({ caretOff - scrollX > clipW - caretW }, {
						:scrollX: caretOff - (clipW - caretW);
					});
					if({ caretOff - scrollX < 0 }, {
						:scrollX: caretOff;
					});
					if({ scrollX < 0 }, { :scrollX: 0; });
				}, {
					:scrollX: 0;
				});
				if({ focused && :hasSelection() }, {
					local Int is s0: :selStart();
					local Int is s1: :selEnd();
					if({ s0 > text:length() }, { s0: text:length(); });
					if({ s1 > text:length() }, { s1: text:length(); });
					if({ s1 > s0 }, {
						local Int is sx0: if({ s0 > 0 }, { ctx:measureTextWidth(text: text:substring(start: 0, end: s0), pixelHeight: fpx) }, { 0 });
						local Int is sx1: ctx:measureTextWidth(text: text:substring(start: 0, end: s1), pixelHeight: fpx);
						local Int is selW: sx1 - sx0;
						if({ selW > 0 }, {
							ctx:fillRect(x: txStart + sx0 - scrollX, y: textY, w: selW, h: th, color: activeTheme:highlight:toArgb());
						});
					});
				});
				ctx:drawText(x: txStart - scrollX, y: textY, text: text, color: activeTheme:textPrimary, pixelHeight: fpx);
				if({ focused && caretVisible }, {
					ctx:fillRect(x: txStart + caretOff - scrollX, y: textY, w: caretW, h: th, color: activeTheme:textPrimary);
				});
			});
			ctx:clearClip();
		});
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is h: :contains(x: x, y: y);
		local Boolean is rbh: :rightButtonVisible() && :rightButtonRect():contains(px: x, py: y);
		if({ h != hovered || rbh != rightBtnHovered }, {
			:hovered: h;
			:rightBtnHovered: rbh;
			invalidate();
			return true;
		});
		return false;
	}

	replace Function is clearHover(){
		if({ hovered || rightBtnHovered }, {
			:hovered: false;
			:rightBtnHovered: false;
			invalidate();
		});
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ acOpen && acPopupRect:contains(px: x, py: y) }, { return CursorShape:POINTER; });
		if({ :rightButtonVisible() && :rightButtonRect():contains(px: x, py: y) }, { return CursorShape:POINTER; });
		if({ :contains(x: x, y: y) }, { return CursorShape:TEXT; });
		return CursorShape:DEFAULT;
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
		if({ :rightButtonVisible() && rightButtonTooltip != '' && :rightButtonRect():contains(px: x, py: y) }, {
			return rightButtonTooltip;
		});
		if({ tooltip != '' && :contains(x: x, y: y) }, { return tooltip; });
		return '';
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Boolean is inside: :contains(x: x, y: y);
		if({ inside && :rightButtonVisible() && :rightButtonRect():contains(px: x, py: y) }, {
			if({ clearable }, {
				:text: '';
				:cursorPos: 0;
				:selAnchor: 0;
				:scrollX: 0;
				:acOpen: false;
				:acHighlight: -1;
				:acHover: -1;
				local Function is cb: onChange;
				cb('');
			});
			local Function is rcb: onRightButtonClick;
			rcb();
			:refreshAutocomplete();
			invalidate();
			return true;
		});
		if({ inside != focused }, {
			:setFocused(next: inside);
		});
		if({ inside }, {
			local Int is fpx: :fontPx();
			local Int is relX: (x - :textStartX()) + scrollX;
			local Int is best: 0;
			if({ relX > 0 && text:length() > 0 }, {
				local Int is bestDist: relX;
				local Int is i: 1;
				while({ i <= text:length() }, {
					local Int is w: DrawContext:measureWidth(text: text:substring(start: 0, end: i), pixelHeight: fpx);
					local Int is d: if({ w >= relX }, { w - relX }, { relX - w });
					if({ d <= bestDist }, {
						bestDist: d;
						best: i;
					});
					i: i + 1;
				});
			});
			local Int is nowMs: clock:monotonicMs();
			local Int is dist: if({ best >= lastClickPos }, { best - lastClickPos }, { lastClickPos - best });
			if({ lastClickMs > 0 && (nowMs - lastClickMs) <= 450 && dist <= 2 }, {
				:clickStreak: clickStreak + 1;
				if({ clickStreak > 3 }, { :clickStreak: 1; });
			}, {
				:clickStreak: 1;
			});
			:lastClickMs: nowMs;
			:lastClickPos: best;
			if({ clickStreak == 2 }, {
				:selectWordAt(pos: best);
			}, {
			if({ clickStreak == 3 }, {
				:selectAll();
			}, {
				:cursorPos: best;
				:selAnchor: best;
			}); });
			:caretVisible: true;
			:caretBlinkMs: 0;
			invalidate();
			return true;
		});
		return false;
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
			invalidate();
			return true;
		});
		return false;
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
		if({ acOpen }, {
			local Int is vis: suggestions:length();
			if({ vis > autocompleteMaxVisible }, { vis: autocompleteMaxVisible; });
			if({ key == KeyCode:ESC }, {
				:acOpen: false;
				:acHighlight: -1;
				:acHover: -1;
				invalidate();
				return true;
			});
			if({ key == KeyCode:UP }, {
				if({ vis > 0 }, {
					:acHighlight: if({ acHighlight > 0 }, { acHighlight - 1 }, { vis - 1 });
					invalidate();
				});
				return true;
			});
			if({ key == KeyCode:DOWN }, {
				if({ vis > 0 }, {
					:acHighlight: if({ acHighlight + 1 < vis }, { acHighlight + 1 }, { 0 });
					invalidate();
				});
				return true;
			});
			if({ (KeyCode:isEnter(key: key) || key == KeyCode:TAB) && acHighlight >= 0 && acHighlight < vis }, {
				:acceptAutocomplete(idx: acHighlight);
				return true;
			});
		});
		if({ key == KeyCode:UP }, {
			local Function is ucb: onUp;
			ucb();
			return true;
		});
		if({ key == KeyCode:DOWN }, {
			if({ hasAutocomplete && !acOpen }, {
				:refreshAutocomplete();
				if({ acOpen }, {
					invalidate();
					return true;
				});
			});
			local Function is dcb: onDown;
			dcb();
			return true;
		});
		if({ key == KeyCode:LEFT }, {
			if({ :hasSelection() }, {
				:cursorPos: :selStart();
				:clearSelection();
				:caretVisible: true;
				:caretBlinkMs: 0;
				invalidate();
			}, {
			if({ cursorPos > 0 }, {
				:cursorPos: cursorPos - 1;
				:clearSelection();
				:caretVisible: true;
				:caretBlinkMs: 0;
				invalidate();
			}); });
			return true;
		});
		if({ key == KeyCode:RIGHT }, {
			if({ :hasSelection() }, {
				:cursorPos: :selEnd();
				:clearSelection();
				:caretVisible: true;
				:caretBlinkMs: 0;
				invalidate();
			}, {
			if({ cursorPos < text:length() }, {
				:cursorPos: cursorPos + 1;
				:clearSelection();
				:caretVisible: true;
				:caretBlinkMs: 0;
				invalidate();
			}); });
			return true;
		});
		if({ key == KeyCode:HOME }, {
			:cursorPos: 0;
			:clearSelection();
			:caretVisible: true;
			:caretBlinkMs: 0;
			invalidate();
			return true;
		});
		if({ key == KeyCode:END }, {
			:cursorPos: text:length();
			:clearSelection();
			:caretVisible: true;
			:caretBlinkMs: 0;
			invalidate();
			return true;
		});
		if({ key == KeyCode:BACKSPACE }, {
			if({ :hasSelection() }, {
				:deleteSelection();
				:caretVisible: true;
				:caretBlinkMs: 0;
				local Function is cb: onChange;
				cb(text);
				:refreshAutocomplete();
				invalidate();
			}, {
			if({ cursorPos > 0 }, {
				:text: text:substring(start: 0, end: cursorPos - 1) . text:substring(start: cursorPos, end: text:length());
				:cursorPos: cursorPos - 1;
				:clearSelection();
				:caretVisible: true;
				:caretBlinkMs: 0;
				local Function is cb: onChange;
				cb(text);
				:refreshAutocomplete();
				invalidate();
			}); });
			return true;
		});
		if({ key == KeyCode:DELETE }, {
			if({ :hasSelection() }, {
				:deleteSelection();
				:caretVisible: true;
				:caretBlinkMs: 0;
				local Function is cb: onChange;
				cb(text);
				:refreshAutocomplete();
				invalidate();
			}, {
			if({ cursorPos < text:length() }, {
				:text: text:substring(start: 0, end: cursorPos) . text:substring(start: cursorPos + 1, end: text:length());
				:clearSelection();
				:caretVisible: true;
				:caretBlinkMs: 0;
				local Function is cb: onChange;
				cb(text);
				:refreshAutocomplete();
				invalidate();
			}); });
			return true;
		});
		if({ KeyCode:isEnter(key: key) }, {
			local Function is scb: onSubmit;
			scb(text);
			return true;
		});
		return false;
	}

	replace Function of Boolean is onText(String is ch, Int is mods){
		if({ !focused || ch == '' }, { return false; });
		if({ :hasSelection() }, { :deleteSelection(); });
		local Int is cPos: cursorPos;
		if({ cPos < 0 }, { cPos: 0; });
		if({ cPos > text:length() }, { cPos: text:length(); });
		:text: text:substring(start: 0, end: cPos) . ch . text:substring(start: cPos, end: text:length());
		:cursorPos: cPos + ch:length();
		:selAnchor: cursorPos;
		:caretVisible: true;
		:caretBlinkMs: 0;
		local Function is cb: onChange;
		cb(text);
		:refreshAutocomplete();
		invalidate();
		return true;
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		if({ !:contains(x: x, y: y) }, { return false; });
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

	replace Function of Boolean is blocksPointerAt(Int is x, Int is y){
		if({ acOpen && acPopupRect:contains(px: x, py: y) }, { return true; });
		return :contains(x: x, y: y);
	}

	replace Function of Boolean is closePopupsOutside(Int is x, Int is y){
		if({ !acOpen }, { return false; });
		if({ acPopupRect:contains(px: x, py: y) || :contains(x: x, y: y) }, { return false; });
		:acOpen: false;
		:acHighlight: -1;
		:acHover: -1;
		invalidate();
		return true;
	}

	replace Function of Boolean is onOverlayPointerMove(Int is x, Int is y){
		if({ !acOpen }, { return false; });
		if({ !acPopupRect:contains(px: x, py: y) }, {
			if({ acHover != -1 }, {
				:acHover: -1;
				invalidate();
				return true;
			});
			return false;
		});
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is rh: :acRowHeightPx();
		local Int is idx: (y - (acPopupRect:y + bw)) / rh;
		local Int is vis: suggestions:length();
		if({ vis > autocompleteMaxVisible }, { vis: autocompleteMaxVisible; });
		if({ idx < 0 || idx >= vis }, { idx: -1; });
		if({ idx != acHover }, {
			:acHover: idx;
			if({ idx >= 0 }, { :acHighlight: idx; });
			invalidate();
		});
		return true;
	}

	replace Function of Boolean is onOverlayPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ !acOpen }, { return false; });
		if({ !acPopupRect:contains(px: x, py: y) }, { return false; });
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is rh: :acRowHeightPx();
		local Int is idx: (y - (acPopupRect:y + bw)) / rh;
		local Int is vis: suggestions:length();
		if({ vis > autocompleteMaxVisible }, { vis: autocompleteMaxVisible; });
		if({ idx >= 0 && idx < vis }, {
			:acceptAutocomplete(idx: idx);
		});
		return true;
	}

	replace Function is paintOverlay(DrawContext is ctx){
		if({ !acOpen || suggestions:length() == 0 }, { return; });
		:layoutAcPopup(viewW: ctx:canvas:width, viewH: ctx:canvas:height);
		local Rect is pr: acPopupRect;
		if({ pr:width <= 0 || pr:height <= 0 }, { return; });
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is radPx: activeScale:px(pt: activeTheme:panelCornerRadiusPt);
		ctx:drawStyledBox(
			x: pr:x, y: pr:y, w: pr:width, h: pr:height,
			bgColor: activeTheme:panelBg, borderColor: activeTheme:panelBorderColorArgb(),
			thickness: bw, radius: radPx, style: activeTheme:panelBorderStyle
		);
		local Int is rh: :acRowHeightPx();
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is padX: activeScale:px(pt: activeTheme:paddingPt);
		local Int is vis: suggestions:length();
		if({ vis > autocompleteMaxVisible }, { vis: autocompleteMaxVisible; });
		ctx:setClip(x: pr:x + bw, y: pr:y + bw, w: pr:width - bw * 2, h: pr:height - bw * 2);
		local Int is i: 0;
		while({ i < vis }, {
			local Int is ry: pr:y + bw + i * rh;
			local Boolean is isHi: (i == acHighlight || i == acHover);
			if({ isHi }, {
				local FillStyle is rowFill: activeTheme:resolveButtonFill(enabled: true, selected: (i == acHighlight), hovered: (i == acHover), focused: false);
				ctx:drawStyledBoxFill(
					x: pr:x + bw, y: ry, w: pr:width - bw * 2, h: rh,
					fill: rowFill, borderColor: 0, thickness: 0, radius: 0,
					style: activeTheme:buttonBorderStyle
				);
			});
			ctx:drawText(
				x: pr:x + bw + padX,
				y: ry + (rh - th) / 2,
				text: suggestions:get(index: i),
				color: activeTheme:textPrimary,
				pixelHeight: fpx
			);
			i: i + 1;
		});
		ctx:clearClip();
	}
}