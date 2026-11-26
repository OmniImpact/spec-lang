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
	Int is scrollY: 0;
	Int is contentH: 0;
	Float is barWidthPt: 12.0;
	String is scrollbarSide: 'right';

	replace Function is init(SewNode is child, Float is barWidthPt: 12.0, String is scrollbarSide: 'right'){
		:child: child;
		:barWidthPt: barWidthPt;
		:scrollbarSide: scrollbarSide;
		:scrollY: 0;
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
		local Int is cw: if({ c:maxW > bw }, { c:maxW - bw }, { c:maxW });
		local Size is cs: child:measure(c: Constraints(minW: cw, maxW: cw, minH: 0, maxH: 0));
		contentH: cs:height;
		desiredSize: Size(width: c:maxW, height: c:maxH);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is bw: activeScale:px(pt: barWidthPt);
		local Int is cw: if({ bounds:width > bw }, { bounds:width - bw }, { bounds:width });
		local Int is cx: if({ scrollbarSide == 'left' }, { bounds:x + bw }, { bounds:x });
		local Int is maxScroll: if({ contentH > bounds:height }, { contentH - bounds:height }, { 0 });
		if({ scrollY > maxScroll }, { scrollY: maxScroll; });
		if({ scrollY < 0 }, { scrollY: 0; });
		local Int is ch: if({ contentH > bounds:height }, { contentH }, { bounds:height });
		child:arrange(bounds: Rect(x: cx, y: bounds:y - scrollY, width: cw, height: ch));
	}

	replace Function of Boolean is onScroll(Int is deltaY){
		local Rect is b: bounds();
		local Int is maxScroll: if({ contentH > b:height }, { contentH - b:height }, { 0 });
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

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });

		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: activeTheme:windowBg);

		local Int is bw: activeScale:px(pt: barWidthPt);
		local Int is cw: if({ b:width > bw }, { b:width - bw }, { b:width });
		local Int is cx: if({ scrollbarSide == 'left' }, { b:x + bw }, { b:x });
		ctx:setClip(x: cx, y: b:y, w: cw, h: b:height);
		child:paint(ctx: ctx);
		ctx:clearClip();

		## Draw scrollbar track & thumb on specified side ('right' default or 'left')
		if({ bw > 2 }, {
			local Int is sx: if({ scrollbarSide == 'left' }, { b:x }, { b:x + cw });
			ctx:fillRect(x: sx, y: b:y, w: bw, h: b:height, color: activeTheme:menuBg);
			local Int is borderX: if({ scrollbarSide == 'left' }, { sx + bw - 1 }, { sx });
			ctx:fillRect(x: borderX, y: b:y, w: 1, h: b:height, color: activeTheme:toolbarBorder);
			if({ contentH > b:height }, {
				local Int is thumbH: (b:height * b:height) / contentH;
				if({ thumbH < activeScale:px(pt: 22.0) }, { thumbH: activeScale:px(pt: 22.0); });
				if({ thumbH > b:height }, { thumbH: b:height; });
				local Int is maxScroll: contentH - b:height;
				local Int is trackRange: b:height - thumbH;
				local Int is thumbY: b:y + if({ maxScroll > 0 }, { (scrollY * trackRange) / maxScroll }, { 0 });
				ctx:fillRect(x: sx + 2, y: thumbY + 1, w: bw - 4, h: thumbH - 2, color: activeTheme:activeBg);
			});
		});
	}
}
