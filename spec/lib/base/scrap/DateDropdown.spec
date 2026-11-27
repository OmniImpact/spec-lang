#! Package base:scrap
#! Date picker dropdown button with a floating [DateSelector] overlay placed via [DropdownPopup].

Class of SewNode is DateDropdown{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', DateTime],
		['base', 'sys', as DateTime()],
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext],
		['base', 'scrap', DropdownPopup],
		['base', 'scrap', DateSelector],
		['base', 'fabric', 'svg', SvgRenderer]
	];

	DateTime is value: DateTime:now();
	String is iconSvg: '';
	Boolean is open: false;
	Boolean is hovered: false;
	Boolean is focused: false;
	DateSelector is selector: DateSelector();
	Rect is popupRect: Rect();
	Int is lastViewW: 0;
	Int is lastViewH: 0;
	Function is onChange: local Function(DateTime is _dt){};

	replace Function is init(
		DateTime is value: DateTime:now(),
		String is iconSvg: '',
		Function is onChange: local Function(DateTime is _dt){},
		String is tooltip: ''
	){
		:value: value;
		:iconSvg: iconSvg;
		:open: false;
		:hovered: false;
		:focused: false;
		:onChange: onChange;
		:tooltip: tooltip;
		:selector: DateSelector(
			value: value,
			onChange: local Function(DateTime is next){
				:value: next;
				local Function is cb: :onChange;
				cb(next);
				:open: false;
				invalidate();
			}
		);
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
			if({ !next && open }, { :open: false; });
			invalidate();
		});
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		if({ focused && (key == 10 || key == 13 || key == 32) }, {
			:open: !open;
			if({ open }, {
				selector:setValue(next: value);
				:layoutPopup(viewW: lastViewW, viewH: lastViewH);
			});
			invalidate();
			return true;
		});
		if({ open && key == 27 }, {
			:open: false;
			invalidate();
			return true;
		});
		return false;
	}

	Function is setValue(DateTime is next){
		:value: next;
		selector:setValue(next: next);
		invalidate();
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 14.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Boolean is inRect(Rect is r, Int is x, Int is y){
		return x >= r:x && x < r:x + r:width && y >= r:y && y < r:y + r:height;
	}

	local Function of Boolean is hitSelf(Int is x, Int is y){
		return :inRect(r: bounds(), x: x, y: y);
	}

	local Function is layoutPopup(Int is viewW, Int is viewH){
		if({ viewW > 0 }, { lastViewW: viewW; });
		if({ viewH > 0 }, { lastViewH: viewH; });
		local Int is maxW: if({ lastViewW > 0 }, { lastViewW }, { Constraints:UNBOUNDED });
		local Int is maxH: if({ lastViewH > 0 }, { lastViewH }, { Constraints:UNBOUNDED });
		local Size is ps: selector:measure(c: Constraints(minW: 0, maxW: maxW, minH: 0, maxH: maxH));
		local Rect is pr: DropdownPopup:shared:placeRect(
			anchor: bounds(),
			popupW: ps:width,
			popupH: ps:height,
			viewW: lastViewW,
			viewH: lastViewH,
			gapPx: 2
		);
		:popupRect: pr;
		selector:arrange(bounds: pr);
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		selector:applyTheme(theme: theme);
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		selector:setScale(scale: scale);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		selector:bindDirty(cb: cb);
	}

	replace Function of Size is measure(Constraints is c){
		local Int is fpx: :fontPx();
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Int is h: activeScale:px(pt: activeTheme:buttonHeightPt);
		local Int is dw: DrawContext:measureWidth(text: '2026-12-31  ▾', pixelHeight: fpx);
		local Int is w: dw + pad * 3;
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		if({ open }, { :layoutPopup(viewW: lastViewW, viewH: lastViewH); });
	}

	replace Function of Boolean is blocksPointerAt(Int is x, Int is y){
		if({ pointerTransparent }, { return false; });
		if({ :hitSelf(x: x, y: y) }, { return true; });
		if({ open && :inRect(r: popupRect, x: x, y: y) }, { return true; });
		return false;
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is h: :hitSelf(x: x, y: y);
		local Boolean is changed: false;
		if({ h != hovered }, {
			:hovered: h;
			invalidate();
			changed: true;
		});
		if({ open }, {
			if({ selector:onPointerMove(x: x, y: y) }, { changed: true; });
		});
		return changed;
	}

	replace Function is clearHover(){
		if({ hovered }, {
			:hovered: false;
			invalidate();
		});
		selector:clearHover();
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ :hitSelf(x: x, y: y) }, {
			:open: !open;
			if({ open }, {
				selector:setValue(next: value);
				:layoutPopup(viewW: lastViewW, viewH: lastViewH);
			});
			invalidate();
			return true;
		});
		if({ open }, {
			if({ :inRect(r: popupRect, x: x, y: y) }, {
				return selector:onPointerClickMod(x: x, y: y, mods: mods);
			});
			:open: false;
			invalidate();
			return true;
		});
		return false;
	}

	replace Function of Boolean is closePopupsOutside(Int is x, Int is y){
		if({ open && !:blocksPointerAt(x: x, y: y) }, {
			:open: false;
			invalidate();
			return true;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			selector:onPointerClickMod(x: x, y: y, mods: mods);
			return true;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerMove(Int is x, Int is y){
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			selector:onPointerMove(x: x, y: y);
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

	replace Function of String is tooltipAt(Int is x, Int is y){
		if({ tooltip != '' && :hitSelf(x: x, y: y) }, { return tooltip; });
		return '';
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ :hitSelf(x: x, y: y) }, { return CursorShape:POINTER; });
		return CursorShape:DEFAULT;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		DropdownPopup:shared:paintButtonBox(
			ctx: ctx, theme: activeTheme, scale: activeScale, bounds: b,
			selected: open, hovered: hovered, focused: focused
		);
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local String is txt: value:formatDate();
		ctx:drawText(x: b:x + pad, y: b:y + (b:height - th) / 2, text: txt, color: activeTheme:textPrimary, pixelHeight: fpx);
		if({ iconSvg != '' }, {
			local Int is iconSz: activeScale:px(pt: activeTheme:iconSizePt);
			if({ iconSz < 10 }, { iconSz: 10; });
			SvgRenderer:shared:draw(ctx: ctx, svgSrc: iconSvg, x: b:x + b:width - pad - iconSz, y: b:y + (b:height - iconSz) / 2, widthPx: iconSz, heightPx: iconSz, tintColor: activeTheme:textMuted, useTint: true);
		}, {
			local Int is cw: ctx:measureTextWidth(text: '▾', pixelHeight: fpx);
			ctx:drawText(x: b:x + b:width - pad - cw, y: b:y + (b:height - th) / 2, text: '▾', color: activeTheme:textMuted, pixelHeight: fpx);
		});
	}

	replace Function is paintOverlay(DrawContext is ctx){
		if({ !open }, { return; });
		:layoutPopup(viewW: ctx:canvas:width, viewH: ctx:canvas:height);
		selector:paint(ctx: ctx);
	}
}
