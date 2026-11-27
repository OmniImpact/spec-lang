#! Package base:scrap
#! Interactive calendar month grid (`SewNode`) backed by [DateTime] for selecting calendar dates.

Class of SewNode is DateSelector{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', DateTime],
		['base', 'sys', as DateTime()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext],
		['base', 'fabric', 'svg', SvgRenderer]
	];

	DateTime is value: DateTime:now();
	Int is viewYear: 2026;
	Int is viewMonth: 1;
	Int is hoverPart: 0;
	String is prevIconSvg: '';
	String is nextIconSvg: '';
	Function is onChange: local Function(DateTime is _dt){};

	replace Function is init(
		DateTime is value: DateTime:now(),
		String is prevIconSvg: '',
		String is nextIconSvg: '',
		Function is onChange: local Function(DateTime is _dt){},
		String is tooltip: ''
	){
		:value: value;
		:viewYear: value:getYear();
		:viewMonth: value:getMonth();
		:prevIconSvg: prevIconSvg;
		:nextIconSvg: nextIconSvg;
		:onChange: onChange;
		:hoverPart: 0;
		:tooltip: tooltip;
	}

	Function is setValue(DateTime is next){
		:value: next;
		:viewYear: next:getYear();
		:viewMonth: next:getMonth();
		invalidate();
	}

	local Function is stepMonth(Int is delta){
		local DateTime is shifted: DateTime:of(year: viewYear, month: viewMonth, day: 1):addMonths(months: delta);
		:viewYear: shifted:getYear();
		:viewMonth: shifted:getMonth();
		invalidate();
	}

	local Function is selectDay(Int is day){
		:value: value:withDate(year: viewYear, month: viewMonth, day: day);
		local Function is cb: onChange;
		cb(value);
		invalidate();
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 13.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Int is cellSizePx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 14.0) + activeTheme:paddingPt * 2.5);
		return if({ px < 22 }, { 22 }, { px });
	}

	local Function of Int is padPx(){
		return activeScale:px(pt: activeTheme:paddingPt);
	}

	local Function of Rect is prevRect(Rect is b){
		local Int is pad: :padPx();
		local Int is cs: :cellSizePx();
		return Rect(x: b:x + pad, y: b:y + pad, width: cs, height: cs);
	}

	local Function of Rect is nextRect(Rect is b){
		local Int is pad: :padPx();
		local Int is cs: :cellSizePx();
		return Rect(x: b:x + b:width - pad - cs, y: b:y + pad, width: cs, height: cs);
	}

	local Function of Rect is todayRect(Rect is b){
		local Int is pad: :padPx();
		local Int is cs: :cellSizePx();
		local Int is tw: cs * 2;
		return Rect(x: b:x + b:width - pad - cs - pad / 2 - tw, y: b:y + pad, width: tw, height: cs);
	}

	local Function of Boolean is inRect(Rect is r, Int is x, Int is y){
		return x >= r:x && x < r:x + r:width && y >= r:y && y < r:y + r:height;
	}

	local Function of Int is hitPartAt(Int is x, Int is y){
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return 0; });
		if({ :inRect(r: :prevRect(b: b), x: x, y: y) }, { return 1; });
		if({ :inRect(r: :nextRect(b: b), x: x, y: y) }, { return 2; });
		if({ :inRect(r: :todayRect(b: b), x: x, y: y) }, { return 3; });

		local Int is pad: :padPx();
		local Int is cs: :cellSizePx();
		local Int is gridX: b:x + pad;
		local Int is gridY: b:y + pad + cs + (cs * 7) / 10 + pad;
		if({ x < gridX || x >= gridX + cs * 7 || y < gridY || y >= gridY + cs * 6 }, { return 0; });
		local Int is col: (x - gridX) / cs;
		local Int is row: (y - gridY) / cs;
		local Int is slot: row * 7 + col;
		local Int is firstDow: DateTime:firstDayOfMonthDow(year: viewYear, month: viewMonth);
		local Int is dim: DateTime:daysInMonth(y: viewYear, m: viewMonth);
		local Int is day: slot - firstDow + 1;
		if({ day >= 1 && day <= dim }, {
			return 10 + day;
		});
		return 0;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is pad: :padPx();
		local Int is cs: :cellSizePx();
		local Int is dowH: (cs * 7) / 10;
		local Int is w: pad * 2 + cs * 7;
		local Int is h: pad * 3 + cs + dowH + cs * 6;
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });

		local Int is pad: :padPx();
		local Int is cs: :cellSizePx();
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is btnPx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
		local Int is radPx: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
		local Int is panelPx: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);

		ctx:drawStyledBox(
			x: b:x, y: b:y, w: b:width, h: b:height,
			bgColor: activeTheme:panelBg, borderColor: activeTheme:panelBorderColorArgb(),
			thickness: panelPx, radius: radPx, style: activeTheme:panelBorderStyle
		);

		local Rect is pr: :prevRect(b: b);
		local Rect is nr: :nextRect(b: b);
		local Rect is tr: :todayRect(b: b);

		ctx:drawStyledBoxFill(
			x: pr:x, y: pr:y, w: pr:width, h: pr:height,
			fill: activeTheme:resolveButtonFill(enabled: true, selected: false, hovered: hoverPart == 1),
			borderColor: activeTheme:buttonBorderColorArgb(), thickness: btnPx, radius: radPx, style: activeTheme:buttonBorderStyle
		);
		if({ prevIconSvg != '' }, {
			local Int is isz: (pr:height * 60) / 100;
			if({ isz < 10 }, { isz: 10; });
			SvgRenderer:shared:draw(ctx: ctx, svgSrc: prevIconSvg, x: pr:x + (pr:width - isz) / 2, y: pr:y + (pr:height - isz) / 2, widthPx: isz, heightPx: isz, tintColor: activeTheme:textPrimary, useTint: true);
		}, {
			local Int is pw: ctx:measureTextWidth(text: '◀', pixelHeight: fpx);
			ctx:drawText(x: pr:x + (pr:width - pw) / 2, y: pr:y + (pr:height - th) / 2, text: '◀', color: activeTheme:textPrimary, pixelHeight: fpx);
		});

		ctx:drawStyledBoxFill(
			x: nr:x, y: nr:y, w: nr:width, h: nr:height,
			fill: activeTheme:resolveButtonFill(enabled: true, selected: false, hovered: hoverPart == 2),
			borderColor: activeTheme:buttonBorderColorArgb(), thickness: btnPx, radius: radPx, style: activeTheme:buttonBorderStyle
		);
		if({ nextIconSvg != '' }, {
			local Int is isz: (nr:height * 60) / 100;
			if({ isz < 10 }, { isz: 10; });
			SvgRenderer:shared:draw(ctx: ctx, svgSrc: nextIconSvg, x: nr:x + (nr:width - isz) / 2, y: nr:y + (nr:height - isz) / 2, widthPx: isz, heightPx: isz, tintColor: activeTheme:textPrimary, useTint: true);
		}, {
			local Int is nw: ctx:measureTextWidth(text: '▶', pixelHeight: fpx);
			ctx:drawText(x: nr:x + (nr:width - nw) / 2, y: nr:y + (nr:height - th) / 2, text: '▶', color: activeTheme:textPrimary, pixelHeight: fpx);
		});

		ctx:drawStyledBoxFill(
			x: tr:x, y: tr:y, w: tr:width, h: tr:height,
			fill: activeTheme:resolveButtonFill(enabled: true, selected: false, hovered: hoverPart == 3),
			borderColor: activeTheme:buttonBorderColorArgb(), thickness: btnPx, radius: radPx, style: activeTheme:buttonBorderStyle
		);
		local Int is tdw: ctx:measureTextWidth(text: 'Today', pixelHeight: fpx);
		ctx:drawText(x: tr:x + (tr:width - tdw) / 2, y: tr:y + (tr:height - th) / 2, text: 'Today', color: activeTheme:textPrimary, pixelHeight: fpx);

		local String is title: DateTime:monthShortName(month: viewMonth) . ' ' . (viewYear as String);
		ctx:drawText(x: pr:x + pr:width + pad, y: pr:y + (pr:height - th) / 2, text: title, color: activeTheme:textPrimary, pixelHeight: fpx);

		local Int is gridX: b:x + pad;
		local Int is dowY: b:y + pad + cs + pad / 2;
		local Int is dowH: (cs * 7) / 10;
		local Int is dwIdx: 0;
		while({ dwIdx < 7 }, {
			local String is wd: DateTime:weekdayShortName(dow: dwIdx);
			local Int is wdw: ctx:measureTextWidth(text: wd, pixelHeight: fpx);
			local Int is cx: gridX + dwIdx * cs;
			ctx:drawText(x: cx + (cs - wdw) / 2, y: dowY + (dowH - th) / 2, text: wd, color: activeTheme:textMuted, pixelHeight: fpx);
			dwIdx: dwIdx + 1;
		});

		local Int is gridY: b:y + pad + cs + dowH + pad;
		local Int is firstDow: DateTime:firstDayOfMonthDow(year: viewYear, month: viewMonth);
		local Int is dim: DateTime:daysInMonth(y: viewYear, m: viewMonth);
		local DateTime is today: DateTime:now();
		local Int is day: 1;
		while({ day <= dim }, {
			local Int is slot: firstDow + day - 1;
			local Int is col: slot % 7;
			local Int is row: slot / 7;
			local Int is cx: gridX + col * cs;
			local Int is cy: gridY + row * cs;
			local Boolean is isSel: value:getYear() == viewYear && value:getMonth() == viewMonth && value:getDay() == day;
			local Boolean is isToday: today:getYear() == viewYear && today:getMonth() == viewMonth && today:getDay() == day;
			local Boolean is isHov: hoverPart == 10 + day;

			if({ isSel || isHov || isToday }, {
				local FillStyle is cellFill: activeTheme:resolveButtonFill(enabled: true, selected: isSel, hovered: isHov);
				local Int is bCol: if({ isToday }, { activeTheme:textAccent }, { activeTheme:buttonBorderColorArgb() });
				local Int is bThk: if({ isToday || isSel }, { if({ btnPx > 0 }, { btnPx }, { 1 }) }, { 0 });
				ctx:drawStyledBoxFill(
					x: cx + 1, y: cy + 1, w: cs - 2, h: cs - 2,
					fill: cellFill, borderColor: bCol, thickness: bThk, radius: radPx, style: activeTheme:buttonBorderStyle
				);
			});

			local String is ds: day as String;
			local Int is dsw: ctx:measureTextWidth(text: ds, pixelHeight: fpx);
			ctx:drawText(x: cx + (cs - dsw) / 2, y: cy + (cs - th) / 2, text: ds, color: activeTheme:textPrimary, pixelHeight: fpx);
			day: day + 1;
		});
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
		if({ part == 1 }, { :stepMonth(delta: -1); return true; });
		if({ part == 2 }, { :stepMonth(delta: 1); return true; });
		if({ part == 3 }, {
			local DateTime is now: DateTime:now();
			:viewYear: now:getYear();
			:viewMonth: now:getMonth();
			:value: value:withDate(year: viewYear, month: viewMonth, day: now:getDay());
			local Function is cb: onChange;
			cb(value);
			invalidate();
			return true;
		});
		if({ part >= 10 }, {
			:selectDay(day: part - 10);
			return true;
		});
		return false;
	}
}
