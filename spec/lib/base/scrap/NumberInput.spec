#! Package base:scrap
#! Numeric stepper / SpinBox widget with decrement/increment buttons, direct text entry, and wheel/arrow support.

Class of SewNode is NumberInput{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', Time],
		['base', 'fabric', Theme],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale]
	];

	Float is value: 0.0;
	Float is minVal: 0.0;
	Float is maxVal: 100.0;
	Float is step: 1.0;
	Int is decimals: 0;
	String is suffix: '';
	Float is minWidthPt: 110.0;
	Float is heightPt: 0.0;
	Function is onChange: local Function(Float is _next){};

	Boolean is hovered: false;
	Boolean is focused: false;
	Int is hoverZone: 0;
	Boolean is editing: false;
	String is editBuffer: '';
	Boolean is allSelected: false;
	Boolean is caretVisible: true;
	Int is caretBlinkMs: 0;
	Int is lastClickMs: 0;
	Int is clickStreak: 0;
	Time is clock: Time();

	replace Function is init(
		Float is value: 0.0,
		Float is minVal: 0.0,
		Float is maxVal: 100.0,
		Float is step: 1.0,
		Int is decimals: 0,
		String is suffix: '',
		Float is minWidthPt: 110.0,
		Float is heightPt: 0.0,
		String is tooltip: '',
		Function is onChange: local Function(Float is _next){}
	){
		:minVal: minVal;
		:maxVal: maxVal;
		:step: step;
		:decimals: decimals;
		:suffix: suffix;
		:minWidthPt: minWidthPt;
		:heightPt: heightPt;
		:tooltip: tooltip;
		:onChange: onChange;
		:value: :clampVal(v: value);
	}

	local Function of Float is clampVal(Float is v){
		if({ v < minVal }, { return minVal; });
		if({ v > maxVal }, { return maxVal; });
		return v;
	}

	Function is setValue(Float is next){
		:value: :clampVal(v: next);
		:editing: false;
		:invalidate();
	}

	local Function of Int is roundFloat(Float is v){
		if({ v >= 0.0 }, { return (v + 0.5) as Int; });
		return (v - 0.5) as Int;
	}

	local Function of String is formatValue(Float is v){
		if({ decimals <= 0 }, {
			local Int is iv: :roundFloat(v: v);
			return (iv as String) . suffix;
		});
		local Float is mult: 1.0;
		local Int is d: 0;
		while({ d < decimals }, {
			mult: mult * 10.0;
			d: d + 1;
		});
		local Int is scaled: :roundFloat(v: v * mult);
		local Boolean is neg: scaled < 0;
		if({ neg }, { scaled: 0 - scaled; });
		local Int is imult: :roundFloat(v: mult);
		local Int is whole: scaled / imult;
		local Int is frac: scaled - whole * imult;
		local String is fracStr: frac as String;
		while({ fracStr:length() < decimals }, {
			fracStr: '0' . fracStr;
		});
		local String is sign: if({ neg && (whole > 0 || frac > 0) }, { '-' }, { '' });
		return sign . (whole as String) . '.' . fracStr . suffix;
	}

	local Function of Float is parseBuffer(String is s){
		local Int is n: s:runeCount();
		if({ n == 0 }, { return value; });
		local Int is i: 0;
		local Boolean is neg: false;
		if({ s:codePointAtRune(runeIndex: 0) == 45 }, {
			neg: true;
			i: 1;
		}, {
		if({ s:codePointAtRune(runeIndex: 0) == 43 }, {
			i: 1;
		}); });
		local Float is intPart: 0.0;
		local Float is fracPart: 0.0;
		local Float is fracDiv: 1.0;
		local Boolean is seenDot: false;
		local Boolean is seenDigit: false;
		while({ i < n }, {
			local Int is cp: s:codePointAtRune(runeIndex: i);
			if({ cp >= 48 && cp <= 57 }, {
				seenDigit: true;
				local Float is digit: (cp - 48) as Float;
				if({ seenDot }, {
					fracDiv: fracDiv * 10.0;
					fracPart: fracPart + digit / fracDiv;
				}, {
					intPart: intPart * 10.0 + digit;
				});
			}, {
			if({ cp == 46 && !seenDot }, {
				seenDot: true;
			}); });
			i: i + 1;
		});
		if({ !seenDigit }, { return value; });
		local Float is res: intPart + fracPart;
		if({ neg }, { res: 0.0 - res; });
		return :clampVal(v: res);
	}

	local Function is commitEdit(){
		if({ !editing }, { return; });
		local Float is next: :parseBuffer(s: editBuffer);
		:editing: false;
		if({ next != value }, {
			:value: next;
			local Function is cb: :onChange;
			cb(value);
		});
		:invalidate();
	}

	local Function is stepBy(Float is delta){
		if({ editing }, { :commitEdit(); });
		local Float is next: :clampVal(v: value + delta);
		if({ next != value }, {
			:value: next;
			local Function is cb: :onChange;
			cb(value);
			:invalidate();
		});
	}

	local Function of Int is btnWidthPx(){
		local Int is bh: bounds():height;
		if({ bh > 0 }, { return bh; });
		return activeScale:px(pt: activeTheme:buttonHeightPt);
	}

	local Function of Int is zoneAtX(Int is x){
		local Rect is b: bounds();
		local Int is bw: :btnWidthPx();
		if({ bw * 2 >= b:width }, { bw: b:width / 3; });
		if({ x < b:x + bw }, { return 1; });
		if({ x >= b:x + b:width - bw }, { return 3; });
		return 2;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is minW: activeScale:px(pt: minWidthPt);
		local Int is h: if({ heightPt > 0.0 }, {
			activeScale:px(pt: heightPt)
		}, {
			activeScale:px(pt: activeTheme:buttonHeightPt)
		});
		desiredSize: Size(width: c:clampW(w: minW), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is btnPx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
		local Int is divPx: activeTheme:dividerPx(scaleFactor: activeScale:factor);
		local Int is radPx: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
		local FillStyle is fill: activeTheme:resolveButtonFill(
			enabled: true, selected: false, hovered: hovered, focused: focused
		);
		local Int is borderCol: if({ focused }, { activeTheme:textAccent }, { activeTheme:buttonBorderColorArgb() });
		ctx:drawStyledBoxFill(
			x: b:x, y: b:y, w: b:width, h: b:height,
			fill: fill, borderColor: borderCol, thickness: btnPx, radius: radPx,
			style: activeTheme:buttonBorderStyle
		);

		local Int is bw: :btnWidthPx();
		if({ bw * 2 >= b:width }, { bw: b:width / 3; });
		local Int is fpx: activeScale:px(pt: activeTheme:baseTextPt);
		if({ fpx < 10 }, { fpx: 10; });
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);

		# Minus button
		if({ hoverZone == 1 }, {
			ctx:fillRect(x: b:x + btnPx, y: b:y + btnPx, w: bw - btnPx, h: b:height - btnPx * 2, color: activeTheme:hoverBg);
		});
		local Int is minusW: ctx:measureTextWidth(text: '−', pixelHeight: fpx);
		ctx:drawText(
			x: b:x + (bw - minusW) / 2,
			y: b:y + (b:height - th) / 2,
			text: '−',
			color: if({ value <= minVal }, { activeTheme:textMuted }, { activeTheme:textPrimary }),
			pixelHeight: fpx
		);

		# Plus button
		local Int is plusX: b:x + b:width - bw;
		if({ hoverZone == 3 }, {
			ctx:fillRect(x: plusX, y: b:y + btnPx, w: bw - btnPx, h: b:height - btnPx * 2, color: activeTheme:hoverBg);
		});
		local Int is plusW: ctx:measureTextWidth(text: '+', pixelHeight: fpx);
		ctx:drawText(
			x: plusX + (bw - plusW) / 2,
			y: b:y + (b:height - th) / 2,
			text: '+',
			color: if({ value >= maxVal }, { activeTheme:textMuted }, { activeTheme:textPrimary }),
			pixelHeight: fpx
		);

		# Dividers
		if({ divPx > 0 }, {
			ctx:drawDivider(x: b:x + bw, y: b:y + btnPx, w: divPx, h: b:height - btnPx * 2, color: activeTheme:dividerColorArgb(), thickness: divPx, style: activeTheme:dividerStyle);
			ctx:drawDivider(x: plusX - divPx, y: b:y + btnPx, w: divPx, h: b:height - btnPx * 2, color: activeTheme:dividerColorArgb(), thickness: divPx, style: activeTheme:dividerStyle);
		});

		# Center value text
		local Int is centerX: b:x + bw + divPx;
		local Int is centerW: b:width - bw * 2 - divPx * 2;
		if({ centerW > 0 }, {
			local String is txt: if({ editing }, { editBuffer }, { :formatValue(v: value) });
			local Int is tw: ctx:measureTextWidth(text: txt, pixelHeight: fpx);
			ctx:setClip(x: centerX, y: b:y, w: centerW, h: b:height);
			local Int is tx: centerX + (centerW - tw) / 2;
			if({ tx < centerX + 4 }, { tx: centerX + 4; });
			if({ focused && editing && allSelected && tw > 0 }, {
				ctx:fillRect(x: tx, y: b:y + (b:height - th) / 2, w: tw, h: th, color: activeTheme:highlight:toArgb());
			});
			ctx:drawText(
				x: tx,
				y: b:y + (b:height - th) / 2,
				text: txt,
				color: activeTheme:textPrimary,
				pixelHeight: fpx,
				bold: false,
				italic: false,
				mono: true
			);
			if({ focused && editing && caretVisible }, {
				local Int is cx: tx + tw + 1;
				if({ cx >= centerX && cx < centerX + centerW }, {
					ctx:fillRect(x: cx, y: b:y + (b:height - th) / 2, w: 1, h: th, color: activeTheme:textAccent);
				});
			});
			ctx:clearClip();
		});
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is inside: :containsPoint(x: x, y: y);
		local Int is z: if({ inside }, { :zoneAtX(x: x) }, { 0 });
		if({ inside != hovered || z != hoverZone }, {
			:hovered: inside;
			:hoverZone: z;
			:invalidate();
		});
		return inside;
	}

	replace Function is clearHover(){
		if({ hovered || hoverZone != 0 }, {
			:hovered: false;
			:hoverZone: 0;
			:invalidate();
		});
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ !:containsPoint(x: x, y: y) }, {
			if({ editing }, { :commitEdit(); });
			return false;
		});
		local Int is z: :zoneAtX(x: x);
		if({ z == 1 }, {
			:stepBy(delta: 0.0 - step);
			return true;
		});
		if({ z == 3 }, {
			:stepBy(delta: step);
			return true;
		});
		local Int is nowMs: clock:monotonicMs();
		if({ lastClickMs > 0 && (nowMs - lastClickMs) <= 450 }, {
			:clickStreak: clickStreak + 1;
			if({ clickStreak > 3 }, { :clickStreak: 1; });
		}, {
			:clickStreak: 1;
		});
		:lastClickMs: nowMs;
		if({ !editing }, {
			:editing: true;
			local Int is iv: :roundFloat(v: value);
			:editBuffer: if({ decimals <= 0 }, { iv as String }, { :formatValue(v: value) });
		});
		:allSelected: clickStreak >= 2;
		:caretVisible: true;
		:caretBlinkMs: 0;
		:invalidate();
		return true;
	}

	replace Function of Boolean is tick(Int is nowMs){
		if({ !focused || !editing }, {
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
		if({ !hovered }, { return false; });
		if({ deltaY > 0 }, {
			:stepBy(delta: step);
		}, {
		if({ deltaY < 0 }, {
			:stepBy(delta: 0.0 - step);
		}); });
		return true;
	}

	replace Function of Boolean is onText(String is ch, Int is mods){
		if({ !focused || ch == '' }, { return false; });
		if({ !editing }, {
			:editing: true;
			:editBuffer: '';
		});
		local Int is cp: ch:codePointAtRune(runeIndex: 0);
		local Boolean is ok: (cp >= 48 && cp <= 57) || cp == 46 || cp == 45;
		if({ ok }, {
			if({ allSelected }, {
				:editBuffer: ch;
				:allSelected: false;
			}, {
				:editBuffer: editBuffer . ch;
			});
			:caretVisible: true;
			:caretBlinkMs: 0;
			:invalidate();
		});
		return true;
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		if({ !focused }, { return false; });
		if({ key == 1001 || key == 111 }, {
			:stepBy(delta: step);
			return true;
		});
		if({ key == 1002 || key == 116 }, {
			:stepBy(delta: 0.0 - step);
			return true;
		});
		if({ key == 10 || key == 13 || key == 36 }, {
			:commitEdit();
			return true;
		});
		if({ key == 27 || key == 9 }, {
			:editing: false;
			:invalidate();
			return true;
		});
		if({ (key == 8 || key == 22) && editing }, {
			if({ allSelected }, {
				:editBuffer: '';
				:allSelected: false;
				:caretVisible: true;
				:caretBlinkMs: 0;
				:invalidate();
			}, {
				local Int is n: editBuffer:length();
				if({ n > 0 }, {
					:editBuffer: editBuffer:substring(start: 0, end: n - 1);
					:caretVisible: true;
					:caretBlinkMs: 0;
					:invalidate();
				});
			});
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
		if({ !next && editing }, { :commitEdit(); });
		:focused: next;
		:invalidate();
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ !:containsPoint(x: x, y: y) }, { return CursorShape:DEFAULT; });
		local Int is z: :zoneAtX(x: x);
		if({ z == 1 || z == 3 }, { return CursorShape:POINTER; });
		return CursorShape:TEXT;
	}
}
