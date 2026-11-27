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
	Boolean is draggable: true;
	Boolean is dragging: false;
	Boolean is gripHovered: false;
	Int is dragOffsetX: 0;
	Int is dragOffsetY: 0;
	Int is dragStartPtrX: 0;
	Int is dragStartPtrY: 0;
	Int is dragStartOffX: 0;
	Int is dragStartOffY: 0;
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
		Boolean is draggable: true,
		Function is onOpenChange: local Function(Boolean is _open){}
	){
		:anchor: anchor;
		:content: content;
		:open: open;
		:toggleOnAnchorClick: toggleOnAnchorClick;
		:closeOnOutsideClick: closeOnOutsideClick;
		:padPt: padPt;
		:draggable: draggable;
		:dragging: false;
		:gripHovered: false;
		:dragOffsetX: 0;
		:dragOffsetY: 0;
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

	local Function is layoutPopup(Int is viewW, Int is viewH){
		if({ viewW > 0 }, { lastViewW: viewW; });
		if({ viewH > 0 }, { lastViewH: viewH; });
		local Int is gh: :gripHeight();
		local Int is padPx: if({ padPt > 0.0 }, { activeScale:px(pt: padPt) }, { 0 });
		local Size is ps: content:measure(c: Constraints(minW: 0, maxW: 640, minH: 0, maxH: 640));
		local Int is popW: ps:width + padPx * 2;
		local Int is popH: ps:height + gh + padPx * 2;
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
		content:arrange(bounds: Rect(x: px + padPx, y: py + gh + padPx, width: ps:width, height: ps:height));
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
		if({ open && (dragging || :inRect(r: popupRect, x: x, y: y)) }, { return true; });
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
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			content:onPointerClickMod(x: x, y: y, mods: mods);
			return true;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerMove(Int is x, Int is y){
		local Boolean is ghov: :inGrip(x: x, y: y);
		if({ ghov != gripHovered }, {
			:gripHovered: ghov;
			invalidate();
		});
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			content:onPointerMove(x: x, y: y);
			return true;
		});
		return ghov;
	}

	replace Function of Boolean is onOverlayPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ open && dragging }, {
			:dragOffsetX: dragStartOffX + (x - dragStartPtrX);
			:dragOffsetY: dragStartOffY + (y - dragStartPtrY);
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
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			content:onPointerUp(x: x, y: y);
			return true;
		});
		return false;
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ dragging || :inGrip(x: x, y: y) }, { return CursorShape:POINTER; });
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
	}
}
