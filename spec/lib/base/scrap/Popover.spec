#! Package base:scrap
#! Reusable floating popover wrapper (`SewNode`) pairing an anchor node with overlay content via [DropdownPopup].

Class of SewNode is Popover{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'scrap', DropdownPopup]
	];

	SewNode is anchor: SewNode();
	SewNode is content: SewNode();
	Boolean is open: false;
	Boolean is toggleOnAnchorClick: true;
	Boolean is closeOnOutsideClick: false;
	Float is padPt: 6.0;
	Float is maxWidthPt: 420.0;
	Float is maxHeightPt: 340.0;
	Boolean is resizable: false;
	Boolean is draggable: true;
	Boolean is dragging: false;
	Boolean is gripHovered: false;
	Int is dragOffsetX: 0;
	Int is dragOffsetY: 0;
	Int is dragStartPtrX: 0;
	Int is dragStartPtrY: 0;
	Int is dragStartOffX: 0;
	Int is dragStartOffY: 0;
	Int is customWidthPx: 0;
	Int is customHeightPx: 0;
	Int is resizeMode: 0;
	Int is hoverResizeMode: 0;
	Int is resizeStartPtrX: 0;
	Int is resizeStartPtrY: 0;
	Int is resizeStartW: 0;
	Int is resizeStartH: 0;
	Int is lastPtrX: -1;
	Int is lastPtrY: -1;
	Rect is popupRect: Rect();
	Int is lastViewW: 0;
	Int is lastViewH: 0;
	Function is onOpenChange: local Function(Boolean is _open){};

	replace Function is init(
		SewNode is anchor: SewNode(),
		SewNode is content: SewNode(),
		Boolean is open: false,
		Boolean is toggleOnAnchorClick: true,
		Boolean is closeOnOutsideClick: false,
		Float is padPt: 6.0,
		Float is maxWidthPt: 420.0,
		Float is maxHeightPt: 340.0,
		Boolean is resizable: false,
		Boolean is draggable: true,
		Function is onOpenChange: local Function(Boolean is _open){}
	){
		:anchor: anchor;
		:content: content;
		:open: open;
		:toggleOnAnchorClick: toggleOnAnchorClick;
		:closeOnOutsideClick: closeOnOutsideClick;
		:padPt: padPt;
		:maxWidthPt: maxWidthPt;
		:maxHeightPt: maxHeightPt;
		:resizable: resizable;
		:draggable: draggable;
		:dragging: false;
		:gripHovered: false;
		:dragOffsetX: 0;
		:dragOffsetY: 0;
		:customWidthPx: 0;
		:customHeightPx: 0;
		:resizeMode: 0;
		:hoverResizeMode: 0;
		:onOpenChange: onOpenChange;
	}

	Function is setOpen(Boolean is next){
		if({ open != next }, {
			:open: next;
			if({ open }, {
				:layoutPopup(viewW: lastViewW, viewH: lastViewH);
			}, {
				:dragging: false;
				:gripHovered: false;
				:dragOffsetX: 0;
				:dragOffsetY: 0;
				:resizeMode: 0;
				:hoverResizeMode: 0;
			});
			local Function is cb: onOpenChange;
			cb(open);
			invalidate();
		});
	}

	local Function of Boolean is inRect(Rect is r, Int is x, Int is y){
		return x >= r:x && x < r:x + r:width && y >= r:y && y < r:y + r:height;
	}

	local Function of Int is gripHeight(){
		if({ !draggable }, { return 0; });
		local Int is gh: activeScale:px(pt: 14.0);
		return if({ gh < 12 }, { 12 }, { gh });
	}

	local Function of Boolean is inGrip(Int is x, Int is y){
		if({ !draggable || !open }, { return false; });
		local Int is gh: :gripHeight();
		return x >= popupRect:x && x < popupRect:x + popupRect:width && y >= popupRect:y && y < popupRect:y + gh;
	}

	local Function of Int is hitResizeEdge(Int is x, Int is y){
		if({ !resizable || !open }, { return 0; });
		local Int is edge: activeScale:px(pt: 6.0);
		if({ edge < 6 }, { edge: 6; });
		local Int is rx: popupRect:x + popupRect:width;
		local Int is by: popupRect:y + popupRect:height;
		local Boolean is inX: x >= popupRect:x && x <= rx + 2;
		local Boolean is inY: y >= popupRect:y && y <= by + 2;
		if({ !inX || !inY }, { return 0; });
		local Boolean is onRight: x >= rx - edge;
		local Boolean is onBottom: y >= by - edge;
		if({ onRight && onBottom }, { return 3; });
		if({ onRight }, { return 1; });
		if({ onBottom }, { return 2; });
		return 0;
	}

	local Function is layoutPopup(Int is viewW, Int is viewH){
		if({ viewW > 0 }, { lastViewW: viewW; });
		if({ viewH > 0 }, { lastViewH: viewH; });
		local Int is gh: :gripHeight();
		local Int is padPx: if({ padPt > 0.0 }, { activeScale:px(pt: padPt) }, { 0 });
		local Int is maxW: if({ lastViewW > 24 }, { lastViewW - 24 }, { Constraints:UNBOUNDED });
		local Int is maxH: if({ lastViewH > 24 }, { lastViewH - 24 }, { Constraints:UNBOUNDED });
		if({ maxWidthPt > 0.0 && (!resizable || customWidthPx == 0) }, {
			local Int is capW: activeScale:px(pt: maxWidthPt);
			if({ maxW == Constraints:UNBOUNDED || capW < maxW }, { maxW: capW; });
		});
		if({ maxHeightPt > 0.0 && (!resizable || customHeightPx == 0) }, {
			local Int is capH: activeScale:px(pt: maxHeightPt);
			if({ maxH == Constraints:UNBOUNDED || capH < maxH }, { maxH: capH; });
		});
		local Int is cMaxW: if({ maxW == Constraints:UNBOUNDED }, { Constraints:UNBOUNDED }, {
			if({ maxW > padPx * 2 }, { maxW - padPx * 2 }, { 64 })
		});
		local Int is cMaxH: if({ maxH == Constraints:UNBOUNDED }, { Constraints:UNBOUNDED }, {
			if({ maxH > gh + padPx * 2 }, { maxH - gh - padPx * 2 }, { 64 })
		});
		local Size is ps: content:measure(c: Constraints(minW: 0, maxW: cMaxW, minH: 0, maxH: cMaxH));
		local Int is popW: ps:width + padPx * 2;
		local Int is popH: ps:height + gh + padPx * 2;
		if({ maxW != Constraints:UNBOUNDED && popW > maxW }, { popW: maxW; });
		if({ maxH != Constraints:UNBOUNDED && popH > maxH }, { popH: maxH; });
		if({ resizable && customWidthPx > 0 }, {
			local Int is minW: activeScale:px(pt: 180.0);
			popW: customWidthPx;
			if({ popW < minW }, { popW: minW; });
			if({ lastViewW > 16 && popW > lastViewW - 16 }, { popW: lastViewW - 16; });
		});
		if({ resizable && customHeightPx > 0 }, {
			local Int is minH: activeScale:px(pt: 120.0);
			popH: customHeightPx;
			if({ popH < minH }, { popH: minH; });
			if({ lastViewH > 16 && popH > lastViewH - 16 }, { popH: lastViewH - 16; });
		});
		local Rect is pr: DropdownPopup:shared:placeRect(
			anchor: anchor:bounds(),
			popupW: popW,
			popupH: popH,
			viewW: lastViewW,
			viewH: lastViewH,
			gapPx: 2
		);
		local Int is px: pr:x + dragOffsetX;
		local Int is py: pr:y + dragOffsetY;
		if({ lastViewW > 0 }, {
			if({ px + popW > lastViewW }, { px: lastViewW - popW; });
			if({ px < 0 }, { px: 0; });
		});
		if({ lastViewH > 0 }, {
			if({ py + popH > lastViewH }, { py: lastViewH - popH; });
			if({ py < 0 }, { py: 0; });
		});
		:popupRect: Rect(x: px, y: py, width: popW, height: popH);
		local Int is innerW: if({ popW > padPx * 2 }, { popW - padPx * 2 }, { 0 });
		local Int is innerH: if({ popH > gh + padPx * 2 }, { popH - gh - padPx * 2 }, { 0 });
		content:arrange(bounds: Rect(x: px + padPx, y: py + gh + padPx, width: innerW, height: innerH));
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		anchor:applyTheme(theme: theme);
		content:applyTheme(theme: theme);
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		anchor:setScale(scale: scale);
		content:setScale(scale: scale);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		anchor:bindDirty(cb: cb);
		content:bindDirty(cb: cb);
	}

	replace Function is collectFocusables(Array of SewNode is out){
		anchor:collectFocusables(out: out);
		if({ open }, {
			content:collectFocusables(out: out);
		});
	}

	replace Function of Boolean is onScroll(Int is deltaY){
		if({ open && content:onScroll(deltaY: deltaY) }, { return true; });
		return anchor:onScroll(deltaY: deltaY);
	}

	replace Function of Boolean is onScrollX(Int is deltaX){
		if({ open && content:onScrollX(deltaX: deltaX) }, { return true; });
		return anchor:onScrollX(deltaX: deltaX);
	}

	replace Function of Boolean is onOverlayScroll(Int is deltaY){
		if({ !open }, { return false; });
		if({ content:onOverlayScroll(deltaY: deltaY) }, { return true; });
		if({ :inRect(r: popupRect, x: lastPtrX, y: lastPtrY) }, {
			content:onScroll(deltaY: deltaY);
			return true;
		});
		return false;
	}

	replace Function of Boolean is onOverlayScrollX(Int is deltaX){
		if({ !open }, { return false; });
		if({ content:onOverlayScrollX(deltaX: deltaX) }, { return true; });
		if({ :inRect(r: popupRect, x: lastPtrX, y: lastPtrY) }, {
			content:onScrollX(deltaX: deltaX);
			return true;
		});
		return false;
	}

	replace Function of Size is measure(Constraints is c){
		desiredSize: anchor:measure(c: c);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		anchor:arrange(bounds: bounds);
		if({ open }, { :layoutPopup(viewW: lastViewW, viewH: lastViewH); });
	}

	replace Function of Boolean is blocksPointerAt(Int is x, Int is y){
		if({ pointerTransparent }, { return false; });
		if({ anchor:blocksPointerAt(x: x, y: y) }, { return true; });
		if({ open && (dragging || resizeMode != 0 || :inRect(r: popupRect, x: x, y: y)) }, { return true; });
		return false;
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is changed: anchor:onPointerMove(x: x, y: y);
		local Boolean is ghov: :inGrip(x: x, y: y);
		if({ ghov != gripHovered }, {
			:gripHovered: ghov;
			invalidate();
			changed: true;
		});
		if({ open }, {
			if({ content:onPointerMove(x: x, y: y) }, { changed: true; });
		});
		return changed;
	}

	replace Function is clearHover(){
		anchor:clearHover();
		content:clearHover();
		if({ gripHovered }, {
			:gripHovered: false;
			invalidate();
		});
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ anchor:containsPoint(x: x, y: y) }, {
			local Boolean is handled: anchor:onPointerClickMod(x: x, y: y, mods: mods);
			if({ toggleOnAnchorClick }, {
				:setOpen(next: !open);
				return true;
			});
			return handled;
		});
		if({ open }, {
			if({ :inGrip(x: x, y: y) }, {
				:dragging: true;
				:dragStartPtrX: x;
				:dragStartPtrY: y;
				:dragStartOffX: dragOffsetX;
				:dragStartOffY: dragOffsetY;
				invalidate();
				return true;
			});
			if({ :inRect(r: popupRect, x: x, y: y) }, {
				return content:onPointerClickMod(x: x, y: y, mods: mods);
			});
			if({ closeOnOutsideClick }, {
				:setOpen(next: false);
				return true;
			});
		});
		return false;
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ open && dragging }, {
			:dragOffsetX: dragStartOffX + (x - dragStartPtrX);
			:dragOffsetY: dragStartOffY + (y - dragStartPtrY);
			:layoutPopup(viewW: lastViewW, viewH: lastViewH);
			invalidate();
			return true;
		});
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			return content:onPointerDrag(x: x, y: y, mods: mods);
		});
		return false;
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		if({ dragging }, {
			:dragging: false;
			invalidate();
			return true;
		});
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			return content:onPointerUp(x: x, y: y);
		});
		return false;
	}

	replace Function of Boolean is closePopupsOutside(Int is x, Int is y){
		if({ !closeOnOutsideClick || dragging }, { return false; });
		if({ open && !:blocksPointerAt(x: x, y: y) }, {
			:setOpen(next: false);
			return true;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ open && :inGrip(x: x, y: y) }, {
			:dragging: true;
			:dragStartPtrX: x;
			:dragStartPtrY: y;
			:dragStartOffX: dragOffsetX;
			:dragStartOffY: dragOffsetY;
			invalidate();
			return true;
		});
		local Int is re: :hitResizeEdge(x: x, y: y);
		if({ re != 0 }, {
			:resizeMode: re;
			:resizeStartPtrX: x;
			:resizeStartPtrY: y;
			:resizeStartW: popupRect:width;
			:resizeStartH: popupRect:height;
			invalidate();
			return true;
		});
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			content:onPointerClickMod(x: x, y: y, mods: mods);
			return true;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerMove(Int is x, Int is y){
		:lastPtrX: x;
		:lastPtrY: y;
		local Boolean is ghov: :inGrip(x: x, y: y);
		local Int is rEdge: :hitResizeEdge(x: x, y: y);
		if({ ghov != gripHovered || rEdge != hoverResizeMode }, {
			:gripHovered: ghov;
			:hoverResizeMode: rEdge;
			invalidate();
		});
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			content:onPointerMove(x: x, y: y);
			return true;
		});
		return ghov || rEdge != 0;
	}

	replace Function of Boolean is onOverlayPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ open && dragging }, {
			:dragOffsetX: dragStartOffX + (x - dragStartPtrX);
			:dragOffsetY: dragStartOffY + (y - dragStartPtrY);
			:layoutPopup(viewW: lastViewW, viewH: lastViewH);
			invalidate();
			return true;
		});
		if({ open && resizeMode != 0 }, {
			if({ resizeMode == 1 || resizeMode == 3 }, {
				:customWidthPx: resizeStartW + (x - resizeStartPtrX);
			});
			if({ resizeMode == 2 || resizeMode == 3 }, {
				:customHeightPx: resizeStartH + (y - resizeStartPtrY);
			});
			:layoutPopup(viewW: lastViewW, viewH: lastViewH);
			invalidate();
			return true;
		});
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			content:onPointerDrag(x: x, y: y, mods: mods);
			return true;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerUp(Int is x, Int is y){
		if({ dragging }, {
			:dragging: false;
			invalidate();
			return true;
		});
		if({ resizeMode != 0 }, {
			:resizeMode: 0;
			invalidate();
			return true;
		});
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			content:onPointerUp(x: x, y: y);
			return true;
		});
		return false;
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ dragging || :inGrip(x: x, y: y) }, { return CursorShape:POINTER; });
		local Int is re: if({ resizeMode != 0 }, { resizeMode }, { :hitResizeEdge(x: x, y: y) });
		if({ re == 1 || re == 3 }, { return CursorShape:EW_RESIZE; });
		if({ re == 2 }, { return CursorShape:NS_RESIZE; });
		if({ open && :inRect(r: popupRect, x: x, y: y) }, { return content:cursorAt(x: x, y: y); });
		return anchor:cursorAt(x: x, y: y);
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
		if({ :inGrip(x: x, y: y) && !dragging }, { return 'Drag to move'; });
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			return content:tooltipAt(x: x, y: y);
		});
		return anchor:tooltipAt(x: x, y: y);
	}

	replace Function is paint(DrawContext is ctx){
		anchor:paint(ctx: ctx);
	}

	replace Function is paintOverlay(DrawContext is ctx){
		if({ !open }, { return; });
		:layoutPopup(viewW: ctx:canvas:width, viewH: ctx:canvas:height);
		local Int is bw: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is radPx: activeScale:px(pt: activeTheme:panelCornerRadiusPt);
		ctx:drawStyledBox(
			x: popupRect:x, y: popupRect:y, w: popupRect:width, h: popupRect:height,
			bgColor: activeTheme:menuBg, borderColor: activeTheme:menuBorder,
			thickness: bw, radius: radPx, style: activeTheme:panelBorderStyle
		);
		if({ draggable }, {
			local Int is gh: :gripHeight();
			if({ dragging || gripHovered }, {
				local Int is inset: if({ bw > 0 }, { bw }, { 1 });
				if({ popupRect:width > inset * 2 && gh > inset + 1 }, {
					ctx:fillRect(x: popupRect:x + inset, y: popupRect:y + inset, w: popupRect:width - inset * 2, h: gh - inset - 1, color: activeTheme:hoverBg);
				});
			});
			ctx:fillRect(x: popupRect:x, y: popupRect:y + gh - 1, w: popupRect:width, h: 1, color: activeTheme:menuBorder);
			local Int is dot: activeScale:px(pt: 2.0);
			if({ dot < 2 }, { dot: 2; });
			local Int is stepX: dot * 2;
			local Int is stepY: dot * 2;
			local Int is gridW: stepX * 3 + dot;
			local Int is gridH: stepY + dot;
			local Int is gx0: popupRect:x + (popupRect:width - gridW) / 2;
			local Int is gy0: popupRect:y + (gh - gridH) / 2;
			local Int is dotCol: if({ dragging || gripHovered }, { activeTheme:textPrimary }, { activeTheme:textMuted });
			local Int is r: 0;
			while({ r < 2 }, {
				local Int is c: 0;
				while({ c < 4 }, {
					ctx:fillRect(x: gx0 + c * stepX, y: gy0 + r * stepY, w: dot, h: dot, color: dotCol);
					c: c + 1;
				});
				r: r + 1;
			});
		});
		content:paint(ctx: ctx);
		content:paintOverlay(ctx: ctx);
		if({ resizable }, {
			local Int is activeEdge: if({ resizeMode != 0 }, { resizeMode }, { hoverResizeMode });
			if({ activeEdge != 0 }, {
				local Int is linePx: activeTheme:linePx(scaleFactor: activeScale:factor);
				if({ linePx < 2 }, { linePx: 2; });
				if({ activeEdge == 1 || activeEdge == 3 }, {
					ctx:fillRect(x: popupRect:x + popupRect:width - linePx, y: popupRect:y, w: linePx, h: popupRect:height, color: activeTheme:textAccent);
				});
				if({ activeEdge == 2 || activeEdge == 3 }, {
					ctx:fillRect(x: popupRect:x, y: popupRect:y + popupRect:height - linePx, w: popupRect:width, h: linePx, color: activeTheme:textAccent);
				});
			});
			local Int is gCol: if({ activeEdge != 0 }, { activeTheme:textAccent }, { activeTheme:textMuted });
			local Int is sz: activeScale:px(pt: 2.0);
			if({ sz < 2 }, { sz: 2; });
			local Int is step: sz * 2;
			local Int is rx: popupRect:x + popupRect:width - sz * 2;
			local Int is by: popupRect:y + popupRect:height - sz * 2;
			ctx:fillRect(x: rx, y: by, w: sz, h: sz, color: gCol);
			ctx:fillRect(x: rx - step, y: by, w: sz, h: sz, color: gCol);
			ctx:fillRect(x: rx, y: by - step, w: sz, h: sz, color: gCol);
		});
	}
}
