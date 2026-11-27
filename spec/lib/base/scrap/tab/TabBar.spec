#! Package base:scrap
#! Horizontal tab bar (`SewNode`) with min/max tab widths, optional close ('X') buttons, and right-click support.

Class of SewNode is TabBar{
	replace [String] is namespace: ['base', 'scrap', 'tab'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', DockSide],
		['base', 'fabric', DrawContext],
		['base', 'scrap', 'tab', TabItemConfig]
	];

	Array of TabItemConfig is tabs: Array();
	Int is activeIndex: 0;
	Float is heightPt: 0.0;
	Float is outerPadPt: -1.0;
	DockSide is dockSide: DockSide:TOP;
	Float is minTabWidthPt: 0.0;
	Float is maxTabWidthPt: 0.0;
	Boolean is showCloseButton: true;
	Function is onSelectTab: local Function(Int is _idx){};
	Function is onCloseTab: local Function(Int is _idx){};
	Function is onRightClickTab: local Function(Int is _idx, Int is _x, Int is _y){};

	Int is hoverTabIdx: -1;
	Int is hoverCloseIdx: -1;

	replace Function is init(
		Array of TabItemConfig is tabs: Array(),
		Int is activeIndex: 0,
		Float is heightPt: 0.0,
		Float is outerPadPt: -1.0,
		DockSide is dockSide: DockSide:TOP,
		Float is minTabWidthPt: 0.0,
		Float is maxTabWidthPt: 0.0,
		Boolean is showCloseButton: true,
		Function is onSelectTab: local Function(Int is _idx){},
		Function is onCloseTab: local Function(Int is _idx){},
		Function is onRightClickTab: local Function(Int is _idx, Int is _x, Int is _y){}
	){
		:tabs: tabs;
		:activeIndex: activeIndex;
		:heightPt: heightPt;
		:outerPadPt: outerPadPt;
		:dockSide: dockSide;
		:minTabWidthPt: minTabWidthPt;
		:maxTabWidthPt: maxTabWidthPt;
		:showCloseButton: showCloseButton;
		:onSelectTab: onSelectTab;
		:onCloseTab: onCloseTab;
		:onRightClickTab: onRightClickTab;
		hoverTabIdx: -1;
		hoverCloseIdx: -1;
	}

	## Replaces the visible tab list and active index, triggering a redraw.
	Function is setTabs(Array of TabItemConfig is tabs, Int is activeIndex){
		:tabs: tabs;
		:activeIndex: activeIndex;
		hoverTabIdx: -1;
		hoverCloseIdx: -1;
		invalidate();
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 14.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Int is tabWidthPx(Int is totalW){
		local Int is count: tabs:length();
		if({ count <= 0 }, { return 0; });
		local Int is minW: activeScale:px(pt: if({ minTabWidthPt > 0.0 }, { minTabWidthPt }, { activeTheme:tabMinWidthPt }));
		local Int is maxW: activeScale:px(pt: if({ maxTabWidthPt > 0.0 }, { maxTabWidthPt }, { activeTheme:tabMaxWidthPt }));
		local Int is w: totalW / count;
		if({ w > maxW }, { w: maxW; });
		if({ w < minW }, { w: minW; });
		return w;
	}

	local Function of Int is closeBoxSizePx(){
		return activeScale:px(pt: activeTheme:iconSizePt * 1.15);
	}

	local Function of Int is outerPadPx(){
		local Float is pt: if({ outerPadPt >= 0.0 }, { outerPadPt }, { activeTheme:paddingSmallPt });
		local Int is p: activeScale:px(pt: pt);
		return if({ p < 1 }, { 1 }, { p });
	}

	local Function of Rect is tabsAreaRect(Rect is b){
		local Int is p: :outerPadPx();
		if({ dockSide == DockSide:BOTTOM }, { return Rect(x: b:x, y: b:y, width: b:width, height: if({ b:height > p }, { b:height - p }, { b:height })); });
		if({ dockSide == DockSide:LEFT }, { return Rect(x: b:x + p, y: b:y, width: if({ b:width > p }, { b:width - p }, { b:width }), height: b:height); });
		if({ dockSide == DockSide:RIGHT }, { return Rect(x: b:x, y: b:y, width: if({ b:width > p }, { b:width - p }, { b:width }), height: b:height); });
		return Rect(x: b:x, y: b:y + p, width: b:width, height: if({ b:height > p }, { b:height - p }, { b:height }));
	}

	local Function of Boolean is pointInCloseBtn(Int is x, Int is y, Int is tabX, Int is tabW, Rect is area){
		if({ !showCloseButton }, { return false; });
		local Int is cs: :closeBoxSizePx();
		local Int is padR: activeScale:px(pt: activeTheme:paddingSmallPt * 2.0);
		local Int is cx: tabX + tabW - padR - cs;
		local Int is cy: area:y + (area:height - cs) / 2;
		return x >= cx && x < cx + cs && y >= cy && y < cy + cs;
	}

	local Function of String is fitLabel(String is label, Int is maxTextW, Int is fpx){
		if({ maxTextW <= 0 || label == '' }, { return ''; });
		if({ DrawContext:measureWidth(text: label, pixelHeight: fpx) <= maxTextW }, {
			return label;
		});
		local Int is ellW: DrawContext:measureWidth(text: '...', pixelHeight: fpx);
		local Int is target: maxTextW - ellW;
		if({ target <= 0 }, { return '...'; });
		local Int is endIdx: label:length() - 1;
		while({ endIdx > 0 && DrawContext:measureWidth(text: label:substring(start: 0, end: endIdx), pixelHeight: fpx) > target }, {
			endIdx: endIdx - 1;
		});
		return label:substring(start: 0, end: endIdx) . '...';
	}

	replace Function of Size is measure(Constraints is c){
		local Int is hPx: activeScale:px(pt: if({ heightPt > 0.0 }, { heightPt }, { activeTheme:tabBarHeightPt }));
		desiredSize: Size(width: c:maxW, height: c:clampH(h: hPx));
		return desiredSize;
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Rect is area: :tabsAreaRect(b: bounds());
		local Int is nextTab: -1;
		local Int is nextClose: -1;
		if({ x >= area:x && x < area:x + area:width && y >= area:y && y < area:y + area:height && tabs:length() > 0 }, {
			local Int is tw: :tabWidthPx(totalW: area:width);
			if({ tw > 0 }, {
				local Int is idx: (x - area:x) / tw;
				if({ idx >= 0 && idx < tabs:length() }, {
					nextTab: idx;
					local TabItemConfig is t: tabs:get(index: idx);
					if({ showCloseButton && t:closable }, {
						if({ :pointInCloseBtn(x: x, y: y, tabX: area:x + idx * tw, tabW: tw, area: area) }, {
							nextClose: idx;
						});
					});
				});
			});
		});
		if({ nextTab != hoverTabIdx || nextClose != hoverCloseIdx }, {
			hoverTabIdx: nextTab;
			hoverCloseIdx: nextClose;
			return true;
		});
		return false;
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Rect is area: :tabsAreaRect(b: bounds());
		if({ x < area:x || x >= area:x + area:width || y < area:y || y >= area:y + area:height || tabs:length() == 0 }, { return false; });
		local Int is tw: :tabWidthPx(totalW: area:width);
		if({ tw <= 0 }, { return false; });
		local Int is idx: (x - area:x) / tw;
		if({ idx < 0 || idx >= tabs:length() }, { return false; });
		local TabItemConfig is t: tabs:get(index: idx);
		if({ showCloseButton && t:closable && :pointInCloseBtn(x: x, y: y, tabX: area:x + idx * tw, tabW: tw, area: area) }, {
			local Function is ccb: onCloseTab;
			ccb(idx);
			return true;
		});
		local Function is scb: onSelectTab;
		scb(idx);
		return true;
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		local Rect is area: :tabsAreaRect(b: bounds());
		if({ x < area:x || x >= area:x + area:width || y < area:y || y >= area:y + area:height || tabs:length() == 0 }, { return false; });
		local Int is tw: :tabWidthPx(totalW: area:width);
		if({ tw <= 0 }, { return false; });
		local Int is idx: (x - area:x) / tw;
		if({ idx < 0 || idx >= tabs:length() }, { return false; });
		local Function is rcb: onRightClickTab;
		rcb(idx, x, y);
		return true;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });

		local Int is linePx: activeTheme:borderPx(scaleFactor: activeScale:factor);
		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: activeTheme:tabBarBg);
		if({ dockSide == DockSide:BOTTOM }, {
			ctx:fillRect(x: b:x, y: b:y, w: b:width, h: linePx, color: activeTheme:toolbarBorder);
		}, {
			ctx:fillRect(x: b:x, y: b:y + b:height - linePx, w: b:width, h: linePx, color: activeTheme:toolbarBorder);
		});

		local Int is count: tabs:length();
		if({ count <= 0 }, { return; });

		local Rect is area: :tabsAreaRect(b: b);
		local Int is tw: :tabWidthPx(totalW: area:width);
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is padL: activeScale:px(pt: activeTheme:paddingPt * 1.5);
		local Int is padR: activeScale:px(pt: activeTheme:paddingSmallPt * 2.0);
		local Int is cs: :closeBoxSizePx();

		ctx:setClip(x: area:x, y: area:y, w: area:width, h: area:height);
		local Int is i: 0;
		while({ i < count }, {
			local Int is tx: area:x + i * tw;
			if({ tx < area:x + area:width }, {
				local TabItemConfig is tab: tabs:get(index: i);
				local Boolean is isActive: i == activeIndex;
				local Int is bg: if({ isActive }, { activeTheme:windowBg }, { if({ hoverTabIdx == i }, { activeTheme:hoverBg }, { activeTheme:tabBarBg }) });
				local Int is ty0: if({ dockSide == DockSide:BOTTOM && !isActive }, { area:y + linePx }, { area:y });
				local Int is fillH: if({ isActive }, { area:height }, { area:height - linePx });
				ctx:fillRect(x: tx, y: ty0, w: tw, h: fillH, color: bg);
				if({ dockSide != DockSide:BOTTOM }, {
					ctx:fillRect(x: tx, y: area:y, w: tw, h: linePx, color: activeTheme:toolbarBorder);
				}, {
					ctx:fillRect(x: tx, y: area:y + area:height - linePx, w: tw, h: linePx, color: activeTheme:toolbarBorder);
				});
				ctx:fillRect(x: tx + tw - linePx, y: area:y, w: linePx, h: area:height, color: activeTheme:toolbarBorder);

				local Int is closeReserve: if({ showCloseButton && tab:closable }, { cs + padR * 2 }, { padR });
				local String is rawTitle: if({ tab:dirty }, { tab:label . ' *' }, { tab:label });
				local String is disp: :fitLabel(label: rawTitle, maxTextW: tw - padL - closeReserve, fpx: fpx);
				local Int is ty: area:y + (area:height - th) / 2;
				local Int is tcol: if({ isActive }, { activeTheme:textPrimary }, { activeTheme:textMuted });
				ctx:drawText(x: tx + padL, y: ty, text: disp, color: tcol, pixelHeight: fpx);

				if({ showCloseButton && tab:closable }, {
					local Int is cx: tx + tw - padR - cs;
					local Int is cy: area:y + (area:height - cs) / 2;
					if({ hoverCloseIdx == i }, {
						ctx:fillRect(x: cx, y: cy, w: cs, h: cs, color: activeTheme:activeBg);
					});
					local Int is xw: ctx:measureTextWidth(text: 'x', pixelHeight: fpx);
					ctx:drawText(x: cx + (cs - xw) / 2, y: cy + (cs - th) / 2 - 1, text: 'x', color: tcol, pixelHeight: fpx);
				});
			});
			i: i + 1;
		});
		ctx:clearClip();
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
		local Rect is area: :tabsAreaRect(b: bounds());
		if({ x < area:x || x >= area:x + area:width || y < area:y || y >= area:y + area:height }, { return ''; });
		if({ hoverCloseIdx >= 0 }, { return 'Close tab'; });
		if({ hoverTabIdx >= 0 && hoverTabIdx < tabs:length() }, {
			return tabs:get(index: hoverTabIdx):label;
		});
		return '';
	}
}
