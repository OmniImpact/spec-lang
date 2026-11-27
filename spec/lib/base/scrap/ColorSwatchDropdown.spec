#! Package base:scrap
#! Color swatch button with a floating dropdown containing an optional [ColorSelector] and/or [ColorSwatchHistory].

Class of SewNode is ColorSwatchDropdown{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'sew', Column],
		['base', 'fabric', Color],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', DropdownPopup],
		['base', 'scrap', ColorSelector],
		['base', 'scrap', ColorSwatchHistory]
	];

	Color is color: Color(r: 100, g: 180, b: 255);
	Boolean is open: false;
	Boolean is hovered: false;
	Boolean is focused: false;
	Boolean is showPicker: true;
	Boolean is showHistory: true;
	Boolean is compactPicker: false;
	ColorSelector is picker: ColorSelector();
	ColorSwatchHistory is history: ColorSwatchHistory();
	Column is popupCol: Column();
	Rect is popupRect: Rect();
	Int is lastViewW: 0;
	Int is lastViewH: 0;
	Function is onChange: local Function(Color is _c){};

	replace Function is init(
		Color is color: Color(r: 100, g: 180, b: 255),
		Boolean is showPicker: true,
		Boolean is showHistory: true,
		Boolean is compactPicker: false,
		Array of Color is historyColors: Array(),
		Function is onChange: local Function(Color is _c){},
		String is tooltip: ''
	){
		:color: color;
		:open: false;
		:hovered: false;
		:focused: false;
		:showPicker: showPicker;
		:showHistory: showHistory;
		:compactPicker: compactPicker;
		:onChange: onChange;
		:tooltip: tooltip;

		:picker: ColorSelector(
			color: color,
			currentColor: color,
			hasCurrent: true,
			compact: compactPicker,
			onChange: local Function(Color is next){
				:color: next;
				local Function is cb: :onChange;
				cb(next);
				invalidate();
			},
			onCommit: local Function(Color is next){
				if({ :showHistory }, { :history:addColor(c: next); });
			}
		);

		local Array of Color is initHist: historyColors;
		if({ showHistory && initHist:length() == 0 }, {
			initHist: Array([
				Color(r: 20, g: 23, b: 33),
				Color(r: 242, g: 245, b: 250),
				Color(r: 66, g: 133, b: 244),
				Color(r: 76, g: 175, b: 80),
				Color(r: 239, g: 83, b: 80),
				Color(r: 255, g: 193, b: 7)
			]);
		});
		:history: ColorSwatchHistory(
			colors: initHist,
			onSelect: local Function(Color is next){
				:setColor(next: next);
				local Function is cb: :onChange;
				cb(next);
				:open: false;
				invalidate();
			}
		);

		:rebuildPopup();
	}

	local Function is rebuildPopup(){
		local Array of SewNode is items: Array();
		if({ showPicker }, { items:add(item: picker); });
		if({ showHistory }, { items:add(item: history); });
		:popupCol: Column(children: items, gapPt: 8.0);
		popupCol:applyTheme(theme: activeTheme);
		popupCol:setScale(scale: activeScale);
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
				picker:setCurrentColor(next: color, hasCurrent: true);
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

	Function is setColor(Color is next){
		:color: next;
		picker:setColor(next: next);
		invalidate();
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		popupCol:applyTheme(theme: theme);
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		popupCol:setScale(scale: scale);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		popupCol:bindDirty(cb: cb);
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 14.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	replace Function of Size is measure(Constraints is c){
		local Int is sw: activeScale:px(pt: 20.0);
		local Int is fpx: :fontPx();
		local Int is tw: DrawContext:measureWidth(text: '#RRGGBB', pixelHeight: fpx);
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Int is w: sw + tw + pad * 3;
		local Int is h: activeScale:px(pt: activeTheme:buttonHeightPt);
		if({ h < 20 }, { h: 20; });
		desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: h));
		return desiredSize;
	}

	local Function is layoutPopup(Int is viewW, Int is viewH){
		if({ viewW > 0 }, { :lastViewW: viewW; });
		if({ viewH > 0 }, { :lastViewH: viewH; });
		local Rect is b: bounds();
		local Int is pad: activeScale:px(pt: activeTheme:paddingMediumPt);
		if({ pad < 6 }, { pad: 6; });
		local Size is cs: popupCol:measure(c: Constraints(minW: 0, maxW: activeScale:px(pt: 240.0), minH: 0, maxH: 1000));
		local Int is pw: cs:width + pad * 2;
		local Int is ph: cs:height + pad * 2;
		local Rect is placed: DropdownPopup:shared:placeRect(
			anchor: b,
			popupW: pw,
			popupH: ph,
			viewW: lastViewW,
			viewH: lastViewH,
			gapPx: 2
		);
		:popupRect: placed;
		popupCol:arrange(bounds: Rect(x: placed:x + pad, y: placed:y + pad, width: cs:width, height: cs:height));
	}

	local Function of Boolean is inRect(Rect is r, Int is x, Int is y){
		return x >= r:x && x < r:x + r:width && y >= r:y && y < r:y + r:height;
	}

	replace Function of Boolean is blocksPointerAt(Int is x, Int is y){
		if({ pointerTransparent }, { return false; });
		if({ :containsPoint(x: x, y: y) }, { return true; });
		if({ open && :inRect(r: popupRect, x: x, y: y) }, { return true; });
		return false;
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is h: :containsPoint(x: x, y: y);
		local Boolean is changed: false;
		if({ h != hovered }, {
			:hovered: h;
			invalidate();
			changed: true;
		});
		if({ open }, {
			if({ popupCol:onPointerMove(x: x, y: y) }, { changed: true; });
		});
		return changed;
	}

	replace Function is clearHover(){
		if({ hovered }, {
			:hovered: false;
			invalidate();
		});
		popupCol:clearHover();
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ :containsPoint(x: x, y: y) }, {
			:open: !open;
			if({ open }, {
				picker:setCurrentColor(next: color, hasCurrent: true);
				:layoutPopup(viewW: lastViewW, viewH: lastViewH);
			});
			invalidate();
			return true;
		});
		if({ open }, {
			if({ :inRect(r: popupRect, x: x, y: y) }, {
				return popupCol:onPointerClickMod(x: x, y: y, mods: mods);
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
			popupCol:onPointerClickMod(x: x, y: y, mods: mods);
			return true;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerMove(Int is x, Int is y){
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			popupCol:onPointerMove(x: x, y: y);
			return true;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ open }, {
			local Boolean is handled: popupCol:onPointerDrag(x: x, y: y, mods: mods);
			if({ handled || :inRect(r: popupRect, x: x, y: y) }, {
				return true;
			});
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerUp(Int is x, Int is y){
		if({ open }, {
			local Boolean is handled: popupCol:onPointerUp(x: x, y: y);
			if({ handled || :inRect(r: popupRect, x: x, y: y) }, {
				return true;
			});
		});
		return false;
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ open }, {
			return popupCol:onPointerDrag(x: x, y: y, mods: mods);
		});
		return false;
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		if({ open }, {
			return popupCol:onPointerUp(x: x, y: y);
		});
		return false;
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			return popupCol:tooltipAt(x: x, y: y);
		});
		if({ tooltip != '' && :containsPoint(x: x, y: y) }, { return tooltip; });
		return '';
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is bw: activeTheme:borderPx(scaleFactor: activeScale:factor);
		local Int is bg: if({ open }, { activeTheme:activeBg }, { if({ hovered }, { activeTheme:hoverBg }, { activeTheme:menuBg }) });
		local Int is borderCol: if({ open }, { activeTheme:textAccent }, { activeTheme:buttonBorder });
		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: bg);
		if({ bw > 0 }, {
			ctx:strokeRect(x: b:x, y: b:y, w: b:width, h: b:height, color: borderCol, thickness: bw);
		});
		local Int is pad: activeScale:px(pt: activeTheme:paddingPt);
		local Int is sw: b:height - pad * 2;
		if({ sw < 10 }, { sw: 10; });
		ctx:fillRect(x: b:x + pad, y: b:y + (b:height - sw) / 2, w: sw, h: sw, color: color:toArgb());
		if({ bw > 0 }, {
			ctx:strokeRect(x: b:x + pad, y: b:y + (b:height - sw) / 2, w: sw, h: sw, color: activeTheme:buttonBorder, thickness: bw);
		});
		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		ctx:drawText(x: b:x + pad * 2 + sw, y: b:y + (b:height - th) / 2, text: color:toHex(), color: activeTheme:textPrimary, pixelHeight: fpx);
	}

	replace Function is paintOverlay(DrawContext is ctx){
		if({ !open }, { return; });
		:layoutPopup(viewW: ctx:canvas:width, viewH: ctx:canvas:height);
		local Int is bw: activeTheme:borderPx(scaleFactor: activeScale:factor);
		ctx:fillRect(x: popupRect:x, y: popupRect:y, w: popupRect:width, h: popupRect:height, color: activeTheme:menuBg);
		if({ bw > 0 }, {
			ctx:strokeRect(x: popupRect:x, y: popupRect:y, w: popupRect:width, h: popupRect:height, color: activeTheme:menuBorder, thickness: bw);
		});
		popupCol:paint(ctx: ctx);
	}
}
