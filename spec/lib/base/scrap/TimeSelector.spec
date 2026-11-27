#! Package base:scrap
#! Interactive wall-clock time picker (`SewNode`) backed by [DateTime] supporting 12h/24h and optional seconds.

Class of SewNode is TimeSelector{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', DateTime],
		['base', 'sys', as DateTime()],
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext]
	];

	DateTime is value: DateTime:now();
	Boolean is use24Hour: false;
	Boolean is showSeconds: false;
	Int is hoverPart: 0;
	Function is onChange: local Function(DateTime is _dt){};

	replace Function is init(
		DateTime is value: DateTime:now(),
		Boolean is use24Hour: false,
		Boolean is showSeconds: false,
		Function is onChange: local Function(DateTime is _dt){},
		String is tooltip: ''
	){
		:value: value;
		:use24Hour: use24Hour;
		:showSeconds: showSeconds;
		:onChange: onChange;
		:hoverPart: 0;
		:tooltip: tooltip;
	}

	Function is setValue(DateTime is next){
		:value: next;
		invalidate();
	}

	local Function is emitValue(DateTime is next){
		:value: next;
		local Function is cb: onChange;
		cb(value);
		invalidate();
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 14.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Int is colW(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 14.0) + activeTheme:paddingPt * 4.5);
		return if({ px < 28 }, { 28 }, { px });
	}

	local Function of Int is btnH(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 14.0) + activeTheme:paddingPt * 1.75);
		return if({ px < 20 }, { 20 }, { px });
	}

	local Function of Int is padPx(){
		return activeScale:px(pt: activeTheme:paddingPt);
	}

	local Function of String is pad2(Int is n){
		return if({ n < 10 }, { '0' . (n as String) }, { n as String });
	}

	local Function of Boolean is inRect(Rect is r, Int is x, Int is y){
		return x >= r:x && x < r:x + r:width && y >= r:y && y < r:y + r:height;
	}

	local Function of Rect is partRect(Rect is b, Int is part){
		local Int is pad: :padPx();
		local Int is cw: :colW();
		local Int is bh: :btnH();
		local Int is gap: pad / 2;
		if({ gap < 2 }, { gap: 2; });
		local Int is yUp: b:y + pad;
		local Int is yVal: yUp + bh + gap;
		local Int is yDn: yVal + bh + gap;
		local Int is sepW: pad;
		local Int is hx: b:x + pad;
		local Int is mx: hx + cw + sepW;
		local Int is sx: mx + cw + sepW;
		local Int is ax: if({ showSeconds }, { sx + cw + pad }, { mx + cw + pad });

		if({ part == 1 }, { return Rect(x: hx, y: yUp, width: cw, height: bh); });
		if({ part == 2 }, { return Rect(x: hx, y: yDn, width: cw, height: bh); });
		if({ part == 3 }, { return Rect(x: mx, y: yUp, width: cw, height: bh); });
		if({ part == 4 }, { return Rect(x: mx, y: yDn, width: cw, height: bh); });
		if({ part == 5 }, { return Rect(x: sx, y: yUp, width: cw, height: bh); });
		if({ part == 6 }, { return Rect(x: sx, y: yDn, width: cw, height: bh); });
		if({ part == 7 }, { return Rect(x: ax, y: yVal, width: cw + pad, height: bh); });
		if({ part == 8 }, { return Rect(x: ax, y: yDn, width: cw + pad, height: bh); });
		return Rect();
	}

	local Function of Int is hitPartAt(Int is x, Int is y){
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return 0; });
		local Int is p: 1;
		local Int is maxP: 8;
		while({ p <= maxP }, {
			local Boolean is activePart: true;
			if({ (p == 5 || p == 6) && !showSeconds }, { activePart: false; });
			if({ p == 7 && use24Hour }, { activePart: false; });
			if({ activePart && :inRect(r: :partRect(b: b, part: p), x: x, y: y) }, {
				return p;
			});
			p: p + 1;
		});
		return 0;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is pad: :padPx();
		local Int is cw: :colW();
		local Int is bh: :btnH();
		local Int is gap: pad / 2;
		if({ gap < 2 }, { gap: 2; });
		local Int is cols: if({ showSeconds }, { 3 }, { 2 });
		local Int is w: pad * 2 + cols * cw + (cols - 1) * pad + pad + cw + pad;
		local Int is h: pad * 2 + bh * 3 + gap * 2;
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	local Function is drawBtn(DrawContext is ctx, Rect is r, String is lbl, Boolean is hov, Boolean is sel: false){
		local Int is btnPx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
		local Int is radPx: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		ctx:drawStyledBoxFill(
			x: r:x, y: r:y, w: r:width, h: r:height,
			fill: activeTheme:resolveButtonFill(enabled: true, selected: sel, hovered: hov),
			borderColor: activeTheme:buttonBorderColorArgb(), thickness: btnPx, radius: radPx, style: activeTheme:buttonBorderStyle
		);
		local Int is tw: ctx:measureTextWidth(text: lbl, pixelHeight: fpx);
		ctx:drawText(x: r:x + (r:width - tw) / 2, y: r:y + (r:height - th) / 2, text: lbl, color: activeTheme:textPrimary, pixelHeight: fpx);
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });

		local Int is pad: :padPx();
		local Int is cw: :colW();
		local Int is bh: :btnH();
		local Int is gap: pad / 2;
		if({ gap < 2 }, { gap: 2; });
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is radPx: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
		local Int is panelPx: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);

		ctx:drawStyledBox(
			x: b:x, y: b:y, w: b:width, h: b:height,
			bgColor: activeTheme:panelBg, borderColor: activeTheme:panelBorderColorArgb(),
			thickness: panelPx, radius: radPx, style: activeTheme:panelBorderStyle
		);

		local Int is yVal: b:y + pad + bh + gap;
		local Int is hx: b:x + pad;
		local Int is mx: hx + cw + pad;
		local Int is sx: mx + cw + pad;

		:drawBtn(ctx: ctx, r: :partRect(b: b, part: 1), lbl: '+', hov: hoverPart == 1);
		:drawBtn(ctx: ctx, r: :partRect(b: b, part: 2), lbl: '-', hov: hoverPart == 2);
		local String is hTxt: :pad2(n: if({ use24Hour }, { value:getHour() }, { value:hour12() }));
		local Int is htw: ctx:measureTextWidth(text: hTxt, pixelHeight: fpx);
		ctx:drawText(x: hx + (cw - htw) / 2, y: yVal + (bh - th) / 2, text: hTxt, color: activeTheme:textPrimary, pixelHeight: fpx);

		local Int is colw: ctx:measureTextWidth(text: ':', pixelHeight: fpx);
		ctx:drawText(x: hx + cw + (pad - colw) / 2, y: yVal + (bh - th) / 2, text: ':', color: activeTheme:textMuted, pixelHeight: fpx);

		:drawBtn(ctx: ctx, r: :partRect(b: b, part: 3), lbl: '+', hov: hoverPart == 3);
		:drawBtn(ctx: ctx, r: :partRect(b: b, part: 4), lbl: '-', hov: hoverPart == 4);
		local String is mTxt: :pad2(n: value:getMinute());
		local Int is mtw: ctx:measureTextWidth(text: mTxt, pixelHeight: fpx);
		ctx:drawText(x: mx + (cw - mtw) / 2, y: yVal + (bh - th) / 2, text: mTxt, color: activeTheme:textPrimary, pixelHeight: fpx);

		if({ showSeconds }, {
			ctx:drawText(x: mx + cw + (pad - colw) / 2, y: yVal + (bh - th) / 2, text: ':', color: activeTheme:textMuted, pixelHeight: fpx);
			:drawBtn(ctx: ctx, r: :partRect(b: b, part: 5), lbl: '+', hov: hoverPart == 5);
			:drawBtn(ctx: ctx, r: :partRect(b: b, part: 6), lbl: '-', hov: hoverPart == 6);
			local String is sTxt: :pad2(n: value:getSecond());
			local Int is stw: ctx:measureTextWidth(text: sTxt, pixelHeight: fpx);
			ctx:drawText(x: sx + (cw - stw) / 2, y: yVal + (bh - th) / 2, text: sTxt, color: activeTheme:textPrimary, pixelHeight: fpx);
		});

		if({ !use24Hour }, {
			local String is apTxt: if({ value:isPm() }, { 'PM' }, { 'AM' });
			:drawBtn(ctx: ctx, r: :partRect(b: b, part: 7), lbl: apTxt, hov: hoverPart == 7, sel: value:isPm());
		});
		:drawBtn(ctx: ctx, r: :partRect(b: b, part: 8), lbl: 'Now', hov: hoverPart == 8);
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Int is next: :hitPartAt(x: x, y: y);
		if({ next != hoverPart }, {
			:hoverPart: next;
			invalidate();
			return true;
		});
		return false;
	}

	replace Function is clearHover(){
		if({ hoverPart != 0 }, {
			:hoverPart: 0;
			invalidate();
		});
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Int is part: :hitPartAt(x: x, y: y);
		if({ part == 0 }, { return false; });
		local Int is h: value:getHour();
		local Int is m: value:getMinute();
		local Int is s: value:getSecond();
		if({ part == 1 }, { :emitValue(next: value:withTime(hour: (h + 1) % 24, minute: m, second: s)); return true; });
		if({ part == 2 }, { :emitValue(next: value:withTime(hour: (h + 23) % 24, minute: m, second: s)); return true; });
		if({ part == 3 }, { :emitValue(next: value:withTime(hour: h, minute: (m + 1) % 60, second: s)); return true; });
		if({ part == 4 }, { :emitValue(next: value:withTime(hour: h, minute: (m + 59) % 60, second: s)); return true; });
		if({ part == 5 }, { :emitValue(next: value:withTime(hour: h, minute: m, second: (s + 1) % 60)); return true; });
		if({ part == 6 }, { :emitValue(next: value:withTime(hour: h, minute: m, second: (s + 59) % 60)); return true; });
		if({ part == 7 }, {
			local Int is nh: if({ h >= 12 }, { h - 12 }, { h + 12 });
			:emitValue(next: value:withTime(hour: nh, minute: m, second: s));
			return true;
		});
		if({ part == 8 }, {
			local DateTime is now: DateTime:now();
			:emitValue(next: value:withTime(hour: now:getHour(), minute: now:getMinute(), second: now:getSecond()));
			return true;
		});
		return false;
	}
}
