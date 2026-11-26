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
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale]
	];

	Array of SewNode is children: Array();
	Float is gapPt: 0.0;

	replace Function is init(Array of SewNode is children: Array(), Float is gapPt: 0.0){
		:children: children;
		:gapPt: gapPt;
	}

	Function is addChild(SewNode is child){
		children:add(item: child);
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
		local Int is totalW: 0;
		local Int is maxH: 0;
		local Int is count: children:length();
		local Int is gapPx: activeScale:px(pt: gapPt);
		local Constraints is loose: Constraints(minW: 0, maxW: c:maxW, minH: 0, maxH: c:maxH);
		times(count: count, worker: local Function(Int is i){
			local Size is sz: children:get(index: i):measure(c: loose);
			totalW: totalW + sz:width;
			if({ i > 0 }, { totalW: totalW + gapPx; });
			if({ sz:height > maxH }, { maxH: sz:height; });
		});
		desiredSize: Size(width: c:clampW(w: totalW), height: c:clampH(h: maxH));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is count: children:length();
		local Int is gapPx: activeScale:px(pt: gapPt);
		local Int is curX: bounds:x;
		times(count: count, worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			local Int is w: ch:desiredSize:width;
			local Int is h: ch:desiredSize:height;
			local Int is cy: bounds:y + (bounds:height - h) / 2;
			ch:arrange(bounds: Rect(x: curX, y: cy, width: w, height: h));
			curX: curX + w + gapPx;
		});
	}

	replace Function is paint(DrawContext is ctx){
		times(count: children:length(), worker: local Function(Int is i){
			children:get(index: i):paint(ctx: ctx);
		});
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

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return false; });
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			local Rect is cb: children:get(index: i):bounds();
			if({ x >= cb:x && x < cb:x + cb:width && y >= cb:y && y < cb:y + cb:height }, {
				if({ children:get(index: i):onPointerClickMod(x: x, y: y, mods: mods) }, { return true; });
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
}
