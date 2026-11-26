#! Package base:scrap
#! Scrollable viewport container (`SewNode`) with configurable scrollbar side (`'right'` default or `'left'`).

Class of SewNode is ScrollView{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext]
	];

	SewNode is child: SewNode();
	Int is scrollX: 0;
	Int is scrollY: 0;
	Int is contentW: 0;
	Int is contentH: 0;
	Float is barWidthPt: 12.0;
	String is scrollbarSide: 'right';
	Int is dragMode: 0;
	Int is dragGrabOffset: 0;

	replace Function is init(SewNode is child, Float is barWidthPt: 12.0, String is scrollbarSide: 'right'){
		:child: child;
		:barWidthPt: barWidthPt;
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
		local Int is bw: activeScale:px(pt: barWidthPt);
		local Int is vw: if({ c:maxW > bw }, { c:maxW - bw }, { c:maxW });
		local Int is vh: if({ c:maxH > bw }, { c:maxH - bw }, { c:maxH });
		local Size is cs: child:measure(c: Constraints(minW: vw, maxW: vw, minH: 0, maxH: vh));
		contentW: cs:width;
		contentH: cs:height;
		desiredSize: Size(width: c:maxW, height: c:maxH);
		return desiredSize;
	}

	local Function of Int is viewWidth(Rect is b){
		local Int is bw: activeScale:px(pt: barWidthPt);
		return if({ b:width > bw }, { b:width - bw }, { b:width });
	}

	local Function of Int is viewHeight(Rect is b){
		local Int is bw: activeScale:px(pt: barWidthPt);
		local Int is vw: :viewWidth(b: b);
		if({ contentW > vw && b:height > bw }, {
			return b:height - bw;
		});
		return b:height;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is bw: activeScale:px(pt: barWidthPt);
		local Int is vw: :viewWidth(b: bounds);
		local Int is vh: :viewHeight(b: bounds);
		local Int is cx: if({ scrollbarSide == 'left' }, { bounds:x + bw }, { bounds:x });
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

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		local Rect is b: bounds();
		if({ x < b:x || x >= b:x + b:width || y < b:y || y >= b:y + b:height }, { return false; });
		local Int is bw: activeScale:px(pt: barWidthPt);
		local Int is vw: :viewWidth(b: b);
		local Int is vh: :viewHeight(b: b);
		local Int is vsx: if({ scrollbarSide == 'left' }, { b:x }, { b:x + vw });
		local Int is cx: if({ scrollbarSide == 'left' }, { b:x + bw }, { b:x });

		## Vertical scrollbar track / thumb press
		if({ x >= vsx && x < vsx + bw && y >= b:y && y < b:y + vh }, {
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
		return child:onPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		local Rect is b: bounds();
		local Int is bw: activeScale:px(pt: barWidthPt);
		local Int is vw: :viewWidth(b: b);
		local Int is vh: :viewHeight(b: b);
		local Int is cx: if({ scrollbarSide == 'left' }, { b:x + bw }, { b:x });
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
		return child:onPointerDrag(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		dragMode: 0;
		return child:onPointerUp(x: x, y: y);
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		return child:onPointerMove(x: x, y: y);
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

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });

		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: activeTheme:windowBg);

		local Int is bw: activeScale:px(pt: barWidthPt);
		local Int is vw: :viewWidth(b: b);
		local Int is vh: :viewHeight(b: b);
		local Int is cx: if({ scrollbarSide == 'left' }, { b:x + bw }, { b:x });
		ctx:setClip(x: cx, y: b:y, w: vw, h: vh);
		child:paint(ctx: ctx);
		ctx:clearClip();

		## Vertical scrollbar track & thumb on specified side ('right' default or 'left')
		if({ bw > 2 }, {
			local Int is sx: if({ scrollbarSide == 'left' }, { b:x }, { b:x + vw });
			ctx:fillRect(x: sx, y: b:y, w: bw, h: vh, color: activeTheme:menuBg);
			local Int is borderX: if({ scrollbarSide == 'left' }, { sx + bw - 1 }, { sx });
			ctx:fillRect(x: borderX, y: b:y, w: 1, h: vh, color: activeTheme:toolbarBorder);
			if({ contentH > vh && vh > 0 }, {
				local Int is thumbH: (vh * vh) / contentH;
				if({ thumbH < activeScale:px(pt: 22.0) }, { thumbH: activeScale:px(pt: 22.0); });
				if({ thumbH > vh }, { thumbH: vh; });
				local Int is maxScroll: contentH - vh;
				local Int is trackRange: vh - thumbH;
				local Int is thumbY: b:y + if({ maxScroll > 0 }, { (scrollY * trackRange) / maxScroll }, { 0 });
				ctx:fillRect(x: sx + 2, y: thumbY + 1, w: bw - 4, h: thumbH - 2, color: activeTheme:activeBg);
			});

			## Horizontal scrollbar track & thumb along bottom when content overflows horizontally
			if({ contentW > vw && vh < b:height && vw > 0 }, {
				local Int is hy: b:y + vh;
				ctx:fillRect(x: cx, y: hy, w: vw, h: bw, color: activeTheme:menuBg);
				ctx:fillRect(x: cx, y: hy, w: vw, h: 1, color: activeTheme:toolbarBorder);
				local Int is thumbW: (vw * vw) / contentW;
				if({ thumbW < activeScale:px(pt: 22.0) }, { thumbW: activeScale:px(pt: 22.0); });
				if({ thumbW > vw }, { thumbW: vw; });
				local Int is maxScrollX: contentW - vw;
				local Int is trackRangeX: vw - thumbW;
				local Int is thumbX: cx + if({ maxScrollX > 0 }, { (scrollX * trackRangeX) / maxScrollX }, { 0 });
				ctx:fillRect(x: thumbX + 1, y: hy + 2, w: thumbW - 2, h: bw - 4, color: activeTheme:activeBg);
				ctx:fillRect(x: sx, y: hy, w: bw, h: bw, color: activeTheme:toolbarBg);
			});
		});
	}
}
