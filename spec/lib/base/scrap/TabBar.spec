#! Package base:scrap
#! Horizontal tab bar (`SewNode`) with min/max tab widths, optional close ('X') buttons, and right-click support.

Class of SewNode is TabBar{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'fabric', DrawContext],
		['base', 'scrap', TabItemConfig]
	];

	Array of TabItemConfig is tabs: Array();
	Int is activeIndex: 0;
	Float is heightPt: 28.0;
	Float is minTabWidthPt: 96.0;
	Float is maxTabWidthPt: 210.0;
	Boolean is showCloseButton: true;
	Function is onSelectTab: local Function(Int is _idx){};
	Function is onCloseTab: local Function(Int is _idx){};
	Function is onRightClickTab: local Function(Int is _idx, Int is _x, Int is _y){};

	Int is hoverTabIdx: -1;
	Int is hoverCloseIdx: -1;

	replace Function is init(
		Array of TabItemConfig is tabs: Array(),
		Int is activeIndex: 0,
		Float is heightPt: 28.0,
		Float is minTabWidthPt: 96.0,
		Float is maxTabWidthPt: 210.0,
		Boolean is showCloseButton: true,
		Function is onSelectTab: local Function(Int is _idx){},
		Function is onCloseTab: local Function(Int is _idx){},
		Function is onRightClickTab: local Function(Int is _idx, Int is _x, Int is _y){}
	){
		:tabs: tabs;
		:activeIndex: activeIndex;
		:heightPt: heightPt;
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
		local Int is px: activeScale:px(pt: 14.0);
		return if({ px < 11 }, { 11 }, { px });
	}

	local Function of Int is tabWidthPx(Int is totalW){
		local Int is count: tabs:length();
		if({ count <= 0 }, { return 0; });
		local Int is minW: activeScale:px(pt: minTabWidthPt);
		local Int is maxW: activeScale:px(pt: maxTabWidthPt);
		local Int is w: totalW / count;
		if({ w > maxW }, { w: maxW; });
		if({ w < minW }, { w: minW; });
		return w;
	}

	local Function of Int is closeBoxSizePx(){
		return activeScale:px(pt: 16.0);
	}

	local Function of Boolean is pointInCloseBtn(Int is x, Int is y, Int is tabX, Int is tabW, Rect is b){
		if({ !showCloseButton }, { return false; });
		local Int is cs: :closeBoxSizePx();
		local Int is padR: activeScale:px(pt: 6.0);
		local Int is cx: tabX + tabW - padR - cs;
		local Int is cy: b:y + (b:height - cs) / 2;
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
		local Int is hPx: activeScale:px(pt: heightPt);
		desiredSize: Size(width: c:maxW, height: c:clampH(h: hPx));
		return desiredSize;
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Rect is b: bounds();
		local Int is nextTab: -1;
		local Int is nextClose: -1;
		if({ x >= b:x && x < b:x + b:width && y >= b:y && y < b:y + b:height && tabs:length() > 0 }, {
			local Int is tw: :tabWidthPx(totalW: b:width);
			if({ tw > 0 }, {
				local Int is idx: (x - b:x) / tw;
				if({ idx >= 0 && idx < tabs:length() }, {
					nextTab: idx;
					local TabItemConfig is t: tabs:get(index: idx);
					if({ showCloseButton && t:closable }, {
						if({ :pointInCloseBtn(x: x, y: y, tabX: b:x + idx * tw, tabW: tw, b: b) }, {
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
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height || tabs:length() == 0 }, { return false; });
		local Int is tw: :tabWidthPx(totalW: b:width);
		if({ tw <= 0 }, { return false; });
		local Int is idx: (x - b:x) / tw;
		if({ idx < 0 || idx >= tabs:length() }, { return false; });
		local TabItemConfig is t: tabs:get(index: idx);
		if({ showCloseButton && t:closable && :pointInCloseBtn(x: x, y: y, tabX: b:x + idx * tw, tabW: tw, b: b) }, {
			local Function is ccb: onCloseTab;
			ccb(idx);
			return true;
		});
		local Function is scb: onSelectTab;
		scb(idx);
		return true;
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height || tabs:length() == 0 }, { return false; });
		local Int is tw: :tabWidthPx(totalW: b:width);
		if({ tw <= 0 }, { return false; });
		local Int is idx: (x - b:x) / tw;
		if({ idx < 0 || idx >= tabs:length() }, { return false; });
		local Function is rcb: onRightClickTab;
		rcb(idx, x, y);
		return true;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });

		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: activeTheme:toolbarBg);
		ctx:fillRect(x: b:x, y: b:y + b:height - 1, w: b:width, h: 1, color: activeTheme:toolbarBorder);

		local Int is count: tabs:length();
		if({ count <= 0 }, { return; });

		local Int is tw: :tabWidthPx(totalW: b:width);
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is padL: activeScale:px(pt: 10.0);
		local Int is padR: activeScale:px(pt: 6.0);
		local Int is cs: :closeBoxSizePx();

		ctx:setClip(x: b:x, y: b:y, w: b:width, h: b:height);
		local Int is i: 0;
		while({ i < count }, {
			local Int is tx: b:x + i * tw;
			if({ tx < b:x + b:width }, {
				local TabItemConfig is tab: tabs:get(index: i);
				local Boolean is isActive: i == activeIndex;
				local Int is bg: if({ isActive }, { activeTheme:windowBg }, { if({ hoverTabIdx == i }, { activeTheme:hoverBg }, { activeTheme:toolbarBg }) });
				local Int is fillH: if({ isActive }, { b:height }, { b:height - 1 });
				ctx:fillRect(x: tx, y: b:y, w: tw, h: fillH, color: bg);
				ctx:fillRect(x: tx + tw - 1, y: b:y, w: 1, h: b:height - 1, color: activeTheme:toolbarBorder);

				local Int is closeReserve: if({ showCloseButton && tab:closable }, { cs + padR * 2 }, { padR });
				local String is rawTitle: if({ tab:dirty }, { tab:label . ' *' }, { tab:label });
				local String is disp: :fitLabel(label: rawTitle, maxTextW: tw - padL - closeReserve, fpx: fpx);
				local Int is ty: b:y + (b:height - th) / 2;
				local Int is tcol: if({ isActive }, { activeTheme:textPrimary }, { activeTheme:textMuted });
				ctx:drawText(x: tx + padL, y: ty, text: disp, color: tcol, pixelHeight: fpx);

				if({ showCloseButton && tab:closable }, {
					local Int is cx: tx + tw - padR - cs;
					local Int is cy: b:y + (b:height - cs) / 2;
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
}
