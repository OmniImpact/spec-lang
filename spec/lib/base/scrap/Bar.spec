#! Package base:scrap
#! Horizontal bar widget supporting top/bottom borders and left/center/right-aligned reactive text.

Class of SewNode is Bar{
	replace [String] is namespace: ['base', 'scrap'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()],
		['base', 'signal', TextEmitter],
		['base', 'signal', TextCollector],
		['base', 'sew', SewNode],
		['base', 'sew', Size],
		['base', 'sew', Rect],
		['base', 'sew', Constraints],
		['base', 'sew', Scale],
		['base', 'sew', DockSide],
		['base', 'fabric', Theme],
		['base', 'fabric', DrawContext],
		['base', 'fabric', 'svg', SvgRenderer]
	];

	Theme is theme: Theme(preset: 'light_grayscale');
	Scale is scale: Scale(factor: 1.0);
	Float is heightPt: 0.0;
	DockSide is borderSide: DockSide:BOTTOM;
	TextEmitter is leftText: TextEmitter(initial: '');
	TextEmitter is centerText: TextEmitter(initial: '');
	TextEmitter is rightText: TextEmitter(initial: '');
	Boolean is rightInteractive: false;
	String is rightIconSvg: '';
	Function is onRightClick: local Function(Int is _x, Int is _y){};
	Boolean is rightHover: false;
	Int is rightHitX: 0;
	Int is rightHitW: 0;

	replace Function is init(
		Float is heightPt: 0.0,
		DockSide is borderSide: DockSide:BOTTOM,
		TextEmitter is leftText: TextEmitter(initial: ''),
		TextEmitter is centerText: TextEmitter(initial: ''),
		TextEmitter is rightText: TextEmitter(initial: ''),
		Boolean is rightInteractive: false,
		String is rightIconSvg: '',
		Function is onRightClick: local Function(Int is _x, Int is _y){},
		Theme is theme: Theme(preset: 'light_grayscale'),
		Scale is scale: Scale(factor: 1.0)
	){
		:heightPt: heightPt;
		:borderSide: borderSide;
		:leftText: leftText;
		:centerText: centerText;
		:rightText: rightText;
		:rightInteractive: rightInteractive;
		:rightIconSvg: rightIconSvg;
		:onRightClick: onRightClick;
		:theme: theme;
		:scale: scale;
		:bindTextEmitters();
	}

	local Function is bindTextEmitters(){
		signalBag:clear();
		signalBag:track(
			slot: 'left',
			emitter: leftText,
			collector: leftText:collect(onEmit: local Function(String is _v){ invalidate(); })
		);
		signalBag:track(
			slot: 'center',
			emitter: centerText,
			collector: centerText:collect(onEmit: local Function(String is _v){ invalidate(); })
		);
		signalBag:track(
			slot: 'right',
			emitter: rightText,
			collector: rightText:collect(onEmit: local Function(String is _v){ invalidate(); })
		);
	}

	replace Function is applyTheme(Theme is theme){
		:activeTheme: theme;
		:theme: theme;
	}

	replace Function is setScale(Scale is scale){
		:scale: scale;
	}

	Function is setHeightPt(Float is heightPt){
		:heightPt: heightPt;
	}

	local Function of Int is fontPx(){
		local Int is px: scale:px(pt: theme:scaledTextPt(defaultPt: 18.0));
		return if({ px < 10 }, { 10 }, { px });
	}

	replace Function of Size is measure(Constraints is c){
		local Float is hPt: if({ heightPt > 0.0 }, { heightPt }, { theme:barHeightPt });
		local Int is h: scale:px(pt: hPt);
		desiredSize: Size(width: c:clampW(w: c:maxW), height: c:clampH(h: h));
		return desiredSize;
	}

	replace Function is paint(DrawContext is ctx){
		local Rect is b: bounds();
		if({ b:width <= 0 || b:height <= 0 }, { return; });

		ctx:fillRect(x: b:x, y: b:y, w: b:width, h: b:height, color: theme:toolbarBg);
		local Int is borderH: theme:dividerPx(scaleFactor: scale:factor);
		if({ borderH > 0 }, {
			if({ borderSide == DockSide:TOP }, {
				ctx:drawDivider(x: b:x, y: b:y, w: b:width, h: borderH, color: theme:dividerColorArgb(), thickness: borderH, style: theme:dividerStyle);
			}, {
				if({ borderSide == DockSide:BOTTOM }, {
					ctx:drawDivider(x: b:x, y: b:y + b:height - borderH, w: b:width, h: borderH, color: theme:dividerColorArgb(), thickness: borderH, style: theme:dividerStyle);
				});
			});
		});

		local Int is fpx: :fontPx();
		local Int is th: ctx:measureTextHeight(pixelHeight: fpx);
		local Int is ty: b:y + (b:height - th) / 2;
		local Int is padX: scale:px(pt: theme:paddingPt * 1.5);

		local String is lStr: leftText:current();
		if({ lStr != '' }, {
			ctx:drawText(x: b:x + padX, y: ty, text: lStr, color: theme:textPrimary, pixelHeight: fpx);
		});

		local String is cStr: centerText:current();
		if({ cStr != '' }, {
			local Int is cw: ctx:measureTextWidth(text: cStr, pixelHeight: fpx);
			ctx:drawText(x: b:x + (b:width - cw) / 2, y: ty, text: cStr, color: theme:textPrimary, pixelHeight: fpx);
		});

		local String is rStr: rightText:current();
		if({ rStr != '' }, {
			local Int is rw: ctx:measureTextWidth(text: rStr, pixelHeight: fpx);
			local Boolean is hasIcon: rightIconSvg != '';
			local Int is chevSz: if({ hasIcon }, { scale:px(pt: 11.0) }, { 0 });
			if({ hasIcon && chevSz < 9 }, { chevSz: 9; });
			local Int is chevGap: if({ hasIcon }, { scale:px(pt: 4.0) }, { 0 });
			local Int is totalRw: rw + chevGap + chevSz;
			local Int is rx: b:x + b:width - padX - totalRw;
			local Int is hitPad: scale:px(pt: 6.0);
			:rightHitX: rx - hitPad;
			:rightHitW: totalRw + hitPad * 2;
			if({ rightInteractive && rightHover }, {
				ctx:fillRect(x: rightHitX, y: b:y + 2, w: rightHitW, h: b:height - 4, color: theme:hoverBg);
			});
			ctx:drawText(x: rx, y: ty, text: rStr, color: theme:textPrimary, pixelHeight: fpx);
			if({ hasIcon }, {
				SvgRenderer:shared:draw(
					ctx: ctx,
					svgSrc: rightIconSvg,
					x: rx + rw + chevGap,
					y: b:y + (b:height - chevSz) / 2,
					widthPx: chevSz,
					heightPx: chevSz,
					tintColor: theme:textMuted,
					useTint: true
				);
			});
		}, {
			:rightHitX: 0;
			:rightHitW: 0;
		});
	}

	local Function of Boolean is inRightHit(Int is x, Int is y){
		if({ !rightInteractive || rightHitW <= 0 }, { return false; });
		local Rect is b: bounds();
		return x >= rightHitX && x < rightHitX + rightHitW && y >= b:y && y < b:y + b:height;
	}

	replace Function of Boolean is onPointerMove(Int is x, Int is y){
		local Boolean is nextHover: :inRightHit(x: x, y: y);
		if({ nextHover != rightHover }, {
			rightHover: nextHover;
			invalidate();
			return true;
		});
		return false;
	}

	replace Function is clearHover(){
		if({ rightHover }, {
			rightHover: false;
			invalidate();
		});
	}

	replace Function of Boolean is onPointerClickMod(Int is x, Int is y, Int is mods: 0){
		if({ :inRightHit(x: x, y: y) }, {
			local Function is cb: onRightClick;
			cb(x, y);
			return true;
		});
		return false;
	}

	Function is dispose(){
		signalBag:clear();
	}
}
