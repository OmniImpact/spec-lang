#! Package base:sew
#! Shared axis-parameterized split-grid container backing [GridFlexH] and [GridFlexV].

Class of SewNode is GridFlex{
	replace [String] is namespace: ['base', 'sew', 'grid'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'struct', Array],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', 'grid', GridFlexPanel],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale]
	];

	Array of GridFlexPanel is panels: Array();
	Float is spacingPt: 0.0;
	Float is heightPt: 0.0;
	Boolean is movable: true;
	Boolean is horizontal: true;
	Int is dragDivider: -1;
	Int is dragChildIdx: -1;
	Int is hoverDivider: -1;
	Int is dragStartPos: 0;
	Int is dragStartSizeA: 0;
	Int is dragStartSizeB: 0;
	Int is lastMouseX: -1;
	Int is lastMouseY: -1;
	Array of Int is panelSizesPx: Array();
	Array of Int is dividerPosPx: Array();
	Array of Int is dividerLeftIdx: Array();
	Array of Int is dividerRightIdx: Array();

	Function is addPanel(GridFlexPanel is panel){
		panels:add(item: panel);
		invalidate();
	}

	Function is setPanelVisible(Int is index, Boolean is visible){
		if({ index < 0 || index >= panels:length() }, { return; });
		panels:get(index: index):visible: visible;
		dragDivider: -1;
		hoverDivider: -1;
		invalidate();
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		times(count: panels:length(), worker: local Function(Int is i){
			panels:get(index: i):child:applyTheme(theme: theme);
		});
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		times(count: panels:length(), worker: local Function(Int is i){
			panels:get(index: i):child:setScale(scale: scale);
		});
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		times(count: panels:length(), worker: local Function(Int is i){
			panels:get(index: i):child:bindDirty(cb: cb);
		});
	}

	local Function of Int is spacingPx(){
		local Float is pt: if({ spacingPt > 0.0 }, { spacingPt }, { activeTheme:splitterSpacingPt });
		local Int is px: activeScale:px(pt: pt);
		return if({ px < 1 }, { 1 }, { px });
	}

	local Function of Int is clampPanelPx(GridFlexPanel is p, Int is px, Int is totalAvail){
		local Int is minPx: if({ p:minSizePt > 0.0 }, { activeScale:px(pt: p:minSizePt) }, { 0 });
		local Int is maxPx: if({ p:maxSizePt > 0.0 }, { activeScale:px(pt: p:maxSizePt) }, { totalAvail });
		if({ maxPx < minPx }, { maxPx: minPx; });
		local Int is r: px;
		if({ r < minPx }, { r: minPx; });
		if({ r > maxPx }, { r: maxPx; });
		if({ r < 0 }, { r: 0; });
		return r;
	}

	local Function of Array of Int is computeSizes(Int is totalMain){
		local Int is count: panels:length();
		local Array of Int is sizes: Array();
		if({ count == 0 }, { return sizes; });
		local Int is visCount: 0;
		local Int is vi: 0;
		while({ vi < count }, {
			if({ panels:get(index: vi):visible }, { visCount: visCount + 1; });
			vi: vi + 1;
		});
		local Int is sp: :spacingPx();
		local Int is totalSpacing: if({ visCount > 1 }, { sp * (visCount - 1) }, { 0 });
		local Int is avail: if({ totalMain > totalSpacing }, { totalMain - totalSpacing }, { 0 });

		local Int is used: 0;
		local Int is flexCount: 0;
		local Int is lastVisIdx: -1;
		local Int is i: 0;
		while({ i < count }, {
			local GridFlexPanel is p: panels:get(index: i);
			if({ !p:visible }, {
				sizes:add(item: 0);
			}, {
				lastVisIdx: i;
				if({ p:flex && p:sizePt <= 0.0 }, {
					sizes:add(item: 0);
					flexCount: flexCount + 1;
				}, {
					local Int is rawPx: if({ p:sizePt > 0.0 }, { activeScale:px(pt: p:sizePt) }, { activeScale:px(pt: p:minSizePt) });
					local Int is clamped: :clampPanelPx(p: p, px: rawPx, totalAvail: avail);
					sizes:add(item: clamped);
					used: used + clamped;
				});
			});
			i: i + 1;
		});

		local Int is rem: if({ avail > used }, { avail - used }, { 0 });
		if({ flexCount > 0 }, {
			local Int is perFlex: rem / flexCount;
			local Int is extra: rem - (perFlex * flexCount);
			i: 0;
			while({ i < count }, {
				local GridFlexPanel is p: panels:get(index: i);
				if({ p:visible && p:flex && p:sizePt <= 0.0 }, {
					local Int is alloc: perFlex + (if({ extra > 0 }, { 1 }, { 0 }));
					if({ extra > 0 }, { extra: extra - 1; });
					sizes:set(index: i, item: :clampPanelPx(p: p, px: alloc, totalAvail: avail));
				});
				i: i + 1;
			});
		}, {
			if({ rem > 0 && lastVisIdx >= 0 }, {
				local GridFlexPanel is lp: panels:get(index: lastVisIdx);
				sizes:set(index: lastVisIdx, item: :clampPanelPx(p: lp, px: sizes:get(index: lastVisIdx) + rem, totalAvail: avail));
			});
		});

		# Clamp total if fixed sizes exceeded available space
		local Int is sum: 0;
		i: 0;
		while({ i < count }, {
			sum: sum + sizes:get(index: i);
			i: i + 1;
		});
		if({ sum > avail }, {
			local Int is over: sum - avail;
			i: count - 1;
			while({ i >= 0 && over > 0 }, {
				if({ panels:get(index: i):visible }, {
					local Int is cur: sizes:get(index: i);
					local Int is minPx: activeScale:px(pt: panels:get(index: i):minSizePt);
					local Int is reducible: if({ cur > minPx }, { cur - minPx }, { 0 });
					local Int is cut: if({ reducible > over }, { over }, { reducible });
					sizes:set(index: i, item: cur - cut);
					over: over - cut;
				});
				i: i - 1;
			});
		});
		return sizes;
	}

	replace Function of Size is measure(Constraints is c){
		local Int is w: if({ c:isBoundedW() }, { c:clampW(w: c:maxW) }, { c:clampW(w: 320) });
		local Int is prefH: if({ heightPt > 0.0 }, { activeScale:px(pt: heightPt) }, { 240 });
		local Int is h: if({ heightPt > 0.0 && !c:isBoundedH() }, {
			c:clampH(h: prefH)
		}, {
			if({ c:isBoundedH() }, { c:clampH(h: c:maxH) }, { c:clampH(h: prefH) })
		});
		local Int is totalMain: if({ horizontal }, { w }, { h });
		local Array of Int is sizes: :computeSizes(totalMain: totalMain);
		local Int is i: 0;
		while({ i < panels:length() }, {
			local Int is szMain: sizes:get(index: i);
			local Constraints is chC: if({ horizontal }, {
				Constraints(minW: szMain, maxW: szMain, minH: h, maxH: h)
			}, {
				Constraints(minW: w, maxW: w, minH: szMain, maxH: szMain)
			});
			panels:get(index: i):child:measure(c: chC);
			i: i + 1;
		});
		desiredSize: Size(width: w, height: h);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is count: panels:length();
		local Int is totalMain: if({ horizontal }, { bounds:width }, { bounds:height });
		:panelSizesPx: :computeSizes(totalMain: totalMain);
		:dividerPosPx: Array();
		:dividerLeftIdx: Array();
		:dividerRightIdx: Array();
		local Int is sp: :spacingPx();
		local Int is cur: if({ horizontal }, { bounds:x }, { bounds:y });
		local Int is i: 0;
		while({ i < count }, {
			local GridFlexPanel is p: panels:get(index: i);
			local Int is szMain: panelSizesPx:get(index: i);
			if({ !p:visible }, {
				p:child:arrange(bounds: Rect(x: cur, y: bounds:y, width: 0, height: 0));
			}, {
				local Rect is chBounds: if({ horizontal }, {
					Rect(x: cur, y: bounds:y, width: szMain, height: bounds:height)
				}, {
					Rect(x: bounds:x, y: cur, width: bounds:width, height: szMain)
				});
				local SewNode is ch: p:child;
				local Constraints is chC: Constraints(minW: chBounds:width, maxW: chBounds:width, minH: chBounds:height, maxH: chBounds:height);
				ch:measure(c: chC);
				ch:arrange(bounds: chBounds);
				cur: cur + szMain;
				local Int is nextVisIdx: -1;
				local Int is ni: i + 1;
				while({ ni < count && nextVisIdx < 0 }, {
					if({ panels:get(index: ni):visible }, { nextVisIdx: ni; });
					ni: ni + 1;
				});
				if({ nextVisIdx >= 0 }, {
					dividerPosPx:add(item: cur);
					dividerLeftIdx:add(item: i);
					dividerRightIdx:add(item: nextVisIdx);
					cur: cur + sp;
				});
			});
			i: i + 1;
		});
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		local Int is count: panels:length();
		local Int is i: 0;
		while({ i < count }, {
			local SewNode is ch: panels:get(index: i):child;
			local Rect is cb: ch:bounds();
			if({ cb:width > 0 && cb:height > 0 }, {
				ch:paint(ctx: ctx);
			});
			i: i + 1;
		});
		local Int is sp: :spacingPx();
		if({ sp > 0 }, {
			local Int is di: 0;
			local Int is linePx: activeTheme:linePx(scaleFactor: activeScale:factor);
			while({ di < dividerPosPx:length() }, {
				local Int is dpos: dividerPosPx:get(index: di);
				local Boolean is active: (dragDivider == di) || (hoverDivider == di && movable);
				local Int is bgCol: if({ active }, { activeTheme:hoverBg }, { activeTheme:toolbarBg });
				if({ horizontal }, {
					ctx:fillRect(x: dpos, y: b:y, w: sp, h: b:height, color: bgCol);
					ctx:fillRect(x: dpos + (sp - linePx) / 2, y: b:y, w: linePx, h: b:height, color: if({ active }, { activeTheme:textAccent }, { activeTheme:toolbarBorder }));
				}, {
					ctx:fillRect(x: b:x, y: dpos, w: b:width, h: sp, color: bgCol);
					ctx:fillRect(x: b:x, y: dpos + (sp - linePx) / 2, w: b:width, h: linePx, color: if({ active }, { activeTheme:textAccent }, { activeTheme:toolbarBorder }));
				});
				di: di + 1;
			});
		});
	}

	local Function of Int is dividerAt(Int is x, Int is y){
		if({ !movable }, { return -1; });
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return -1; });
		local Int is pos: if({ horizontal }, { x }, { y });
		local Int is sp: :spacingPx();
		local Int is slop: activeScale:px(pt: 4.0);
		local Int is di: 0;
		while({ di < dividerPosPx:length() }, {
			local Int is dpos: dividerPosPx:get(index: di);
			if({ pos >= dpos - slop && pos <= dpos + sp + slop }, {
				return di;
			});
			di: di + 1;
		});
		return -1;
	}

	local Function of Int is panelIndexAt(Int is x, Int is y){
		local Int is i: 0;
		while({ i < panels:length() }, {
			local Rect is cb: panels:get(index: i):child:bounds();
			if({ x >= cb:x && x < cb:x + cb:width && y >= cb:y && y < cb:y + cb:height }, {
				return i;
			});
			i: i + 1;
		});
		return -1;
	}

	local Function is beginDividerDrag(Int is di, Int is x, Int is y){
		dragDivider: di;
		dragStartPos: if({ horizontal }, { x }, { y });
		local Int is idxA: if({ di >= 0 && di < dividerLeftIdx:length() }, { dividerLeftIdx:get(index: di) }, { -1 });
		local Int is idxB: if({ di >= 0 && di < dividerRightIdx:length() }, { dividerRightIdx:get(index: di) }, { -1 });
		dragStartSizeA: if({ idxA >= 0 && idxA < panelSizesPx:length() }, { panelSizesPx:get(index: idxA) }, { 0 });
		dragStartSizeB: if({ idxB >= 0 && idxB < panelSizesPx:length() }, { panelSizesPx:get(index: idxB) }, { 0 });
	}

	local Function of Float is pxToPt(Int is px){
		local Float is f: activeScale:factor;
		if({ f <= 0.0 }, { return px as Float; });
		return (px as Float) / f;
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		lastMouseX: x;
		lastMouseY: y;
		local Boolean is changed: false;
		local Int is nextHover: :dividerAt(x: x, y: y);
		if({ nextHover != hoverDivider }, {
			hoverDivider: nextHover;
			changed: true;
		});
		local Int is i: 0;
		while({ i < panels:length() }, {
			local SewNode is ch: panels:get(index: i):child;
			if({ nextHover < 0 && ch:blocksPointerAt(x: x, y: y) }, {
				if({ ch:onPointerMove(x: x, y: y) }, { changed: true; });
			}, {
				if({ nextHover >= 0 }, {
					ch:clearHover();
				}, {
					if({ ch:onPointerMove(x: x, y: y) }, { changed: true; });
				});
			});
			i: i + 1;
		});
		return changed;
	}

	replace Function is clearHover(){
		if({ hoverDivider >= 0 }, {
			hoverDivider: -1;
			invalidate();
		});
		times(count: panels:length(), worker: local Function(Int is i){
			panels:get(index: i):child:clearHover();
		});
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return false; });
		local Int is di: :dividerAt(x: x, y: y);
		if({ di >= 0 }, {
			dragChildIdx: -1;
			:beginDividerDrag(di: di, x: x, y: y);
			return true;
		});
		local Int is pi: :panelIndexAt(x: x, y: y);
		if({ pi >= 0 }, {
			dragChildIdx: pi;
			return panels:get(index: pi):child:onPointerClickMod(x: x, y: y, mods: mods);
		});
		return false;
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return false; });
		local Int is pi: :panelIndexAt(x: x, y: y);
		if({ pi >= 0 }, {
			return panels:get(index: pi):child:onRightClickMod(x: x, y: y, mods: mods);
		});
		return false;
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		if({ dragChildIdx >= 0 && dragChildIdx < panels:length() }, {
			return panels:get(index: dragChildIdx):child:onPointerDrag(x: x, y: y, mods: mods);
		});
		if({ movable && dragDivider < 0 }, {
			local Int is di: :dividerAt(x: x, y: y);
			if({ di >= 0 }, {
				:beginDividerDrag(di: di, x: x, y: y);
			});
		});
		if({ dragDivider >= 0 && dragDivider < dividerLeftIdx:length() && dragDivider < dividerRightIdx:length() }, {
			local Int is idxA: dividerLeftIdx:get(index: dragDivider);
			local Int is idxB: dividerRightIdx:get(index: dragDivider);
			local Int is curPos: if({ horizontal }, { x }, { y });
			local Int is delta: curPos - dragStartPos;
			local Int is combined: dragStartSizeA + dragStartSizeB;
			local GridFlexPanel is pA: panels:get(index: idxA);
			local GridFlexPanel is pB: panels:get(index: idxB);
			local Int is minA: activeScale:px(pt: pA:minSizePt);
			local Int is minB: activeScale:px(pt: pB:minSizePt);
			local Int is maxA: if({ pA:maxSizePt > 0.0 }, { activeScale:px(pt: pA:maxSizePt) }, { combined });
			local Int is maxB: if({ pB:maxSizePt > 0.0 }, { activeScale:px(pt: pB:maxSizePt) }, { combined });
			local Int is nextA: dragStartSizeA + delta;
			if({ nextA < minA }, { nextA: minA; });
			if({ nextA > maxA }, { nextA: maxA; });
			if({ combined - nextA < minB }, { nextA: combined - minB; });
			if({ combined - nextA > maxB }, { nextA: combined - maxB; });
			if({ nextA < 0 }, { nextA: 0; });
			local Int is nextB: combined - nextA;
			pA:sizePt: :pxToPt(px: nextA);
			if({ !pB:flex }, {
				pB:sizePt: :pxToPt(px: nextB);
			});
			invalidate();
			return true;
		});
		local Int is pi: :panelIndexAt(x: x, y: y);
		if({ pi >= 0 }, {
			dragChildIdx: pi;
			return panels:get(index: pi):child:onPointerDrag(x: x, y: y, mods: mods);
		});
		return false;
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		if({ dragDivider >= 0 }, {
			dragDivider: -1;
			dragChildIdx: -1;
			invalidate();
			return true;
		});
		if({ dragChildIdx >= 0 && dragChildIdx < panels:length() }, {
			local Int is pi: dragChildIdx;
			dragChildIdx: -1;
			return panels:get(index: pi):child:onPointerUp(x: x, y: y);
		});
		local Boolean is changed: false;
		local Int is i: 0;
		while({ i < panels:length() }, {
			if({ panels:get(index: i):child:onPointerUp(x: x, y: y) }, { changed: true; });
			i: i + 1;
		});
		return changed;
	}

	replace Function of Boolean is onScroll(Int is deltaY){
		local Int is pi: if({ lastMouseX >= 0 && lastMouseY >= 0 }, { :panelIndexAt(x: lastMouseX, y: lastMouseY) }, { -1 });
		if({ pi >= 0 }, {
			return panels:get(index: pi):child:onScroll(deltaY: deltaY);
		});
		local Int is i: 0;
		while({ i < panels:length() }, {
			if({ panels:get(index: i):child:onScroll(deltaY: deltaY) }, { return true; });
			i: i + 1;
		});
		return false;
	}

	replace Function of Boolean is onScrollX(Int is deltaX){
		local Int is pi: if({ lastMouseX >= 0 && lastMouseY >= 0 }, { :panelIndexAt(x: lastMouseX, y: lastMouseY) }, { -1 });
		if({ pi >= 0 }, {
			return panels:get(index: pi):child:onScrollX(deltaX: deltaX);
		});
		local Int is i: 0;
		while({ i < panels:length() }, {
			if({ panels:get(index: i):child:onScrollX(deltaX: deltaX) }, { return true; });
			i: i + 1;
		});
		return false;
	}

	replace Function of Boolean is onOverlayScroll(Int is deltaY){
		local Int is i: 0;
		while({ i < panels:length() }, {
			if({ panels:get(index: i):child:onOverlayScroll(deltaY: deltaY) }, { return true; });
			i: i + 1;
		});
		return false;
	}

	replace Function of Boolean is onOverlayScrollX(Int is deltaX){
		local Int is i: 0;
		while({ i < panels:length() }, {
			if({ panels:get(index: i):child:onOverlayScrollX(deltaX: deltaX) }, { return true; });
			i: i + 1;
		});
		return false;
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		if({ :dividerAt(x: x, y: y) >= 0 }, {
			return if({ horizontal }, { CursorShape:EW_RESIZE }, { CursorShape:NS_RESIZE });
		});
		local Int is pi: :panelIndexAt(x: x, y: y);
		if({ pi >= 0 }, { return panels:get(index: pi):child:cursorAt(x: x, y: y); });
		return CursorShape:DEFAULT;
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		local Int is i: 0;
		while({ i < panels:length() }, {
			if({ panels:get(index: i):child:onKey(key: key, mods: mods) }, { return true; });
			i: i + 1;
		});
		return false;
	}

	replace Function of Boolean is onText(String is ch, Int is mods){
		local Int is i: 0;
		while({ i < panels:length() }, {
			if({ panels:get(index: i):child:onText(ch: ch, mods: mods) }, { return true; });
			i: i + 1;
		});
		return false;
	}

	replace Function of Boolean is tick(Int is nowMs){
		local Boolean is changed: false;
		local Int is i: 0;
		while({ i < panels:length() }, {
			if({ panels:get(index: i):child:tick(nowMs: nowMs) }, { changed: true; });
			i: i + 1;
		});
		return changed;
	}
}
