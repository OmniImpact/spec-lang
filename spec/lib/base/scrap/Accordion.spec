#! Package base:scrap
#! Collapsible accordion section (`SewNode`) with a clickable/focusable header and expandable body content.

Class of SewNode is Accordion{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'suit', KeyCode],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', FillStyle],
		['base', 'fabric', DrawContext],
		['base', 'fabric', 'svg', SvgRenderer]
	];

	String is title: 'Section';
	Boolean is expanded: false;
	SewNode is child: SewNode();
	Float is padPt: -1.0;
	String is collapsedIconSvg: '';
	String is expandedIconSvg: '';
	Function is onToggle: local Function(Boolean is _expanded){};

	Boolean is hovered: false;
	Boolean is focused: false;
	Rect is headerBounds: Rect();
	Rect is bodyBounds: Rect();

	replace Function is init(
		String is title: 'Section',
		Boolean is expanded: false,
		SewNode is child: SewNode(),
		Float is padPt: -1.0,
		String is collapsedIconSvg: '',
		String is expandedIconSvg: '',
		Function is onToggle: local Function(Boolean is _expanded){},
		String is tooltip: ''
	){
		:title: title;
		:expanded: expanded;
		:child: child;
		:padPt: padPt;
		:collapsedIconSvg: collapsedIconSvg;
		:expandedIconSvg: expandedIconSvg;
		:onToggle: onToggle;
		:hovered: false;
		:focused: false;
		:tooltip: tooltip;
	}

	replace Function of Boolean is canFocus(){
		return true;
	}

	replace Function of Boolean is isFocused(){
		return focused;
	}

	replace Function is setFocused(Boolean is next){
		if({ focused != next }, {
			:focused: next;
			invalidate();
		});
	}

	Function is setExpanded(Boolean is next){
		if({ expanded != next }, {
			:expanded: next;
			invalidate();
		});
	}

	local Function is toggleExpanded(){
		:expanded: !expanded;
		local Function is cb: onToggle;
		cb(expanded);
		invalidate();
	}

	replace Function of Boolean is onKey(Int is key, Int is mods){
		if({ focused && (KeyCode:isEnter(key: key) || key == KeyCode:SPACE) }, {
			:toggleExpanded();
			return true;
		});
		if({ expanded }, {
			return child:onKey(key: key, mods: mods);
		});
		return false;
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 14.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	local Function of Int is headerHeightPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 14.0) + activeTheme:paddingPt * 2.5);
		return if({ px < 22 }, { 22 }, { px });
	}

	local Function of Int is bodyPadPx(){
		local Float is pt: if({ padPt >= 0.0 }, { padPt }, { activeTheme:sectionPaddingPt });
		return activeScale:px(pt: pt);
	}

	local Function of Boolean is inHeader(Int is x, Int is y){
		return x >= headerBounds:x && x < headerBounds:x + headerBounds:width && y >= headerBounds:y && y < headerBounds:y + headerBounds:height;
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
		local Int is hh: :headerHeightPx();
		local Int is fpx: :fontPx();
		local Int is padX: activeScale:px(pt: activeTheme:paddingLargePt);
		local Int is minHeaderW: padX * 3 + DrawContext:measureWidth(text: title, pixelHeight: fpx);
		if({ !expanded }, {
			local Int is w: if({ c:maxW < 100000 }, { c:maxW }, { minHeaderW });
			if({ w < minHeaderW }, { w: minHeaderW; });
			desiredSize: Size(width: c:clampW(w: w), height: c:clampH(h: hh));
			return desiredSize;
		});
		local Int is pad: :bodyPadPx();
		local Int is availW: if({ c:maxW > pad * 2 }, { c:maxW - pad * 2 }, { 0 });
		local Int is availH: if({ c:maxH > hh + pad * 2 }, { c:maxH - hh - pad * 2 }, { 0 });
		local Size is cs: child:measure(c: Constraints(minW: 0, maxW: availW, minH: 0, maxH: availH));
		local Int is contentW: cs:width + pad * 2;
		local Int is totalW: if({ contentW > minHeaderW }, { contentW }, { minHeaderW });
		if({ c:maxW < 100000 && c:maxW > totalW }, { totalW: c:maxW; });
		local Int is totalH: hh + cs:height + pad * 2;
		desiredSize: Size(width: c:clampW(w: totalW), height: c:clampH(h: totalH));
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is hh: :headerHeightPx();
		if({ hh > bounds:height }, { hh: bounds:height; });
		:headerBounds: Rect(x: bounds:x, y: bounds:y, width: bounds:width, height: hh);
		if({ expanded && bounds:height > hh }, {
			local Int is pad: :bodyPadPx();
			:bodyBounds: Rect(x: bounds:x, y: bounds:y + hh, width: bounds:width, height: bounds:height - hh);
			local Int is cw: if({ bodyBounds:width > pad * 2 }, { bodyBounds:width - pad * 2 }, { 0 });
			local Int is ch: if({ bodyBounds:height > pad * 2 }, { bodyBounds:height - pad * 2 }, { 0 });
			child:arrange(bounds: Rect(x: bodyBounds:x + pad, y: bodyBounds:y + pad, width: cw, height: ch));
		}, {
			:bodyBounds: Rect();
		});
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is btnPx: activeTheme:buttonBorderPx(scaleFactor: activeScale:factor);
		local Int is panelPx: activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
		local Int is radPx: activeScale:px(pt: activeTheme:buttonCornerRadiusPt);

		local FillStyle is hFill: activeTheme:resolveButtonFill(enabled: true, selected: expanded, hovered: hovered, focused: focused);
		if({ expanded && bodyBounds:height > 0 }, {
			local Int is hx: headerBounds:x + panelPx;
			local Int is hy: headerBounds:y + panelPx;
			local Int is hw: if({ headerBounds:width > panelPx * 2 }, { headerBounds:width - panelPx * 2 }, { headerBounds:width });
			local Int is hh: if({ headerBounds:height > panelPx }, { headerBounds:height - panelPx }, { headerBounds:height });
			local Int is innerRad: if({ radPx > panelPx }, { radPx - panelPx }, { 0 });
			ctx:drawStyledBox(
				x: b:x, y: b:y, w: b:width, h: b:height,
				bgColor: activeTheme:panelBg, borderColor: activeTheme:panelBorderColorArgb(),
				thickness: panelPx, radius: radPx, style: activeTheme:panelBorderStyle
			);
			if({ hw > 0 && hh > 0 }, {
				ctx:setClip(x: hx, y: hy, w: hw, h: hh);
				ctx:fillRoundRectStyled(x: hx, y: hy, w: hw, h: hh + innerRad, radius: innerRad, fill: hFill);
				ctx:clearClip();
			});
			if({ btnPx > 0 && hw > 0 }, {
				ctx:drawDivider(
					x: hx, y: headerBounds:y + headerBounds:height - btnPx, w: hw, h: btnPx,
					color: activeTheme:dividerColorArgb(), thickness: btnPx, style: activeTheme:dividerStyle
				);
			});
			child:paint(ctx: ctx);
		}, {
			ctx:drawStyledBoxFill(
				x: headerBounds:x, y: headerBounds:y, w: headerBounds:width, h: headerBounds:height,
				fill: hFill, borderColor: activeTheme:buttonBorderColorArgb(),
				thickness: btnPx, radius: radPx, style: activeTheme:buttonBorderStyle
			);
		});

		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is padX: activeScale:px(pt: activeTheme:paddingLargePt);
		local Int is ty: headerBounds:y + (headerBounds:height - th) / 2;
		local String is ico: if({ expanded }, { expandedIconSvg }, { collapsedIconSvg });
		if({ ico != '' }, {
			local Int is isz: activeScale:px(pt: activeTheme:iconSizePt);
			if({ isz < 10 }, { isz: 10; });
			SvgRenderer:shared:draw(ctx: ctx, svgSrc: ico, x: headerBounds:x + padX, y: headerBounds:y + (headerBounds:height - isz) / 2, widthPx: isz, heightPx: isz, tintColor: activeTheme:textMuted, useTint: true);
			ctx:drawText(x: headerBounds:x + padX * 2 + isz, y: ty, text: title, color: activeTheme:textPrimary, pixelHeight: fpx);
		}, {
			ctx:drawText(x: headerBounds:x + padX, y: ty, text: title, color: activeTheme:textPrimary, pixelHeight: fpx);
		});
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is h: :inHeader(x: x, y: y);
		local Boolean is changed: false;
		if({ h != hovered }, {
			:hovered: h;
			invalidate();
			changed: true;
		});
		if({ expanded }, {
			if({ child:onPointerMove(x: x, y: y) }, { changed: true; });
		});
		return changed;
	}

	replace Function is clearHover(){
		if({ hovered }, {
			:hovered: false;
			invalidate();
		});
		if({ expanded }, { child:clearHover(); });
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ :inHeader(x: x, y: y) }, {
			:toggleExpanded();
			return true;
		});
		if({ expanded }, {
			return child:onPointerClickMod(x: x, y: y, mods: mods);
		});
		return false;
	}

	replace Function of String is tooltipAt(Int is x, Int is y){
		if({ expanded }, {
			local String is ct: child:tooltipAt(x: x, y: y);
			if({ ct != '' }, { return ct; });
		});
		if({ tooltip != '' && :inHeader(x: x, y: y) }, { return tooltip; });
		return '';
	}

	replace Function is collectFocusables(Array of SewNode is out){
		if({ expanded }, {
			child:collectFocusables(out: out);
		});
	}
}
