#! Package base:scrap
#! Reusable floating popover wrapper (`SewNode`) pairing an anchor node with overlay content via [DropdownPopup].

Class of SewNode is Popover{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
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
	Rect is popupRect: Rect();
	Int is lastViewW: 0;
	Int is lastViewH: 0;
	Function is onOpenChange: local Function(Boolean is _open){};

	replace Function is init(
		SewNode is anchor: SewNode(),
		SewNode is content: SewNode(),
		Boolean is open: false,
		Boolean is toggleOnAnchorClick: true,
		Function is onOpenChange: local Function(Boolean is _open){}
	){
		:anchor: anchor;
		:content: content;
		:open: open;
		:toggleOnAnchorClick: toggleOnAnchorClick;
		:onOpenChange: onOpenChange;
	}

	Function is setOpen(Boolean is next){
		if({ open != next }, {
			:open: next;
			if({ open }, { :layoutPopup(viewW: lastViewW, viewH: lastViewH); });
			local Function is cb: onOpenChange;
			cb(open);
			invalidate();
		});
	}

	local Function of Boolean is inRect(Rect is r, Int is x, Int is y){
		return x >= r:x && x < r:x + r:width && y >= r:y && y < r:y + r:height;
	}

	local Function is layoutPopup(Int is viewW, Int is viewH){
		if({ viewW > 0 }, { lastViewW: viewW; });
		if({ viewH > 0 }, { lastViewH: viewH; });
		local Size is ps: content:measure(c: Constraints(minW: 0, maxW: 640, minH: 0, maxH: 640));
		local Rect is pr: DropdownPopup:shared:placeRect(
			anchor: anchor:bounds(),
			popupW: ps:width,
			popupH: ps:height,
			viewW: lastViewW,
			viewH: lastViewH,
			gapPx: 2
		);
		:popupRect: pr;
		content:arrange(bounds: pr);
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
		if({ open && :inRect(r: popupRect, x: x, y: y) }, { return true; });
		return false;
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is changed: anchor:onPointerMove(x: x, y: y);
		if({ open }, {
			if({ content:onPointerMove(x: x, y: y) }, { changed: true; });
		});
		return changed;
	}

	replace Function is clearHover(){
		anchor:clearHover();
		content:clearHover();
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
			if({ :inRect(r: popupRect, x: x, y: y) }, {
				return content:onPointerClickMod(x: x, y: y, mods: mods);
			});
			:setOpen(next: false);
			return true;
		});
		return false;
	}

	replace Function of Boolean is closePopupsOutside(Int is x, Int is y){
		if({ open && !:blocksPointerAt(x: x, y: y) }, {
			:setOpen(next: false);
			return true;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			content:onPointerClickMod(x: x, y: y, mods: mods);
			return true;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerMove(Int is x, Int is y){
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			content:onPointerMove(x: x, y: y);
			return true;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			content:onPointerDrag(x: x, y: y, mods: mods);
			return true;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerUp(Int is x, Int is y){
		if({ open && :inRect(r: popupRect, x: x, y: y) }, {
			content:onPointerUp(x: x, y: y);
			return true;
		});
		return false;
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
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
		content:paint(ctx: ctx);
	}
}
