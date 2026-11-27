#! Package base:sew
#! Horizontal layout container arranging children left-to-right with optional point gap.

Class of SewNode is Row{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale]
	];

	Array of SewNode is children: Array();
	Array of Boolean is flexFlags: Array();
	Float is gapPt: 0.0;
	Int is dragChildIdx: -1;

	replace Function is init(Array of SewNode is children: Array(), Float is gapPt: 0.0, Array of Boolean is flexFlags: Array()){
		:children: children;
		:gapPt: gapPt;
		if({ flexFlags:length() == children:length() }, {
			:flexFlags: flexFlags;
		}, {
			:flexFlags: Array();
			times(count: children:length(), worker: local Function(Int is _i){
				:flexFlags:add(item: false);
			});
		});
	}

	Function is addChild(SewNode is child, Boolean is expand: false){
		children:add(item: child);
		flexFlags:add(item: expand);
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		times(count: children:length(), worker: local Function(Int is i){
			children:get(index: i):applyTheme(theme: theme);
		});
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		times(count: children:length(), worker: local Function(Int is i){
			children:get(index: i):setScale(scale: scale);
		});
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		times(count: children:length(), worker: local Function(Int is i){
			children:get(index: i):bindDirty(cb: cb);
		});
	}

	replace Function of Size is measure(Constraints is c){
		local Int is count: children:length();
		local Int is gapPx: activeScale:px(pt: gapPt);
		local Int is totalGap: if({ count > 1 }, { gapPx * (count - 1) }, { 0 });
		local Int is fixedW: 0;
		local Int is flexCount: 0;
		local Int is maxH: 0;
		local Constraints is loose: Constraints(minW: 0, maxW: c:maxW, minH: 0, maxH: c:maxH);
		times(count: count, worker: local Function(Int is i){
			local Boolean is isFlex: i < flexFlags:length() && flexFlags:get(index: i);
			if({ isFlex }, {
				flexCount: flexCount + 1;
			}, {
				local Size is sz: children:get(index: i):measure(c: loose);
				fixedW: fixedW + sz:width;
				if({ sz:height > maxH }, { maxH: sz:height; });
			});
		});
		local Int is totalW: fixedW + totalGap;
		if({ flexCount > 0 }, {
			local Int is remW: c:maxW - fixedW - totalGap;
			if({ remW < 0 }, { remW: 0; });
			local Int is eachW: remW / flexCount;
			local Constraints is flexC: Constraints(minW: eachW, maxW: eachW, minH: 0, maxH: c:maxH);
			times(count: count, worker: local Function(Int is i){
				if({ i < flexFlags:length() && flexFlags:get(index: i) }, {
					local Size is sz: children:get(index: i):measure(c: flexC);
					totalW: totalW + sz:width;
					if({ sz:height > maxH }, { maxH: sz:height; });
				});
			});
			if({ c:maxH > maxH }, { maxH: c:maxH; });
		});
		desiredSize: Size(width: c:clampW(w: totalW), height: c:clampH(h: maxH));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is count: children:length();
		local Int is gapPx: activeScale:px(pt: gapPt);
		local Boolean is hasFlex: false;
		times(count: count, worker: local Function(Int is i){
			if({ i < flexFlags:length() && flexFlags:get(index: i) }, { hasFlex: true; });
		});
		local Int is curX: bounds:x;
		times(count: count, worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			local Int is w: ch:desiredSize:width;
			local Boolean is isFlex: i < flexFlags:length() && flexFlags:get(index: i);
			local Int is h: if({ isFlex }, { bounds:height }, { ch:desiredSize:height });
			if({ h > bounds:height }, { h: bounds:height; });
			local Int is cy: if({ hasFlex }, { bounds:y }, { bounds:y + (bounds:height - h) / 2 });
			ch:arrange(bounds: Rect(x: curX, y: cy, width: w, height: h));
			curX: curX + w + gapPx;
		});
	}

	replace Function is paint(DrawContext is ctx){
		times(count: children:length(), worker: local Function(Int is i){
			children:get(index: i):paint(ctx: ctx);
		});
	}

	replace Function is paintOverlay(DrawContext is ctx){
		times(count: children:length(), worker: local Function(Int is i){
			children:get(index: i):paintOverlay(ctx: ctx);
		});
	}

	replace Function of Boolean is closePopupsOutside(Int is x, Int is y){
		local Boolean is closed: false;
		local Int is i: 0;
		while({ i < children:length() }, {
			if({ children:get(index: i):closePopupsOutside(x: x, y: y) }, { closed: true; });
			i: i + 1;
		});
		return closed;
	}

	replace Function of Boolean is onOverlayPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onOverlayPointerClickMod(x: x, y: y, mods: mods) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerMove(Int is x, Int is y){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onOverlayPointerMove(x: x, y: y) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerDrag(Int is x, Int is y, Int is mods: 0){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onOverlayPointerDrag(x: x, y: y, mods: mods) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onOverlayPointerUp(Int is x, Int is y){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onOverlayPointerUp(x: x, y: y) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is changed: false;
		local Boolean is blocked: false;
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			local SewNode is ch: children:get(index: i);
			if({ !blocked }, {
				if({ ch:onPointerMove(x: x, y: y) }, { changed: true; });
				if({ ch:blocksPointerAt(x: x, y: y) }, { blocked: true; });
			}, {
				ch:clearHover();
			});
			i: i - 1;
		});
		return changed;
	}

	replace Function is clearHover(){
		times(count: children:length(), worker: local Function(Int is i){
			children:get(index: i):clearHover();
		});
	}

	replace Function of Boolean is blocksPointerAt(Int is x, Int is y){
		if({ pointerTransparent }, { return false; });
		if({ :containsPoint(x: x, y: y) }, { return true; });
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):blocksPointerAt(x: x, y: y) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			local SewNode is ch: children:get(index: i);
			if({ ch:blocksPointerAt(x: x, y: y) }, {
				if({ ch:onPointerClickMod(x: x, y: y, mods: mods) }, { return true; });
			});
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return false; });
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			local Rect is cb: children:get(index: i):bounds();
			if({ x >= cb:x && x < cb:x + cb:width && y >= cb:y && y < cb:y + cb:height }, {
				if({ children:get(index: i):onRightClickMod(x: x, y: y, mods: mods) }, { return true; });
			});
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ dragChildIdx >= 0 && dragChildIdx < children:length() }, {
			return children:get(index: dragChildIdx):onPointerDrag(x: x, y: y, mods: mods);
		});
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			local SewNode is ch: children:get(index: i);
			if({ ch:blocksPointerAt(x: x, y: y) }, {
				dragChildIdx: i;
				return ch:onPointerDrag(x: x, y: y, mods: mods);
			});
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		if({ dragChildIdx >= 0 && dragChildIdx < children:length() }, {
			local Int is idx: dragChildIdx;
			dragChildIdx: -1;
			return children:get(index: idx):onPointerUp(x: x, y: y);
		});
		local Boolean is changed: false;
		times(count: children:length(), worker: local Function(Int is i){
			if({ children:get(index: i):onPointerUp(x: x, y: y) }, { changed: true; });
		});
		return changed;
	}

	replace Function of Boolean is onScroll(Int is deltaY){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onScroll(deltaY: deltaY) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onScrollX(Int is deltaX){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onScrollX(deltaX: deltaX) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is tick(Int is nowMs){
		local Boolean is changed: false;
		times(count: children:length(), worker: local Function(Int is i){
			if({ children:get(index: i):tick(nowMs: nowMs) }, { changed: true; });
		});
		return changed;
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onKey(key: key, mods: mods) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onText(String is ch, Int is mods){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onText(ch: ch, mods: mods) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function is collectFocusables(Array of SewNode is out){
		local Int is i: 0;
		while({ i < children:length() }, {
			local SewNode is ch: children:get(index: i);
			if({ ch:canFocus() }, { out:add(item: ch); }, { ch:collectFocusables(out: out); });
			i: i + 1;
		});
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
		if({ !:containsPoint(x: x, y: y) }, { return ''; });
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			local String is tip: children:get(index: i):tooltipAt(x: x, y: y);
			if({ tip != '' }, { return tip; });
			i: i - 1;
		});
		return tooltip;
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ !:containsPoint(x: x, y: y) }, { return CursorShape:DEFAULT; });
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			local CursorShape is cur: children:get(index: i):cursorAt(x: x, y: y);
			if({ cur != CursorShape:DEFAULT }, { return cur; });
			i: i - 1;
		});
		return CursorShape:DEFAULT;
	}
}
