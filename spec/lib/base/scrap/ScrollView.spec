#! Package base:scrap
#! Scrollable viewport container (`SewNode`) with configurable scrollbar side (`'right'` default or `'left'`).

Class of SewNode is ScrollView{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', CursorShape],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'sew', DockSide],
		['base', 'fabric', Theme],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext]
	];

	SewNode is child: SewNode();
	Int is scrollX: 0;
	Int is scrollY: 0;
	Int is contentW: 0;
	Int is contentH: 0;
	Float is barWidthPt: 0.0;
	Float is heightPt: 0.0;
	Boolean is fitContentWidth: false;
	Boolean is allowHScroll: false;
	Boolean is alwaysShowVScroll: false;
	Boolean is alwaysShowHScroll: false;
	DockSide is scrollbarSide: DockSide:RIGHT;
	Int is dragMode: 0;
	Int is dragGrabOffset: 0;
	Boolean is childCapturing: false;
	Boolean is hoverVThumb: false;
	Boolean is hoverHThumb: false;
	Boolean is pointerInside: false;

	replace Function is init(
		SewNode is child,
		Float is barWidthPt: 0.0,
		DockSide is scrollbarSide: DockSide:RIGHT,
		Float is heightPt: 0.0,
		Boolean is fitContentWidth: false,
		Boolean is allowHScroll: false,
		Boolean is alwaysShowVScroll: false,
		Boolean is alwaysShowHScroll: false
	){
		:child: child;
		:barWidthPt: barWidthPt;
		:heightPt: heightPt;
		:fitContentWidth: fitContentWidth;
		:allowHScroll: allowHScroll;
		:alwaysShowVScroll: alwaysShowVScroll;
		:alwaysShowHScroll: alwaysShowHScroll;
		:scrollbarSide: scrollbarSide;
		:scrollX: 0;
		:scrollY: 0;
		:contentW: 0;
		:contentH: 0;
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		child:applyTheme(theme: theme);
	}

	replace Function is setScale(Scale is scale){
		:activeScale: scale;
		child:setScale(scale: scale);
	}

	replace Function is bindDirty(Function is cb){
		:dirtyListeners: Array([cb]);
		child:bindDirty(cb: cb);
	}

	replace Function of Size is measure(Constraints is c){
		local Int is bw: activeScale:px(pt: if({ barWidthPt > 0.0 }, { barWidthPt }, { activeTheme:scrollbarWidthPt }));
		local Int is availW: if({ alwaysShowVScroll && c:maxW > bw }, { c:maxW - bw }, { c:maxW });
		local Int is childMaxW: if({ allowHScroll || alwaysShowHScroll }, { 1000000 }, { availW });
		local Size is cs: child:measure(c: Constraints(minW: if({ fitContentWidth }, { 0 }, { availW }), maxW: childMaxW, minH: 0, maxH: 1000000));
		contentW: cs:width;
		contentH: cs:height;
		local Int is outH: if({ heightPt > 0.0 }, { c:clampH(h: activeScale:px(pt: heightPt)) }, { c:maxH });
		local Boolean is needV: bw > 2 && (alwaysShowVScroll || contentH > outH);
		if({ needV && !alwaysShowVScroll && !fitContentWidth && c:maxW > bw }, {
			local Int is vw: c:maxW - bw;
			local Int is nextMaxW: if({ allowHScroll || alwaysShowHScroll }, { 1000000 }, { vw });
			cs: child:measure(c: Constraints(minW: vw, maxW: nextMaxW, minH: 0, maxH: 1000000));
			contentW: cs:width;
			contentH: cs:height;
		});
		local Int is outW: if({ fitContentWidth }, { c:clampW(w: contentW + (if({ needV }, { bw }, { 0 }))) }, { c:maxW });
		desiredSize: Size(width: outW, height: outH);
		return desiredSize;
	}

	local Function of Int is viewWidth(Rect is b){
		local Int is bw: activeScale:px(pt: if({ barWidthPt > 0.0 }, { barWidthPt }, { activeTheme:scrollbarWidthPt }));
		if({ bw <= 2 || b:width <= bw }, { return b:width; });
		local Boolean is needV: alwaysShowVScroll || contentH > b:height || ((alwaysShowHScroll || contentW > b:width - bw) && contentH > b:height - bw);
		return if({ needV }, { b:width - bw }, { b:width });
	}

	local Function of Int is viewHeight(Rect is b){
		local Int is bw: activeScale:px(pt: if({ barWidthPt > 0.0 }, { barWidthPt }, { activeTheme:scrollbarWidthPt }));
		local Int is vw: :viewWidth(b: b);
		if({ bw > 2 && (alwaysShowHScroll || contentW > vw) && b:height > bw }, {
			return b:height - bw;
		});
		return b:height;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is bw: activeScale:px(pt: if({ barWidthPt > 0.0 }, { barWidthPt }, { activeTheme:scrollbarWidthPt }));
		local Int is vw: :viewWidth(b: bounds);
		local Int is vh: :viewHeight(b: bounds);
		local Int is cx: if({ scrollbarSide == DockSide:LEFT && vw < bounds:width }, { bounds:x + bw }, { bounds:x });
		local Int is maxScrollX: if({ contentW > vw }, { contentW - vw }, { 0 });
		local Int is maxScrollY: if({ contentH > vh }, { contentH - vh }, { 0 });
		if({ scrollX > maxScrollX }, { scrollX: maxScrollX; });
		if({ scrollX < 0 }, { scrollX: 0; });
		if({ scrollY > maxScrollY }, { scrollY: maxScrollY; });
		if({ scrollY < 0 }, { scrollY: 0; });
		local Int is cw: if({ contentW > vw }, { contentW }, { vw });
		local Int is ch: if({ contentH > vh }, { contentH }, { vh });
		child:arrange(bounds: Rect(x: cx - scrollX, y: bounds:y - scrollY, width: cw, height: ch));
	}

	replace Function of Boolean is onScroll(Int is deltaY){
		if({ !pointerInside }, { return false; });
		if({ child:onScroll(deltaY: deltaY) }, { return true; });
		local Rect is b: bounds();
		local Int is vh: :viewHeight(b: b);
		local Int is maxScroll: if({ contentH > vh }, { contentH - vh }, { 0 });
		if({ maxScroll <= 0 }, { return false; });
		local Int is step: activeScale:px(pt: 36.0);
		local Int is prev: scrollY;
		local Int is next: scrollY + (deltaY * step) / 10;
		if({ next < 0 }, { next: 0; });
		if({ next > maxScroll }, { next: maxScroll; });
		if({ next == prev }, { return false; });
		scrollY: next;
		:arrange(bounds: b);
		invalidate();
		return true;
	}

	replace Function of Boolean is onScrollX(Int is deltaX){
		if({ !pointerInside }, { return false; });
		if({ child:onScrollX(deltaX: deltaX) }, { return true; });
		local Rect is b: bounds();
		local Int is vw: :viewWidth(b: b);
		local Int is maxScroll: if({ contentW > vw }, { contentW - vw }, { 0 });
		if({ maxScroll <= 0 }, { return false; });
		local Int is step: activeScale:px(pt: 36.0);
		local Int is prev: scrollX;
		local Int is next: scrollX + (deltaX * step) / 10;
		if({ next < 0 }, { next: 0; });
		if({ next > maxScroll }, { next: maxScroll; });
		if({ next == prev }, { return false; });
		scrollX: next;
		:arrange(bounds: b);
		invalidate();
		return true;
	}

	local Function of Int is thumbLen(Int is viewLen, Int is contentLen){
		if({ contentLen <= viewLen || viewLen <= 0 }, { return viewLen; });
		local Int is t: (viewLen * viewLen) / contentLen;
		local Int is minT: activeScale:px(pt: 22.0);
		if({ t < minT }, { t: minT; });
		if({ t > viewLen }, { t: viewLen; });
		return t;
	}

	local Function of Int is thumbPos(Int is scroll, Int is viewLen, Int is contentLen, Int is tLen){
		local Int is maxScroll: contentLen - viewLen;
		local Int is range: viewLen - tLen;
		if({ maxScroll <= 0 || range <= 0 }, { return 0; });
		return (scroll * range) / maxScroll;
	}

	local Function of Int is scrollFromThumb(Int is pos, Int is viewLen, Int is contentLen, Int is tLen){
		local Int is maxScroll: contentLen - viewLen;
		local Int is range: viewLen - tLen;
		if({ maxScroll <= 0 || range <= 0 }, { return 0; });
		local Int is s: (pos * maxScroll) / range;
		if({ s < 0 }, { s: 0; });
		if({ s > maxScroll }, { s: maxScroll; });
		return s;
	}

	replace Function of Boolean is blocksPointerAt(Int is x, Int is y){
		if({ pointerTransparent }, { return false; });
		return :containsPoint(x: x, y: y);
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return false; });
		local Int is bw: activeScale:px(pt: if({ barWidthPt > 0.0 }, { barWidthPt }, { activeTheme:scrollbarWidthPt }));
		local Int is vw: :viewWidth(b: b);
		local Int is vh: :viewHeight(b: b);
		local Int is vsx: if({ scrollbarSide == DockSide:LEFT }, { b:x }, { b:x + vw });
		local Int is cx: if({ scrollbarSide == DockSide:LEFT && vw < b:width }, { b:x + bw }, { b:x });

		## Vertical scrollbar track / thumb press
		if({ vw < b:width && x >= vsx && x < vsx + bw && y >= b:y && y < b:y + vh }, {
			if({ contentH > vh && vh > 0 }, {
				local Int is tH: :thumbLen(viewLen: vh, contentLen: contentH);
				local Int is tY: b:y + :thumbPos(scroll: scrollY, viewLen: vh, contentLen: contentH, tLen: tH);
				dragMode: 1;
				if({ y >= tY && y < tY + tH }, {
					dragGrabOffset: y - tY;
				}, {
					dragGrabOffset: tH / 2;
					scrollY: :scrollFromThumb(pos: y - b:y - dragGrabOffset, viewLen: vh, contentLen: contentH, tLen: tH);
					:arrange(bounds: b);
					invalidate();
				});
				return true;
			});
			return false;
		});

		## Horizontal scrollbar track / thumb press
		if({ contentW > vw && y >= b:y + vh && y < b:y + b:height && x >= cx && x < cx + vw }, {
			local Int is tW: :thumbLen(viewLen: vw, contentLen: contentW);
			local Int is tX: cx + :thumbPos(scroll: scrollX, viewLen: vw, contentLen: contentW, tLen: tW);
			dragMode: 2;
			if({ x >= tX && x < tX + tW }, {
				dragGrabOffset: x - tX;
			}, {
				dragGrabOffset: tW / 2;
				scrollX: :scrollFromThumb(pos: x - cx - dragGrabOffset, viewLen: vw, contentLen: contentW, tLen: tW);
				:arrange(bounds: b);
				invalidate();
			});
			return true;
		});

		dragMode: 0;
		if({ (x >= cx && x < cx + vw && y >= b:y && y < b:y + vh) || child:blocksPointerAt(x: x, y: y) }, {
			childCapturing: child:onPointerClickMod(x: x, y: y, mods: mods);
			return childCapturing;
		});
		childCapturing: false;
		return false;
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		local Rect is b: bounds();
		local Int is bw: activeScale:px(pt: if({ barWidthPt > 0.0 }, { barWidthPt }, { activeTheme:scrollbarWidthPt }));
		local Int is vw: :viewWidth(b: b);
		local Int is vh: :viewHeight(b: b);
		local Int is cx: if({ scrollbarSide == DockSide:LEFT }, { b:x + bw }, { b:x });
		if({ dragMode == 1 && contentH > vh }, {
			local Int is tH: :thumbLen(viewLen: vh, contentLen: contentH);
			local Int is nextY: :scrollFromThumb(pos: y - b:y - dragGrabOffset, viewLen: vh, contentLen: contentH, tLen: tH);
			if({ nextY != scrollY }, {
				scrollY: nextY;
				:arrange(bounds: b);
				invalidate();
				return true;
			});
			return false;
		});
		if({ dragMode == 2 && contentW > vw }, {
			local Int is tW: :thumbLen(viewLen: vw, contentLen: contentW);
			local Int is nextX: :scrollFromThumb(pos: x - cx - dragGrabOffset, viewLen: vw, contentLen: contentW, tLen: tW);
			if({ nextX != scrollX }, {
				scrollX: nextX;
				:arrange(bounds: b);
				invalidate();
				return true;
			});
			return false;
		});
		if({ childCapturing }, {
			return child:onPointerDrag(x: x, y: y, mods: mods);
		});
		if({ x >= cx && x < cx + vw && y >= b:y && y < b:y + vh }, {
			childCapturing: true;
			return child:onPointerDrag(x: x, y: y, mods: mods);
		});
		return false;
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		dragMode: 0;
		childCapturing: false;
		return child:onPointerUp(x: x, y: y);
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return false; });
		return child:onRightClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Rect is b: bounds();
		:pointerInside: :containsPoint(x: x, y: y);
		local Int is bw: activeScale:px(pt: if({ barWidthPt > 0.0 }, { barWidthPt }, { activeTheme:scrollbarWidthPt }));
		local Int is vw: :viewWidth(b: b);
		local Int is vh: :viewHeight(b: b);
		local Int is vsx: if({ scrollbarSide == DockSide:LEFT }, { b:x }, { b:x + vw });
		local Int is cx: if({ scrollbarSide == DockSide:LEFT && vw < b:width }, { b:x + bw }, { b:x });
		local Boolean is nextV: false;
		local Boolean is nextH: false;
		if({ bw > 2 && vw < b:width && contentH > vh && vh > 0 && x >= vsx && x < vsx + bw && y >= b:y && y < b:y + vh }, {
			local Int is tH: :thumbLen(viewLen: vh, contentLen: contentH);
			local Int is tY: b:y + :thumbPos(scroll: scrollY, viewLen: vh, contentLen: contentH, tLen: tH);
			if({ y >= tY && y < tY + tH }, { nextV: true; });
		});
		if({ bw > 2 && contentW > vw && vw > 0 && y >= b:y + vh && y < b:y + b:height && x >= cx && x < cx + vw }, {
			local Int is tW: :thumbLen(viewLen: vw, contentLen: contentW);
			local Int is tX: cx + :thumbPos(scroll: scrollX, viewLen: vw, contentLen: contentW, tLen: tW);
			if({ x >= tX && x < tX + tW }, { nextH: true; });
		});
		local Boolean is changed: false;
		if({ nextV != hoverVThumb || nextH != hoverHThumb }, {
			:hoverVThumb: nextV;
			:hoverHThumb: nextH;
			changed: true;
		});
		if({ x >= b:x && x < b:x + b:width && y >= b:y && y < b:y + b:height }, {
			if({ child:onPointerMove(x: x, y: y) }, { changed: true; });
		}, {
			child:clearHover();
		});
		return changed;
	}

	replace Function is clearHover(){
		:pointerInside: false;
		if({ hoverVThumb || hoverHThumb }, {
			:hoverVThumb: false;
			:hoverHThumb: false;
		});
		child:clearHover();
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		return child:onKey(key: key, mods: mods);
	}

	replace Function of Boolean is onText(String is ch, Int is mods){
		return child:onText(ch: ch, mods: mods);
	}

	replace Function of Boolean is tick(Int is nowMs){
		return child:tick(nowMs: nowMs);
	}

	replace Function is collectFocusables(Array of SewNode is out){
		if({ child:canFocus() }, { out:add(item: child); }, { child:collectFocusables(out: out); });
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
		local Rect is b: bounds();
		local Int is bw: activeScale:px(pt: if({ barWidthPt > 0.0 }, { barWidthPt }, { activeTheme:scrollbarWidthPt }));
		local Int is vw: :viewWidth(b: b);
		local Int is vh: :viewHeight(b: b);
		local Int is cx: if({ scrollbarSide == DockSide:LEFT }, { b:x + bw }, { b:x });
		if({ x < cx || x >= cx + vw || y < b:y || y >= b:y + vh }, { return ''; });
		return child:tooltipAt(x: x, y: y);
	}

	replace Function of CursorShape is cursorAt(Int is x, Int is y){
		local Rect is b: bounds();
		local Int is bw: activeScale:px(pt: if({ barWidthPt > 0.0 }, { barWidthPt }, { activeTheme:scrollbarWidthPt }));
		local Int is vw: :viewWidth(b: b);
		local Int is vh: :viewHeight(b: b);
		local Int is cx: if({ scrollbarSide == DockSide:LEFT && vw < b:width }, { b:x + bw }, { b:x });
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return CursorShape:DEFAULT; });
		if({ x < cx || x >= cx + vw || y >= b:y + vh }, { return CursorShape:POINTER; });
		return child:cursorAt(x: x, y: y);
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });

		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: activeTheme:windowBg);

		local Int is bw: activeScale:px(pt: if({ barWidthPt > 0.0 }, { barWidthPt }, { activeTheme:scrollbarWidthPt }));
		local Int is vw: :viewWidth(b: b);
		local Int is vh: :viewHeight(b: b);
		local Int is cx: if({ scrollbarSide == DockSide:LEFT && vw < b:width }, { b:x + bw }, { b:x });
		ctx:setClip(x: cx, y: b:y, w: vw, h: vh);
		child:paint(ctx: ctx);
		ctx:clearClip();

		## Vertical scrollbar track & thumb on specified side ('right' default or 'left')
		if({ bw > 2 }, {
			local Int is divPx: activeTheme:dividerPx(scaleFactor: activeScale:factor);
			local Int is btnPx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
			local Int is btnRad: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);
			local Int is shBlur: activeScale:px(pt: activeTheme:buttonShadowBlurPt);
			local Int is shOffX: activeScale:px(pt: activeTheme:buttonShadowOffsetXPt);
			local Int is shOffY: activeScale:px(pt: activeTheme:buttonShadowOffsetYPt);
			local Int is shCol: if({ shBlur > 0 || shOffX != 0 || shOffY != 0 }, { 1426063360 }, { 0 });

			local Int is sx: if({ scrollbarSide == DockSide:LEFT }, { b:x }, { b:x + vw });
			if({ vw < b:width }, {
				ctx:setClip(x: sx, y: b:y, w: bw, h: vh);
				ctx:fillRect(x: sx, y: b:y, w: bw, h: vh, color: activeTheme:menuBg);
				if({ divPx > 0 }, {
					local Int is borderX: if({ scrollbarSide == DockSide:LEFT }, { sx + bw - divPx }, { sx });
					ctx:drawDivider(x: borderX, y: b:y, w: divPx, h: vh, color: activeTheme:dividerColorArgb(), thickness: divPx, style: activeTheme:dividerStyle);
				});
				if({ contentH > vh && vh > 0 }, {
					local Int is thumbH: (vh * vh) / contentH;
					if({ thumbH < activeScale:px(pt: 22.0) }, { thumbH: activeScale:px(pt: 22.0); });
					if({ thumbH > vh }, { thumbH: vh; });
					local Int is maxScroll: contentH - vh;
					local Int is trackRange: vh - thumbH;
					local Int is thumbY: b:y + if({ maxScroll > 0 }, { (scrollY * trackRange) / maxScroll }, { 0 });
					local Int is tx: if({ scrollbarSide == DockSide:LEFT }, { sx + 1 }, { sx + divPx + 1 });
					local Int is tw: bw - divPx - 2;
					if({ tw > 2 && thumbH > 2 }, {
						ctx:setClip(x: tx, y: b:y, w: tw, h: vh);
						local FillStyle is vFill: activeTheme:resolveButtonFill(enabled: true, selected: false, hovered: hoverVThumb || dragMode == 1);
						ctx:drawStyledBoxFill(
							x: tx, y: thumbY + 1, w: tw, h: thumbH - 2,
							fill: vFill, borderColor: activeTheme:buttonBorderColorArgb(),
							thickness: btnPx, radius: btnRad, style: activeTheme:buttonBorderStyle,
							shadowOffsetX: shOffX, shadowOffsetY: shOffY, shadowBlur: shBlur, shadowColor: shCol
						);
						ctx:clearClip();
					});
				});
				ctx:clearClip();
			});

			## Horizontal scrollbar track & thumb along bottom when needed or persistent
			if({ vh < b:height && vw > 0 }, {
				local Int is hy: b:y + vh;
				ctx:setClip(x: cx, y: hy, w: vw, h: bw);
				ctx:fillRect(x: cx, y: hy, w: vw, h: bw, color: activeTheme:menuBg);
				if({ divPx > 0 }, {
					ctx:drawDivider(x: cx, y: hy, w: vw, h: divPx, color: activeTheme:dividerColorArgb(), thickness: divPx, style: activeTheme:dividerStyle);
				});
				if({ contentW > vw }, {
					local Int is thumbW: (vw * vw) / contentW;
					if({ thumbW < activeScale:px(pt: 22.0) }, { thumbW: activeScale:px(pt: 22.0); });
					if({ thumbW > vw }, { thumbW: vw; });
					local Int is maxScrollX: contentW - vw;
					local Int is trackRangeX: vw - thumbW;
					local Int is thumbX: cx + if({ maxScrollX > 0 }, { (scrollX * trackRangeX) / maxScrollX }, { 0 });
					local Int is ty: hy + divPx + 1;
					local Int is th: bw - divPx - 2;
					if({ th > 2 && thumbW > 2 }, {
						ctx:setClip(x: cx, y: ty, w: vw, h: th);
						local FillStyle is hFill: activeTheme:resolveButtonFill(enabled: true, selected: false, hovered: hoverHThumb || dragMode == 2);
						ctx:drawStyledBoxFill(
							x: thumbX + 1, y: ty, w: thumbW - 2, h: th,
							fill: hFill, borderColor: activeTheme:buttonBorderColorArgb(),
							thickness: btnPx, radius: btnRad, style: activeTheme:buttonBorderStyle,
							shadowOffsetX: shOffX, shadowOffsetY: shOffY, shadowBlur: shBlur, shadowColor: shCol
						);
						ctx:clearClip();
					});
				});
				ctx:clearClip();
				if({ vw < b:width }, {
					ctx:fillRect(x: sx, y: hy, w: bw, h: bw, color: activeTheme:toolbarBg);
				});
			});
		});
	}

	replace Function is paintOverlay(DrawContext is ctx){
		child:paintOverlay(ctx: ctx);
	}

	replace Function of Boolean is closePopupsOutside(Int is x, Int is y){
		return child:closePopupsOutside(x: x, y: y);
	}

	replace Function of Boolean is onOverlayPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return child:onOverlayPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onOverlayPointerMove(Int is x, Int is y){
		return child:onOverlayPointerMove(x: x, y: y);
	}

	replace Function of Boolean is onOverlayPointerDrag(Int is x, Int is y, Int is mods: 0){
		return child:onOverlayPointerDrag(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onOverlayPointerUp(Int is x, Int is y){
		return child:onOverlayPointerUp(x: x, y: y);
	}
}
