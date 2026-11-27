#! Package base:sew
#! Vertical layout container stacking children top-to-bottom with optional point gap.

Class of SewNode is Column{
	replace [String] is namespace: ['base', 'sew'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
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

	## Appends a child node; if [expand] is true, it fills remaining vertical space.
	Function is addChild(SewNode is child, Boolean is expand: false){
		children:add(item: child);
		flexFlags:add(item: expand);
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		local Int is i: 0;
		while({ i < children:length() }, {
			children:get(index: i):applyTheme(theme: theme);
			i: i + 1;
		});
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		local Int is i: 0;
		while({ i < children:length() }, {
			children:get(index: i):setScale(scale: scale);
			i: i + 1;
		});
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		local Int is i: 0;
		while({ i < children:length() }, {
			children:get(index: i):bindDirty(cb: cb);
			i: i + 1;
		});
	}

	replace Function of Size is measure(Constraints is c){
		local Int is totalH: 0;
		local Int is maxW: 0;
		local Int is count: children:length();
		local Int is gapPx: activeScale:px(pt: gapPt);
		local Constraints is loose: Constraints(minW: 0, maxW: c:maxW, minH: 0, maxH: c:maxH);
		times(count: count, worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			local Size is sz: ch:measure(c: loose);
			if({ sz:width > maxW }, { maxW: sz:width; });
			totalH: totalH + sz:height;
			if({ i > 0 }, { totalH: totalH + gapPx; });
		});
		desiredSize: Size(width: c:clampW(w: maxW), height: c:clampH(h: totalH));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is count: children:length();
		local Int is gapPx: activeScale:px(pt: gapPt);
		local Int is totalGap: if({ count > 1 }, { (count - 1) * gapPx }, { 0 });
		local Int is fixedH: totalGap;
		local Int is flexCount: 0;
		times(count: count, worker: local Function(Int is i){
			if({ flexFlags:get(index: i) }, {
				flexCount: flexCount + 1;
			}, {
				local SewNode is ch: children:get(index: i);
				fixedH: fixedH + ch:desiredSize:height;
			});
		});

		local Int is remH: if({ bounds:height > fixedH }, { bounds:height - fixedH }, { 0 });
		local Int is flexH: if({ flexCount > 0 }, { remH / flexCount }, { 0 });
		local Int is curY: bounds:y;

		times(count: count, worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			local Int is h: if({ flexFlags:get(index: i) }, { flexH }, { ch:desiredSize:height });
			ch:arrange(bounds: Rect(x: bounds:x, y: curY, width: bounds:width, height: h));
			curY: curY + h + gapPx;
		});
	}

	replace Function is paint(DrawContext is ctx){
		times(count: children:length(), worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			ch:paint(ctx: ctx);
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

	local Function of Int is childIndexAt(Int is x, Int is y){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			local SewNode is ch: children:get(index: i);
			if({ ch:blocksPointerAt(x: x, y: y) }, {
				return i;
			});
			i: i - 1;
		});
		return -1;
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Int is idx: :childIndexAt(x: x, y: y);
		if({ idx >= 0 }, {
			dragChildIdx: idx;
			return children:get(index: idx):onPointerClickMod(x: x, y: y, mods: mods);
		});
		return false;
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return false; });
		local Int is idx: :childIndexAt(x: x, y: y);
		if({ idx >= 0 }, {
			return children:get(index: idx):onRightClickMod(x: x, y: y, mods: mods);
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

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ dragChildIdx >= 0 && dragChildIdx < children:length() }, {
			return children:get(index: dragChildIdx):onPointerDrag(x: x, y: y, mods: mods);
		});
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return false; });
		local Int is idx: :childIndexAt(x: x, y: y);
		if({ idx >= 0 }, {
			dragChildIdx: idx;
			return children:get(index: idx):onPointerDrag(x: x, y: y, mods: mods);
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
}
