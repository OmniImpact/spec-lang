#! Package base:scrap
#! Bordered group frame widget with an optional header title drawn around a child [SewNode].

Class of SewNode is Frame{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'struct', Array],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext]
	];

	String is title: '';
	SewNode is child: SewNode();
	Float is padPt: -1.0;
	Boolean is fillBg: false;

	replace Function is init(String is title: '', SewNode is child: SewNode(), Float is padPt: -1.0, Boolean is fillBg: false){
		:title: title;
		:child: child;
		:padPt: padPt;
		:fillBg: fillBg;
	}

	local Function of Int is effPadPx(){
		local Float is pt: if({ padPt >= 0.0 }, { padPt }, { activeTheme:sectionPaddingPt });
		return activeScale:px(pt: pt);
	}

	local Function of Int is borderPx(){
		return activeTheme:panelBorderPx(scaleFactor: activeScale:factor);
	}

	local Function of Int is fontPx(){
		local Int is px: activeScale:px(pt: activeTheme:scaledTextPt(defaultPt: 13.0));
		return if({ px < 10 }, { 10 }, { px });
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
		local Int is padPx: :effPadPx();
		local Int is bw: :borderPx();
		local Int is insetPx: padPx + bw;
		local Int is fpx: :fontPx();
		local Int is th: if({ title != '' }, { DrawContext:measureHeight(pixelHeight: fpx) }, { 0 });
		local Int is topPad: if({ title != '' }, { th + padPx / 2 }, { insetPx });
		local Int is availW: c:maxW - insetPx * 2;
		if({ availW < 0 }, { availW: 0; });
		local Int is availH: c:maxH - topPad - insetPx;
		if({ availH < 0 }, { availH: 0; });
		local Size is cs: child:measure(c: Constraints(minW: 0, maxW: availW, minH: 0, maxH: availH));
		local Int is w: cs:width + insetPx * 2;
		if({ title != '' }, {
			local Int is minTitleW: DrawContext:measureWidth(text: title, pixelHeight: fpx) + insetPx * 3;
			if({ minTitleW > w }, { w: minTitleW; });
		});
		desiredSize: Size(
			width: c:clampW(w: w),
			height: c:clampH(h: cs:height + topPad + insetPx)
		);
		return desiredSize;
	}

	replace Function is arrange(Rect is bounds){
		layoutBounds: bounds;
		local Int is padPx: :effPadPx();
		local Int is bw: :borderPx();
		local Int is insetPx: padPx + bw;
		local Int is fpx: :fontPx();
		local Int is th: if({ title != '' }, { DrawContext:measureHeight(pixelHeight: fpx) }, { 0 });
		local Int is topPad: if({ title != '' }, { th + padPx / 2 }, { insetPx });
		local Int is cw: bounds:width - insetPx * 2;
		if({ cw < 0 }, { cw: 0; });
		local Int is ch: bounds:height - topPad - insetPx;
		if({ ch < 0 }, { ch: 0; });
		child:arrange(bounds: Rect(x: bounds:x + insetPx, y: bounds:y + topPad, width: cw, height: ch));
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });
		local Int is border: activeTheme:textAccent;
		local Int is bw: :borderPx();
		local Int is radPx: activeScale:px(pt: activeTheme:panelCornerRadiusPt);
		local Int is shBlur: activeScale:px(pt: activeTheme:panelShadowBlurPt);
		local Int is shOffX: activeScale:px(pt: activeTheme:panelShadowOffsetXPt);
		local Int is shOffY: activeScale:px(pt: activeTheme:panelShadowOffsetYPt);
		local Int is shCol: if({ shBlur > 0 || shOffX != 0 || shOffY != 0 }, { 1426063360 }, { 0 });
		local Int is inShBlur: activeScale:px(pt: activeTheme:panelInnerShadowBlurPt);
		local Int is inShOffX: activeScale:px(pt: activeTheme:panelInnerShadowOffsetXPt);
		local Int is inShOffY: activeScale:px(pt: activeTheme:panelInnerShadowOffsetYPt);
		local Int is inShCol: if({ inShBlur > 0 || inShOffX != 0 || inShOffY != 0 }, { 1426063360 }, { 0 });
		local String is pStyle: activeTheme:panelBorderStyle;
		local Int is bgCol: if({ padPt != 0.0 || fillBg }, { activeTheme:windowBg }, { 0 });
		if({ title == '' }, {
			ctx:drawStyledBox(
				x: b:x, y: b:y, w: b:width, h: b:height,
				bgColor: bgCol, borderColor: border, thickness: bw,
				radius: radPx, style: pStyle,
				shadowOffsetX: shOffX, shadowOffsetY: shOffY, shadowBlur: shBlur, shadowColor: shCol,
				innerShadowOffsetX: inShOffX, innerShadowOffsetY: inShOffY, innerShadowBlur: inShBlur, innerShadowColor: inShCol
			);
		}, {
			local Int is fpx: :fontPx();
			local Int is th: DrawContext:measureHeight(pixelHeight: fpx);
			local Int is tw: DrawContext:measureWidth(text: title, pixelHeight: fpx);
			local Int is topY: b:y + th / 2;
			local Int is boxH: b:height - (th / 2);
			if({ boxH > bw }, {
				local Int is titlePad: activeScale:px(pt: activeTheme:paddingLargePt);
				local Int is titleX: b:x + bw + radPx + titlePad;
				local Int is gapPad: activeScale:px(pt: 4.0);
				if({ pStyle == 'single' && radPx <= 0 && shBlur <= 0 && shOffX == 0 && shOffY == 0 && inShBlur <= 0 && inShOffX == 0 && inShOffY == 0 }, {
					if({ bgCol != 0 }, {
						ctx:fillRect(x: b:x + bw, y: topY + bw, w: b:width - bw * 2, h: boxH - bw * 2, color: bgCol);
					});
					local Int is leftSegW: (titleX - gapPad) - b:x;
					if({ leftSegW > 0 }, {
						ctx:fillRect(x: b:x, y: topY, w: leftSegW, h: bw, color: border);
					});
					local Int is rightStart: titleX + tw + gapPad;
					local Int is rightSegW: (b:x + b:width) - rightStart;
					if({ rightSegW > 0 }, {
						ctx:fillRect(x: rightStart, y: topY, w: rightSegW, h: bw, color: border);
					});
					ctx:fillRect(x: b:x, y: topY, w: bw, h: boxH, color: border);
					ctx:fillRect(x: b:x + b:width - bw, y: topY, w: bw, h: boxH, color: border);
					ctx:fillRect(x: b:x, y: b:y + b:height - bw, w: b:width, h: bw, color: border);
				}, {
					ctx:drawStyledBox(
						x: b:x, y: topY, w: b:width, h: boxH,
						bgColor: bgCol, borderColor: border, thickness: bw,
						radius: radPx, style: pStyle,
						shadowOffsetX: shOffX, shadowOffsetY: shOffY, shadowBlur: shBlur, shadowColor: shCol,
						innerShadowOffsetX: inShOffX, innerShadowOffsetY: inShOffY, innerShadowBlur: inShBlur, innerShadowColor: inShCol
					);
					local Int is pillH: if({ th > bw + 2 }, { th }, { bw + 2 });
					ctx:fillRect(x: titleX - gapPad, y: b:y, w: tw + gapPad * 2, h: pillH, color: activeTheme:windowBg);
				});
				ctx:drawText(x: titleX, y: b:y, text: title, color: activeTheme:textMuted, pixelHeight: fpx);
			});
		});
		local Int is clipTop: if({ title != '' }, { b:y + DrawContext:measureHeight(pixelHeight: :fontPx()) / 2 + bw }, { b:y + bw });
		local Int is clipH: (b:y + b:height - bw) - clipTop;
		local Int is clipW: b:width - bw * 2;
		if({ clipW > 0 && clipH > 0 }, {
			ctx:setClip(x: b:x + bw, y: clipTop, w: clipW, h: clipH);
			child:paint(ctx: ctx);
			ctx:clearClip();
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

	replace Function of Boolean is blocksPointerAt(Int is x, Int is y){
		if({ pointerTransparent }, { return false; });
		return :containsPoint(x: x, y: y) || child:blocksPointerAt(x: x, y: y);
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		return child:onPointerMove(x: x, y: y);
	}

	replace Function is clearHover(){
		child:clearHover();
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		return child:onPointerClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onRightClickMod(Int is x, Int is y, Int is mods: 0){
		return child:onRightClickMod(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerDrag(Int is x, Int is y, Int is mods: 0){
		return child:onPointerDrag(x: x, y: y, mods: mods);
	}

	replace Function of Boolean is onPointerUp(Int is x, Int is y){
		return child:onPointerUp(x: x, y: y);
	}

	replace Function of Boolean is onScroll(Int is deltaY){
		return child:onScroll(deltaY: deltaY);
	}

	replace Function of Boolean is onScrollX(Int is deltaX){
		return child:onScrollX(deltaX: deltaX);
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
		if({ !:containsPoint(x: x, y: y) }, { return ''; });
		local String is tip: child:tooltipAt(x: x, y: y);
		if({ tip != '' }, { return tip; });
		return tooltip;
	}
}