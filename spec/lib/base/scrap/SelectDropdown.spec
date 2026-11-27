#! Package base:scrap
#! Generic dropdown / combobox selector with optional search filter and keyboard navigation.

Class of SewNode is SelectDropdown{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
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
		['base', 'scrap', DropdownPopup]
	];

	Array of String is options: Array();
	Int is selectedIndex: -1;
	String is placeholder: 'Select...';
	Boolean is searchable: false;
	Float is minWidthPt: 140.0;
	Float is heightPt: 0.0;
	Float is maxPopupHeightPt: 200.0;
	Function is onSelect: local Function(Int is _idx, String is _val){};

	Boolean is open: false;
	Boolean is hovered: false;
	Int is highlightPos: 0;
	Int is hoverPos: -1;
	Int is scrollY: 0;
	String is filterText: '';
	Array of Int is filteredIndices: Array();
	Rect is popupRect: Rect();

	replace Function is init(
		Array of String is options: Array(),
		Int is selectedIndex: -1,
		String is placeholder: 'Select...',
		Boolean is searchable: false,
		Float is minWidthPt: 140.0,
		Float is heightPt: 0.0,
		Float is maxPopupHeightPt: 200.0,
		String is tooltip: '',
		Function is onSelect: local Function(Int is _idx, String is _val){}
	){
		:options: options;
		:selectedIndex: selectedIndex;
		:placeholder: placeholder;
		:searchable: searchable;
		:minWidthPt: minWidthPt;
		:heightPt: heightPt;
		:maxPopupHeightPt: maxPopupHeightPt;
		:tooltip: tooltip;
		:onSelect: onSelect;
		:rebuildFilter();
	}

	Function is setOptions(Array of String is next){
		:options: next;
		if({ selectedIndex >= options:length() }, {
			:selectedIndex: -1;
		});
		:rebuildFilter();
		:invalidate();
	}

	Function is setSelectedIndex(Int is index){
		if({ index < -1 || index >= options:length() }, { return; });
		:selectedIndex: index;
		:invalidate();
	}

	local Function is rebuildFilter(){
		local Array of Int is out: Array();
		local String is needle: filterText:toLower();
		local Int is i: 0;
		while({ i < options:length() }, {
			if({ needle == '' }, {
				out:add(item: i);
			}, {
				local String is opt: options:get(index: i):toLower();
				if({ opt:sContains(needle: needle) }, {
					out:add(item: i);
				});
			});
			i: i + 1;
		});
		:filteredIndices: out;
		if({ highlightPos >= filteredIndices:length() }, {
			:highlightPos: if({ filteredIndices:length() > 0 }, { filteredIndices:length() - 1 }, { 0 });
		});
		if({ highlightPos < 0 }, { :highlightPos: 0; });
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:baseTextPt);
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Int is rowHeightPx(){
		local Int is fpx: :fontPx();
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Int is h: fpx + pad;
		local Int is minH: activeScale:px(pt: activeTheme:buttonHeightPt * 0.85);
		return if({ h > minH }, { h }, { minH });
	}

	local Function of Int is searchBarHeightPx(){
		if({ !searchable }, { return 0; });
		return :rowHeightPx();
	}

	local Function is openPopup(){
		:open: true;
		:filterText: '';
		:rebuildFilter();
		:highlightPos: 0;
		local Int is i: 0;
		while({ i < filteredIndices:length() }, {
			if({ filteredIndices:get(index: i) == selectedIndex }, {
				:highlightPos: i;
				i: filteredIndices:length();
			});
			i: i + 1;
		});
		:scrollY: 0;
		:hoverPos: -1;
		:invalidate();
	}

	local Function is closePopup(){
		if({ !open }, { return; });
		:open: false;
		:hoverPos: -1;
		:invalidate();
	}

	local Function is chooseFilteredPos(Int is pos){
		if({ pos < 0 || pos >= filteredIndices:length() }, { return; });
		local Int is realIdx: filteredIndices:get(index: pos);
		:selectedIndex: realIdx;
		:open: false;
		:hoverPos: -1;
		local Function is cb: :onSelect;
		cb(realIdx, options:get(index: realIdx));
		:invalidate();
	}

	local Function is layoutPopup(Int is viewW, Int is viewH){
		local Rect is b: bounds();
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is rh: :rowHeightPx();
		local Int is searchH: :searchBarHeightPx();
		local Int is n: filteredIndices:length();
		local Int is listH: if({ n > 0 }, { n * rh }, { rh });
		local Int is maxH: activeScale:px(pt: maxPopupHeightPt);
		local Int is rawPopH: searchH + listH + bw * 2;
		local Int is popH: if({ rawPopH > maxH }, { maxH }, { rawPopH });
		local Int is popW: b:width;
		local Int is minPopW: activeScale:px(pt: minWidthPt);
		if({ popW < minPopW }, { popW: minPopW; });
		:popupRect: DropdownPopup:shared:placeRect(
			anchor: b, popupW: popW, popupH: popH,
			viewW: viewW, viewH: viewH, gapPx: 2
		);
	}

	local Function of Boolean is inRect(Rect is r, Int is x, Int is y){
		return x >= r:x && x < r:x + r:width && y >= r:y && y < r:y + r:height;
	}

	local Function of Int is posAtPopupY(Int is y){
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is searchH: :searchBarHeightPx();
		local Int is rh: :rowHeightPx();
		local Int is listTop: popupRect:y + bw + searchH;
		if({ y < listTop || rh <= 0 }, { return -1; });
		local Int is relY: y - listTop + scrollY;
		local Int is pos: relY / rh;
		if({ pos < 0 || pos >= filteredIndices:length() }, { return -1; });
		return pos;
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
		local Int is radPx: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
		local FillStyle is fill: activeTheme:resolveButtonFill(
			enabled: true, selected: open, hovered: hovered, focused: focused
		);
		local Int is borderCol: if({ focused || open }, { activeTheme:textAccent }, { activeTheme:buttonBorderColorArgb() });
		ctx:drawStyledBoxFill(
			x: b:x, y: b:y, w: b:width, h: b:height,
			fill: fill, borderColor: borderCol, thickness: btnPx, radius: radPx,
			style: activeTheme:buttonBorderStyle
		);
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local String is disp: if({ selectedIndex >= 0 && selectedIndex < options:length() }, {
			options:get(index: selectedIndex)
		}, {
			placeholder
		});
		local Int is textCol: if({ selectedIndex >= 0 && selectedIndex < options:length() }, {
			activeTheme:textPrimary
		}, {
			activeTheme:textMuted
		});
		local Int is arrowW: ctx:measureTextWidth(text: '▾', pixelHeight: fpx);
		local Int is textW: b:width - pad * 2 - arrowW - 4;
		if({ textW > 0 }, {
			ctx:setClip(x: b:x + pad, y: b:y, w: textW, h: b:height);
			ctx:drawText(x: b:x + pad, y: b:y + (b:height - th) / 2, text: disp, color: textCol, pixelHeight: fpx);
			ctx:clearClip();
		});
		ctx:drawText(
			x: b:x + b:width - pad - arrowW,
			y: b:y + (b:height - th) / 2,
			text: if({ open }, { '▴' }, { '▾' }),
			color: activeTheme:textMuted,
			pixelHeight: fpx
		);
	}

	replace Function is paintOverlay(DrawContext is ctx){
		if({ !open }, { return; });
		:layoutPopup(viewW: ctx:canvas:width, viewH: ctx:canvas:height);
		local Rect is pr: popupRect;
		if({ pr:width <= 0 || pr:height <= 0 }, { return; });
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is rad: activeScale:px(pt: activeTheme:panelCornerRadiusPt);
		local Int is divPx: activeTheme:dividerPx(scaleFactor: activeScale:factor);
		ctx:drawStyledBox(
			x: pr:x, y: pr:y, w: pr:width, h: pr:height,
			bgColor: activeTheme:surfaceBg, borderColor: activeTheme:panelBorderColorArgb(),
			thickness: bw, radius: rad, style: activeTheme:panelBorderStyle
		);

		local Int is innerX: pr:x + bw;
		local Int is innerY: pr:y + bw;
		local Int is innerW: pr:width - bw * 2;
		local Int is innerH: pr:height - bw * 2;
		if({ innerW <= 0 || innerH <= 0 }, { return; });

		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Int is rh: :rowHeightPx();
		local Int is searchH: :searchBarHeightPx();

		ctx:setClip(x: innerX, y: innerY, w: innerW, h: innerH);
		if({ searchable }, {
			ctx:fillRect(x: innerX, y: innerY, w: innerW, h: searchH, color: activeTheme:hoverBg);
			local String is sTxt: if({ filterText != '' }, { filterText }, { 'Filter...' });
			local Int is sCol: if({ filterText != '' }, { activeTheme:textPrimary }, { activeTheme:textMuted });
			ctx:drawText(x: innerX + pad, y: innerY + (searchH - th) / 2, text: sTxt, color: sCol, pixelHeight: fpx);
			if({ divPx > 0 }, {
				ctx:drawDivider(
					x: innerX, y: innerY + searchH - divPx, w: innerW, h: divPx,
					color: activeTheme:dividerColorArgb(), thickness: divPx, style: activeTheme:dividerStyle
				);
			});
		});

		local Int is listY: innerY + searchH;
		local Int is listH: innerH - searchH;
		if({ listH > 0 }, {
			ctx:setClip(x: innerX, y: listY, w: innerW, h: listH);
			local Int is n: filteredIndices:length();
			if({ n == 0 }, {
				ctx:drawText(
					x: innerX + pad,
					y: listY + (rh - th) / 2,
					text: 'No matches',
					color: activeTheme:textMuted,
					pixelHeight: fpx
				);
			}, {
				local Int is contentH: n * rh;
				local Int is ms: contentH - listH;
				if({ ms < 0 }, { ms: 0; });
				if({ scrollY > ms }, { :scrollY: ms; });
				local Int is i: 0;
				while({ i < n }, {
					local Int is ry: listY + i * rh - scrollY;
					if({ ry + rh > listY && ry < listY + listH }, {
						local Int is realIdx: filteredIndices:get(index: i);
						local Boolean is isSel: realIdx == selectedIndex;
						local Boolean is isHov: i == hoverPos || i == highlightPos;
						if({ isSel || isHov }, {
							local FillStyle is rowFill: activeTheme:resolveButtonFill(
								enabled: true, selected: isSel, hovered: isHov, focused: false
							);
							ctx:drawStyledBoxFill(
								x: innerX, y: ry, w: innerW, h: rh,
								fill: rowFill, borderColor: 0, thickness: 0, radius: 0,
								style: activeTheme:buttonBorderStyle
							);
						});
						ctx:drawText(
							x: innerX + pad,
							y: ry + (rh - th) / 2,
							text: options:get(index: realIdx),
							color: if({ isSel }, { activeTheme:textPrimary }, { activeTheme:textMuted }),
							pixelHeight: fpx,
							bold: isSel,
							italic: false,
							mono: false
						);
					});
					i: i + 1;
				});
			});
			ctx:clearClip();
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
		if({ :containsPoint(x: x, y: y) }, {
			if({ open }, {
				:closePopup();
			}, {
				:openPopup();
			});
			return true;
		});
		if({ open }, {
			:closePopup();
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			local Int is pos: :posAtPopupY(y: y);
			if({ pos >= 0 }, {
				:chooseFilteredPos(pos: pos);
			});
			return true;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerMove(Int is x, Int is y){
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			local Int is pos: :posAtPopupY(y: y);
			if({ pos != hoverPos }, {
				:hoverPos: pos;
				if({ pos >= 0 }, { :highlightPos: pos; });
				:invalidate();
			});
			return true;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ open && :inRect(r: popupRect, x: x, y: y) }, { return true; });
		return false;
	}

	replace Function of Boolean is onOverlayPointerUp(Int is x, Int is y){
		if({ open && :inRect(r: popupRect, x: x, y: y) }, { return true; });
		return false;
	}

	replace Function of Boolean is onScroll(Int is x, Int is y, Int is dy){
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
			local Int is searchH: :searchBarHeightPx();
			local Int is rh: :rowHeightPx();
			local Int is listH: popupRect:height - bw * 2 - searchH;
			local Int is maxS: filteredIndices:length() * rh - listH;
			if({ maxS < 0 }, { maxS: 0; });
			local Int is step: activeScale:px(pt: 28.0);
			local Int is next: scrollY - dy * step;
			if({ next < 0 }, { next: 0; });
			if({ next > maxS }, { next: maxS; });
			if({ next != scrollY }, {
				:scrollY: next;
				:invalidate();
			});
			return true;
		});
		return false;
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		if({ !focused && !open }, { return false; });
		if({ !open }, {
			if({ key == 36 || key == 65 || key == 116 }, {
				:openPopup();
				return true;
			});
			return false;
		});
		if({ key == 9 }, {
			:closePopup();
			return true;
		});
		local Int is n: filteredIndices:length();
		if({ key == 111 }, {
			if({ n > 0 && highlightPos > 0 }, {
				:highlightPos: highlightPos - 1;
				:invalidate();
			});
			return true;
		});
		if({ key == 116 }, {
			if({ n > 0 && highlightPos + 1 < n }, {
				:highlightPos: highlightPos + 1;
				:invalidate();
			});
			return true;
		});
		if({ key == 36 }, {
			if({ highlightPos >= 0 && highlightPos < n }, {
				:chooseFilteredPos(pos: highlightPos);
			});
			return true;
		});
		if({ searchable && key == 22 }, {
			local Int is fl: filterText:length();
			if({ fl > 0 }, {
				:filterText: filterText:substring(start: 0, end: fl - 1);
				:rebuildFilter();
				:scrollY: 0;
				:invalidate();
			});
			return true;
		});
		return false;
	}

	replace Function of Boolean is onText(String is ch, Int is mods){
		if({ !open || !searchable }, { return false; });
		if({ ch == '' }, { return false; });
		:filterText: filterText . ch;
		:rebuildFilter();
		:scrollY: 0;
		:invalidate();
		return true;
	}

	replace Function is collectFocusables(Array of SewNode is out){
		out:add(item: self);
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ :containsPoint(x: x, y: y) }, { return CursorShape:POINTER; });
		if({ open && :inRect(r: popupRect, x: x, y: y) }, { return CursorShape:POINTER; });
		return CursorShape:DEFAULT;
	}
}
