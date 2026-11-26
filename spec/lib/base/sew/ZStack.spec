#! Package base:sew
#! Z-order overlay layout container stacking children on top of each other.

Class of SewNode is ZStack{
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

	replace Function is init(Array of SewNode is children: Array()){
		:children: children;
	}

	## Appends a child node in back-to-front z-order.
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
		local Int is maxW: 0;
		local Int is maxH: 0;
		local Constraints is childC: Constraints(minW: 0, maxW: c:maxW, minH: 0, maxH: c:maxH);
		times(count: children:length(), worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			local Size is sz: ch:measure(c: childC);
			if({ sz:width > maxW }, { maxW: sz:width; });
			if({ sz:height > maxH }, { maxH: sz:height; });
		});
		desiredSize: Size(width: c:clampW(w: maxW), height: c:clampH(h: maxH));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		times(count: children:length(), worker: local Function(Int is i){
			local SewNode is ch: children:get(index: i);
			ch:arrange(bounds: bounds);
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
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onPointerClickMod(x: x, y: y, mods: mods) }, { return true; });
			i: i - 1;
		});
		return false;
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		local Int is i: children:length() - 1;
		while({ i >= 0 }, {
			if({ children:get(index: i):onRightClickMod(x: x, y: y, mods: mods) }, { return true; });
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
}
